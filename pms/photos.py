"""The photo studio: reshoot each product as a professional photograph.

1. SAM 3.1 finds the product in the owner's photo. We cut it out onto a plain
   neutral ground, so the counter clutter, the bad light and the stray mug don't
   ride along into the reshoot.
2. Muse Image reshoots that cutout in the chosen direction: set, light, lens,
   depth of field. Landscape for the website, portrait for social.
3. SAM finds the product again in the new shot, and we compare it with the
   original (shape and colour inside the masks). That fidelity score is how we
   catch a reshoot that quietly changed the product, which would be false
   advertising on a real store.
"""

from __future__ import annotations

import asyncio
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from muse import client as m

from .directions import RESHOOT

MIN_FIDELITY = 0.6
SIZES = {"landscape": "1536x1024", "portrait": "1024x1536"}


@dataclass
class Shot:
    product: str
    source: str  # owner's original
    cutout: str | None  # SAM isolation, what Muse Image was given
    landscape: str | None
    portrait: str | None
    fidelity: float | None  # 0-1, shape + colour agreement with the original
    sam_confidence: float | None
    note: str = ""


def _mask_image(seg: m.Segment, size: tuple[int, int]) -> np.ndarray:
    full = np.zeros((size[1], size[0]), bool)
    left, top, _, _ = seg.box
    mask = np.frombuffer(seg.mask or b"", np.uint8).reshape(seg.height, seg.width).astype(bool)
    h, w = min(mask.shape[0], size[1] - top), min(mask.shape[1], size[0] - left)
    full[top:top + h, left:left + w] = mask[:h, :w]
    return full


async def find(subject: str, photo: Path) -> tuple[m.Segment | None, np.ndarray | None]:
    """The most confident, then largest, mask of `subject`."""
    segs = await m.segment(subject, photo)
    if not segs:
        return None, None
    best = max(segs, key=lambda s: ((s.confidence or 0) > 0.5, s.area))
    with Image.open(photo) as im:
        return best, _mask_image(best, im.size)


def cutout(photo: Path, mask: np.ndarray, out: Path) -> Path:
    """The product on a soft neutral grey, cropped with breathing room."""
    im = Image.open(photo).convert("RGB")
    ys, xs = np.nonzero(mask)
    pad = int(0.12 * max(np.ptp(xs), np.ptp(ys)))
    box = (max(0, xs.min() - pad), max(0, ys.min() - pad),
           min(im.width, xs.max() + pad), min(im.height, ys.max() + pad))
    alpha = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.5))
    ground = Image.new("RGB", im.size, (226, 224, 220))
    Image.composite(im, ground, alpha).crop(box).save(out, "JPEG", quality=92)
    return out


def _lab_mean(rgb: np.ndarray) -> np.ndarray:
    c = rgb.astype(float) / 255
    c = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    xyz = c @ np.array([[0.4124, 0.3576, 0.1805], [0.2126, 0.7152, 0.0722],
                        [0.0193, 0.1192, 0.9505]]).T / np.array([0.9505, 1.0, 1.089])
    f = np.where(xyz > 0.008856, np.cbrt(xyz), 7.787 * xyz + 16 / 116)
    lab = np.stack([116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])], 1)
    return lab.mean(0)


def fidelity(orig: Path, orig_mask: np.ndarray, new: Path, new_mask: np.ndarray) -> float:
    """1.0 = same shape and colour. Shape: aspect ratio of the mask's box.
    Colour: mean CIELAB distance inside the masks (a delta-E of 30 scores 0)."""
    def aspect(mask: np.ndarray) -> float:
        ys, xs = np.nonzero(mask)
        return (np.ptp(xs) + 1) / (np.ptp(ys) + 1)
    a, b = aspect(orig_mask), aspect(new_mask)
    shape = min(a, b) / max(a, b)
    ca = _lab_mean(np.asarray(Image.open(orig).convert("RGB"))[orig_mask])
    cb = _lab_mean(np.asarray(Image.open(new).convert("RGB"))[new_mask])
    colour = max(0.0, 1 - float(np.linalg.norm(ca - cb)) / 30)
    return round(0.5 * shape + 0.5 * colour, 2)


async def reshoot(product: dict, photo: Path, direction: dict, out: Path) -> Shot:
    out.mkdir(parents=True, exist_ok=True)
    name, subject = product["name"], product["subject"] or "product"
    stem = "".join(ch if ch.isalnum() else "_" for ch in name.lower())[:40]
    seg, mask = await find(subject, photo)
    if seg is None or (seg.confidence or 0) < 0.4 or mask.sum() < 0.01 * mask.size:
        # Nothing to isolate (an illustration, a screenshot): restyle the whole photo.
        src, cut, conf, note = photo, None, seg.confidence if seg else None, \
            f"SAM couldn't isolate a {subject}; restyled the whole photo."
    else:
        cut = cutout(photo, mask, out / f"{stem}_cutout.jpg")
        src, conf, note = cut, seg.confidence, ""

    prompt = RESHOOT.format(subject=subject, photo=direction["photo"])
    land, port = await asyncio.gather(
        asyncio.to_thread(m.edit_image, src, prompt, out / f"{stem}_landscape.png", size=SIZES["landscape"]),
        asyncio.to_thread(m.edit_image, src, prompt, out / f"{stem}_portrait.png", size=SIZES["portrait"]),
    )
    score = None
    if mask is not None and cut is not None:
        _, new_mask = await find(subject, land)
        if new_mask is not None and new_mask.any():
            score = fidelity(photo, mask, land, new_mask)
            if score < MIN_FIDELITY:
                note = f"Fidelity {score:.2f}: check this one before publishing."
        else:
            note = f"SAM couldn't find the {subject} in the reshoot: check it before publishing."
    return Shot(name, str(photo), str(cut) if cut else None, str(land), str(port), score, conf, note)


async def studio(products: list[dict], photos: dict[int, Path], direction: dict, out: Path,
                 limit: int = 4) -> list[Shot]:
    """Reshoot up to `limit` products that have a photo, one photo used once."""
    used, jobs = set(), []
    for prod in products:
        idx = prod["photo"]
        if idx < 0 or idx in used or idx not in photos:
            continue
        used.add(idx)
        jobs.append(reshoot(prod, photos[idx], direction, out))
        if len(jobs) == limit:
            break
    shots = []
    for r in await asyncio.gather(*jobs, return_exceptions=True):
        if isinstance(r, Exception):
            print(f"reshoot failed: {r!r}"[:300])
        else:
            shots.append(r)
    return shots


def shots_json(shots: list[Shot]) -> list[dict]:
    return [asdict(s) for s in shots]
