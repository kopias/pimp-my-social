"""One live cook: frames in, readings and verdicts out.

The phone (or a replayed clip) posts a JPEG every few seconds. Each frame goes
through the same pipeline as the offline scripts: SAM masks for the food and the
lighting reference, Browning Index inside the masks, and, when a progress band
is crossed or enough time has passed, a Spark verdict. Spark runs in the
background so a slow verdict never holds up the next frame; the phone gets the
newest verdict with whichever frame comes back after it lands.

Time is cooking time in seconds, sent by the client: wall-clock since start for
the camera, the video position times a speed-up for a replayed clip. Readings
are indexed by whole cooking seconds, so `fps=1` everywhere downstream.

Every session is saved under out/sessions/<id>/ (frames, readings, verdicts),
which makes each real cook a calibration clip for free.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import math
import time
import uuid
from dataclasses import asdict
from pathlib import Path

import numpy as np
from PIL import Image

from . import browning as b
from . import client as m
from . import judge as j

ROOT = Path(__file__).resolve().parent.parent
SESSIONS = ROOT / "out" / "sessions"
LOST_AFTER = 2  # frames in a row with no food before Sous says so
# SAM loses recipe phrases as food darkens: on the AI onion clip "sliced onions"
# fell to 0.54 confidence at deep brown and found nothing near black, while
# "food" held at 0.91-0.93 throughout. So fall back to it, and stay there.
FALLBACK_CONCEPT = "food"
WEAK = 0.6


class Session:
    def __init__(self, spec: j.WatchSpec):
        self.id = uuid.uuid4().hex[:8]
        self.spec = spec
        self.dir = SESSIONS / self.id
        (self.dir / "frames").mkdir(parents=True, exist_ok=True)
        (self.dir / "spec.json").write_text(json.dumps(asdict(spec), indent=1))
        self.readings: list[b.Reading] = []
        self.ref_l0: float | None = None
        self.first_area: dict[str, int] = {}
        self.missed = 0
        self.concept = spec.food  # what SAM is asked for; may fall back once
        self.verdict: dict | None = None  # newest, with a "seq" the client uses to speak once
        self.seq = 0
        self.last_progress: dict[str, float] = {}
        self.last_judged = 0.0  # wall clock
        self.judging = False
        self._tasks: set[asyncio.Task] = set()

    @classmethod
    async def start(cls, step: str) -> "Session":
        return cls(await asyncio.to_thread(j.watch_spec, step))

    async def add_frame(self, jpeg: bytes, cook_s: float) -> dict:
        tick = max(0, round(cook_s))
        path = self.dir / "frames" / f"{tick:05d}.jpg"
        path.write_bytes(jpeg)
        frame = np.asarray(Image.open(io.BytesIO(jpeg)).convert("RGB"))

        t0 = time.monotonic()
        food, ref = await asyncio.gather(m.segment(self.concept, path),
                                         m.segment(self.spec.reference, path))
        if self.concept != FALLBACK_CONCEPT and _weak(food):
            fallback = await m.segment(FALLBACK_CONCEPT, path)
            if not _weak(fallback):
                print(f"[{self.id}] SAM: {self.concept!r} weak, using {FALLBACK_CONCEPT!r} from now on")
                self.concept, food = FALLBACK_CONCEPT, fallback
        sam_s = time.monotonic() - t0
        for s in food + ref:
            s.frame = tick
        if self.spec.pile:
            food = b.split_regions(food)

        if self.ref_l0 is None:
            self.ref_l0 = b.reference_lightness({tick: frame}, ref).get(tick)
        new = b.measure({tick: frame}, food, reference=ref, ref_l0=self.ref_l0,
                        first_area=self.first_area)
        self.readings += new

        self.missed = 0 if new else self.missed + 1
        if self.missed >= LOST_AFTER:
            self._publish(j.verdict(self.spec, [], path, fps=1, elapsed_min=cook_s / 60),
                          cook_s)
        elif new and not self.judging and j.should_judge(
                self.readings, self.spec, self.last_progress,
                time.monotonic() - self.last_judged):
            self.judging = True
            task = asyncio.create_task(self._judge(path, cook_s))
            self._tasks.add(task)
            task.add_done_callback(self._tasks.discard)

        return {
            "tick": tick,
            "cook_min": round(cook_s / 60, 2),
            "sam_s": round(sam_s, 2),
            "concept": self.concept,
            "found": len([s for s in food if "/" not in s.object_id]),
            "pieces": self.pieces(),
            "overlay": overlay_png([s for s in food if "/" not in s.object_id], frame,
                                   self.spec.target_bi),
            "verdict": self.verdict,
            "judging": self.judging,
        }

    async def _judge(self, path: Path, cook_s: float) -> None:
        try:
            t0 = time.monotonic()
            v = await asyncio.to_thread(j.verdict, self.spec, list(self.readings), path,
                                        fps=1, elapsed_min=cook_s / 60)
            self.last_progress = v.progress
            self._publish(v, cook_s, latency=time.monotonic() - t0)
        except Exception as e:  # a failed call must not kill the session
            print(f"[{self.id}] judge failed: {e!r}")
        finally:
            self.last_judged = time.monotonic()
            self.judging = False

    def _publish(self, v: j.Verdict, cook_s: float, latency: float | None = None) -> None:
        self.seq += 1
        self.verdict = {"seq": self.seq, "cook_min": round(cook_s / 60, 2),
                        "latency_s": None if latency is None else round(latency, 1),
                        **v.as_dict()}
        with open(self.dir / "verdicts.jsonl", "a") as f:
            f.write(json.dumps(self.verdict) + "\n")
        b.save_readings(self.readings, self.dir / "readings.json")

    def pieces(self) -> list[dict]:
        """Latest progress per piece or region, for the bars on the phone."""
        if not self.readings:
            return []
        _, progress, _ = j.progress_table(self.readings, self.spec, fps=1)
        where = b.positions(self.readings)
        latest = {oid: rows[-1] for oid, rows in b.by_object(self.readings).items()}
        out = []
        for oid, p in progress.items():
            r = latest[oid]
            out.append({"id": oid, "position": where.get(oid, oid),
                        "progress": None if math.isnan(p) else p,
                        "bi": None if math.isnan(r.bi) else round(r.bi),
                        "lightness": round(r.lightness), "browned": round(r.browned, 2),
                        "stale": r.frame != max(x.frame for x in latest.values())})
        out.sort(key=lambda x: (x["position"] != "whole pan", x["position"]))
        return out


def _weak(segs: list[m.Segment]) -> bool:
    return not segs or max(s.confidence or 0 for s in segs) < WEAK


def overlay_png(segs: list[m.Segment], frame: np.ndarray, target_bi: float) -> str | None:
    """A transparent PNG the size of the frame: each mask's outline, plus a light
    tint by progress toward the target (blue raw, green at target, red over).
    Light enough that the food's own colour still shows. A data URL for an <img>
    laid over the video."""
    if not segs:
        return None
    h, w = frame.shape[:2]
    rgba = np.zeros((h, w, 4), np.uint8)
    over = 1 + j.OVERDONE_MARGIN / target_bi
    stops = np.array([[90, 140, 230], [120, 200, 140], [230, 90, 70]], float)  # 0, 1, over
    for seg in segs:
        left, top, right, bottom = seg.box
        crop = frame[top:bottom, left:right]
        mask = b.mask_array(seg)[: crop.shape[0], : crop.shape[1]]
        p = np.nan_to_num(b.browning_index(b.srgb_to_lab(crop)), nan=0) / target_bi
        lo = np.clip(p, 0, 1)[..., None]
        hi = np.clip((p - 1) / (over - 1), 0, 1)[..., None]
        rgb = np.where(p[..., None] <= 1, stops[0] + lo * (stops[1] - stops[0]),
                       stops[1] + hi * (stops[2] - stops[1]))
        edge = mask & ~b.erode(mask, max(2, min(mask.shape) // 150))
        alpha = np.where(edge, 230, 70)
        tint = np.concatenate([rgb, alpha[..., None]], axis=-1).astype(np.uint8)
        region = rgba[top:top + mask.shape[0], left:left + mask.shape[1]]
        region[mask] = tint[mask]
    buf = io.BytesIO()
    Image.fromarray(rgba, "RGBA").save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
