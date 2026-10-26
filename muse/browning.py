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


def measure(frames: dict[int, np.ndarray], food: list[Segment],
            reference: list[Segment] | None = None,
            browned_bi: float = BROWNED_BI) -> list[Reading]:
    """Readings for every food segment, frame by frame, oldest first.

    `frames` maps frame index -> HxWx3 uint8 RGB. Image results (frame None)
    are treated as frame 0.
    """
    ref_l: dict[int, float] = {}
    for seg in reference or []:
        f = seg.frame or 0
        if f in frames:
            px = masked_pixels(frames[f], seg)
            if len(px):
                ref_l.setdefault(f, float(np.median(srgb_to_lab(px)[:, 0])))
    ref0 = ref_l[min(ref_l)] if ref_l else None

    first_area: dict[str, int] = {}
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
        ))
    return out


def by_object(readings: list[Reading]) -> dict[str, list[Reading]]:
    out: dict[str, list[Reading]] = defaultdict(list)
    for r in readings:
        out[r.object_id].append(r)
    return dict(out)


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
