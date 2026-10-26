"""Measure how browned each piece of food is, inside its SAM mask.

The signal is the Browning Index from food science (Buera et al.; Maskan 2001),
computed per pixel in CIELAB:

    x  = (a* + 1.75 L*) / (5.645 L* + a* - 3.012 b*)
    BI = 100 (x - 0.31) / 0.17

On reference skin swatches (tests/test_browning.py): raw ~20, pale gold ~70,
golden ~135, deep brown ~195. Those are starting points, not truth;
`scripts/browning.py` plots the curves so the bands can be calibrated against
real footage.

Per object per frame we report the mean BI, mean lightness, the fraction of the
surface past a "browned" threshold, and area relative to the first frame (food
shrinks as it cooks). Edges are eroded off each mask first so pan, oil and
shadow at the boundary don't leak in.

Lighting: colour drifts as light changes, so an optional reference region (a
second SAM concept that shouldn't change, such as the pan rim or the stovetop)
is measured too, and its lightness drift is subtracted from L* before BI is
computed.
"""

from __future__ import annotations

import json
import subprocess
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

from .client import Segment

BROWNED_BI = 80.0  # a pixel past this counts as browned; calibrate on real clips
ERODE_FRACTION = 0.04  # erode this share of the mask's shorter side off its edge


# --- colour ------------------------------------------------------------------


def srgb_to_lab(rgb: np.ndarray) -> np.ndarray:
    """(..., 3) uint8 sRGB -> (..., 3) float CIELAB, D65."""
    c = rgb.astype(np.float64) / 255.0
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([[0.4124564, 0.3575761, 0.1804375],
                  [0.2126729, 0.7151522, 0.0721750],
                  [0.0193339, 0.1191920, 0.9503041]])
    xyz = c @ m.T / np.array([0.95047, 1.0, 1.08883])
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    L = 116 * f[..., 1] - 16
    a = 500 * (f[..., 0] - f[..., 1])
    b = 200 * (f[..., 1] - f[..., 2])
    return np.stack([L, a, b], axis=-1)


def browning_index(lab: np.ndarray) -> np.ndarray:
    L, a, b = lab[..., 0], lab[..., 1], lab[..., 2]
    denom = 5.645 * L + a - 3.012 * b
    x = np.divide(a + 1.75 * L, denom, out=np.full_like(L, np.nan), where=np.abs(denom) > 1e-6)
    bi = 100 * (x - 0.31) / 0.17
    # Near-black or blown-out pixels make the ratio meaningless; drop them.
    return np.where((L > 5) & (L < 98), bi, np.nan)


# --- masks -------------------------------------------------------------------


def mask_array(seg: Segment) -> np.ndarray:
    return np.frombuffer(seg.mask or b"", dtype=np.uint8).reshape(seg.height, seg.width).astype(bool)


def erode(mask: np.ndarray, radius: int) -> np.ndarray:
    """Binary erosion by a (2r+1) square, with numpy only."""
    if radius <= 0:
        return mask
    padded = np.pad(mask, radius, constant_values=False)
    out = np.ones_like(mask)
    h, w = mask.shape
    for dy in range(2 * radius + 1):
        for dx in range(2 * radius + 1):
            out &= padded[dy:dy + h, dx:dx + w]
    return out


def masked_pixels(frame: np.ndarray, seg: Segment, erode_fraction: float = ERODE_FRACTION):
    """RGB pixels of `frame` inside the (eroded) mask of `seg`, as (N, 3)."""
    left, top, right, bottom = seg.box
    crop = frame[top:bottom, left:right]
    mask = mask_array(seg)[: crop.shape[0], : crop.shape[1]]
    radius = int(min(mask.shape) * erode_fraction)
    inner = erode(mask, radius)
    if inner.sum() < 50:  # tiny piece: erosion ate it, fall back to the raw mask
        inner = mask
    return crop[inner]


# --- measurement -------------------------------------------------------------


@dataclass
class Reading:
    object_id: str
    frame: int
    bi: float  # mean Browning Index over the surface
    lightness: float  # mean L*, after lighting correction
    browned: float  # share of surface pixels past BROWNED_BI, 0-1
    area: int  # mask pixels
    area_ratio: float  # area / area in this object's first frame
    confidence: float | None
    # Mask centre as a share of frame width / height (0 = left / back).
    cx: float | None = None
    cy: float | None = None
    # Set when this reading is one cell of a pile split by `split_regions`:
    # "back left", "middle", ... ; "whole pan" for the pile itself.
    region: str | None = None


