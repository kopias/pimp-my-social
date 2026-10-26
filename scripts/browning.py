"""Browning curves for a pan clip (or one photo), measured inside SAM masks.

    uv run scripts/browning.py fixtures/thighs.mov --food "chicken thigh"
    uv run scripts/browning.py fixtures/onions.mov --food "sliced onions" --ref "gas stove" --regions
    uv run scripts/browning.py fixtures/pan.png --food "chicken thigh"

Writes to out/<clip name>/:
    readings.json   one row per object per frame
    curves.png      BI and browned-share over time, one line per piece
    overlay.png     the last frame with each mask tinted by its browning

--regions splits each mask into a 3x3 grid of pan regions ("back left", ...),
for food SAM sees as one pile, like onions.

The clip is first downsampled (default 4 fps, 960 px) because SAM bills per
frame; the frame indices SAM returns refer to that prepared clip.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from muse import browning as b  # noqa: E402
from muse import client as m  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
VIDEO_SUFFIXES = {".mp4", ".mov", ".m4v", ".webm", ".avi"}


def plot_curves(readings: list[b.Reading], fps: float, out: Path, title: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9, 6), sharex=True)
    for oid, rows in sorted(b.by_object(readings).items()):
        t = [r.frame / fps for r in rows]
        label = rows[-1].region or f"piece {oid}"
        style = {"lw": 2.5, "color": "k"} if label == "whole pan" else {"lw": 1}
        ax1.plot(t, [r.bi for r in rows], label=label, **style)
        ax2.plot(t, [100 * r.browned for r in rows], label=label, **style)
    ax1.axhline(b.BROWNED_BI, color="0.6", ls="--", lw=1)
    ax1.set_ylabel("Browning Index")
    ax2.set_ylabel(f"% surface past BI {b.BROWNED_BI:.0f}")
    ax2.set_xlabel("seconds")
    ax2.set_ylim(0, 100)
    ax1.legend(loc="upper left", fontsize=8)
    ax1.set_title(title)
    fig.tight_layout()
    fig.savefig(out, dpi=120)
    plt.close(fig)


def overlay(frame: np.ndarray, segs: list[m.Segment], out: Path) -> None:
    """Tint each pixel inside a mask from blue (raw) through red (browned)."""
    img = frame.astype(np.float64).copy()
    for seg in segs:
        left, top, right, bottom = seg.box
        crop = img[top:bottom, left:right]
        mask = b.mask_array(seg)[: crop.shape[0], : crop.shape[1]]
        bi = b.browning_index(b.srgb_to_lab(frame[top:bottom, left:right]))
        t = np.clip(np.nan_to_num(bi, nan=0) / (2 * b.BROWNED_BI), 0, 1)
        tint = np.stack([255 * t, 60 * np.ones_like(t), 255 * (1 - t)], axis=-1)
        crop[mask] = 0.45 * crop[mask] + 0.55 * tint[mask]
    Image.fromarray(img.astype(np.uint8)).save(out)


async def run(src: Path, food: str, ref: str | None, fps: float, out_dir: Path,
              regions: bool = False) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    video = src.suffix.lower() in VIDEO_SUFFIXES
    t0 = time.monotonic()
    if video:
        media = b.prepare_clip(src, out_dir / "prepared.mp4", fps=fps)
        frames = b.decode_frames(media)
    else:
        media = src
        frames = {0: np.asarray(Image.open(src).convert("RGB"))}
    print(f"{len(frames)} frame(s) to SAM")

    jobs = [m.segment(food, media, video=video)]
    if ref:
        jobs.append(m.segment(ref, media, video=video))
    results = await asyncio.gather(*jobs)
    food_segs, ref_segs = results[0], (results[1] if ref else None)
    print(f"SAM: {len(food_segs)} food masks"
          + (f", {len(ref_segs)} reference masks" if ref_segs is not None else "")
          + f" in {time.monotonic() - t0:.1f}s")
    if not food_segs:
        raise SystemExit(f'SAM found no "{food}" in {src.name}')

    readings = b.measure(frames, b.split_regions(food_segs) if regions else food_segs,
                         reference=ref_segs)
    b.save_readings(readings, out_dir / "readings.json")

    last = max(r.frame for r in readings)
    overlay(frames[last], [s for s in food_segs if (s.frame or 0) == last], out_dir / "overlay.png")
    if video:
        plot_curves(readings, fps, out_dir / "curves.png", f"{src.name}: {food}")

    print(f"{'piece':<16}{'BI start':>9}{'BI end':>8}{'browned':>9}{'area':>7}")
    for oid, rows in sorted(b.by_object(readings).items()):
        a, z = rows[0], rows[-1]
        print(f"{z.region or oid:<16}{a.bi:9.1f}{z.bi:8.1f}{100 * z.browned:8.0f}%{z.area_ratio:7.2f}")
    print(f"wrote {out_dir.relative_to(ROOT)}/")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("media", type=Path)
    p.add_argument("--food", required=True, help='one SAM noun phrase, e.g. "chicken thigh"')
    p.add_argument("--ref", help='a region that should not change, e.g. "frying pan"')
    p.add_argument("--fps", type=float, default=4)
    p.add_argument("--regions", action="store_true", help="also measure a 3x3 grid of pan regions")
    args = p.parse_args()
    asyncio.run(run(args.media, args.food, args.ref, args.fps, ROOT / "out" / args.media.stem,
                    regions=args.regions))


if __name__ == "__main__":
    main()