ROWS = ("back", "", "front")  # top of the photo is the back of the pan
COLS = ("left", "", "right")
MIN_CELL_SHARE = 0.04  # drop grid cells holding less than this share of the pile


def region_name(row: int, col: int) -> str:
    return " ".join(w for w in (ROWS[row], COLS[col]) if w) or "middle"


def split_regions(segs: list[Segment], n: int = 3) -> list[Segment]:
    """Cut each pile mask into an n x n grid over its own box, one Segment per cell.

    For food that SAM sees as one mass (a pan of onions), so the judge can tell
    "the back is catching" from "it's all catching". Cell ids are
    "<object>/<region>", e.g. "0/back left". Cells with little of the pile in
    them (the corners of a round pan) are dropped. The original pile segments
    are returned too, with region "whole pan".
    """
    out: list[Segment] = []
    for seg in segs:
        out.append(seg)
        mask = mask_array(seg)
        total = mask.sum()
        if not total:
            continue
        left, top, _, _ = seg.box
        ys = np.linspace(0, seg.height, n + 1).astype(int)
        xs = np.linspace(0, seg.width, n + 1).astype(int)
        for r in range(n):
            for c in range(n):
                cell = mask[ys[r]:ys[r + 1], xs[c]:xs[c + 1]]
                if cell.sum() < MIN_CELL_SHARE * total:
                    continue
                h, w = cell.shape
                out.append(Segment(
                    object_id=f"{seg.object_id}/{region_name(r, c) if n == 3 else f'{r},{c}'}",
                    box=(left + xs[c], top + ys[r], left + xs[c] + w, top + ys[r] + h),
                    mask=cell.astype(np.uint8).tobytes(),
                    width=w, height=h, confidence=seg.confidence, frame=seg.frame,
                ))
    return out


def reference_lightness(frames: dict[int, np.ndarray],
                        reference: list[Segment] | None) -> dict[int, float]:
    """Median L* of the reference region, per frame."""
    ref_l: dict[int, float] = {}
    for seg in reference or []:
        f = seg.frame or 0
        if f in frames:
            px = masked_pixels(frames[f], seg)
            if len(px):
                ref_l.setdefault(f, float(np.median(srgb_to_lab(px)[:, 0])))
    return ref_l


def measure(frames: dict[int, np.ndarray], food: list[Segment],
            reference: list[Segment] | None = None,
            browned_bi: float = BROWNED_BI, *, ref_l0: float | None = None,
            first_area: dict[str, int] | None = None) -> list[Reading]:
    """Readings for every food segment, frame by frame, oldest first.

    `frames` maps frame index -> HxWx3 uint8 RGB. Image results (frame None)
    are treated as frame 0.

    A live session measures one frame per call, so it passes the state that
    spans calls: `ref_l0`, the reference lightness at the start of the cook,
    and `first_area`, each object's area in its first frame (updated in place).
    """
    ref_l = reference_lightness(frames, reference)
    ref0 = ref_l0 if ref_l0 is not None else (ref_l[min(ref_l)] if ref_l else None)

    first_area = {} if first_area is None else first_area
    out: list[Reading] = []
    for seg in sorted(food, key=lambda s: (s.frame or 0, s.object_id)):
        f = seg.frame or 0
        if f not in frames:
            continue
        px = masked_pixels(frames[f], seg)
        if not len(px):
            continue
        lab = srgb_to_lab(px)
        if ref0 is not None and f in ref_l:
            lab[:, 0] -= ref_l[f] - ref0  # undo the scene-wide lightness drift
        bi = browning_index(lab)
        valid = bi[~np.isnan(bi)]
        area = seg.area
        first_area.setdefault(seg.object_id, area)
        out.append(Reading(
            object_id=seg.object_id,
            frame=f,
            bi=float(np.mean(valid)) if len(valid) else float("nan"),
            lightness=float(np.mean(lab[:, 0])),
            browned=float(np.mean(valid > browned_bi)) if len(valid) else 0.0,
            area=area,
            area_ratio=area / first_area[seg.object_id] if first_area[seg.object_id] else 1.0,
            confidence=seg.confidence,
            cx=(seg.box[0] + seg.box[2]) / 2 / frames[f].shape[1],
            cy=(seg.box[1] + seg.box[3]) / 2 / frames[f].shape[0],
            region=(seg.object_id.split("/", 1)[1] if "/" in seg.object_id
                    else "whole pan" if _has_cells(food, seg.object_id) else None),
        ))
    return out


def _has_cells(segs: list[Segment], oid: str) -> bool:
    return any(s.object_id.startswith(oid + "/") for s in segs)


def by_object(readings: list[Reading]) -> dict[str, list[Reading]]:
    out: dict[str, list[Reading]] = defaultdict(list)
    for r in readings:
        out[r.object_id].append(r)
    return dict(out)


def positions(readings: list[Reading]) -> dict[str, str]:
    """Name each piece the way a cook would: "left", "right", "back", "front left".

    From each piece's latest mask centre. Pieces are ranked along whichever axis
    separates them more, so two thighs side by side are "left" and "right" even
    if both sit left of centre.
    """
    latest = {oid: rows[-1] for oid, rows in by_object(readings).items()}
    if any(r.region for r in latest.values()):
        return {oid: r.region or oid for oid, r in latest.items()}
    pts = {oid: (r.cx, r.cy) for oid, r in latest.items() if r.cx is not None}
    if len(pts) <= 1:
        return {oid: "the piece" for oid in latest}
    xs = [x for x, _ in pts.values()]
    ys = [y for _, y in pts.values()]
    horizontal = (max(xs) - min(xs)) >= (max(ys) - min(ys))
    order = sorted(pts, key=lambda o: pts[o][0] if horizontal else pts[o][1])
    names = (["left", "right"], ["left", "middle", "right"]) if horizontal else \
            (["back", "front"], ["back", "middle", "front"])
    if len(order) <= 3:
        return dict(zip(order, names[len(order) - 2]))
    # Many pieces: a coarse 3x3 grid, numbered when two share a cell.
    out: dict[str, str] = {}
    seen: dict[str, int] = {}
    for oid in order:
        x, y = pts[oid]
        col = "left" if x < 0.4 else "right" if x > 0.6 else ""
        row = "back" if y < 0.4 else "front" if y > 0.6 else ""
        cell = " ".join(w for w in (row, col) if w) or "middle"
        seen[cell] = seen.get(cell, 0) + 1
        out[oid] = cell if seen[cell] == 1 else f"{cell} {seen[cell]}"
    return out


def save_readings(readings: list[Reading], path: str | Path) -> None:
    Path(path).write_text(json.dumps([asdict(r) for r in readings], indent=1))


# --- video frames ------------------------------------------------------------


def probe_size(video: str | Path) -> tuple[int, int]:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height", "-of", "csv=p=0", str(video)],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    w, h = out.split(",")[:2]
    return int(w), int(h)


def decode_frames(video: str | Path) -> dict[int, np.ndarray]:
    """Every frame of `video` as RGB, indexed the way SAM counts them (from 0).

    Fine for the short, downsampled clips we send to SAM; not for long video.
    """
    w, h = probe_size(video)
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(video), "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        check=True, capture_output=True,
    ).stdout
    n = len(raw) // (w * h * 3)
    arr = np.frombuffer(raw[: n * w * h * 3], dtype=np.uint8).reshape(n, h, w, 3)
    return {i: arr[i] for i in range(n)}


def prepare_clip(src: str | Path, out: str | Path, *, fps: float = 4, max_side: int = 960) -> Path:
    """Downsample a phone clip before SAM: fewer frames is cheaper and faster.

    SAM bills per frame ($0.20 / 1,000), so 4 fps on a 2-minute clip is 480
    frames, about $0.10, against $0.72 at 30 fps.
    """
    scale = f"scale='if(gt(iw,ih),min({max_side},iw),-2)':'if(gt(iw,ih),-2,min({max_side},ih))'"
    subprocess.run(
        ["ffmpeg", "-y", "-v", "error", "-i", str(src), "-vf", f"fps={fps},{scale}",
         "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(out)],
        check=True,
    )
    return Path(out)
