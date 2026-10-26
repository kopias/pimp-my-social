"""Exercise every Muse model once, end to end, on self-made fixtures.

    uv run scripts/smoke.py            # all checks
    uv run scripts/smoke.py text sam   # just some

Cost of a full run is a few cents: 1 image ($0.01), a handful of short text
calls, one SAM image, a 3s video, and ~4s of audio.
"""

from __future__ import annotations

import asyncio
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from muse import client as m  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "fixtures"
OUT.mkdir(exist_ok=True)
DISH = OUT / "pan.png"


def check_text() -> str:
    return m.ask("In one sentence: what does a Maillard reaction do to a steak?")


def check_image() -> str:
    m.generate_image(
        "overhead phone photo of a cast-iron skillet on a gas stove, two chicken thighs "
        "skin-side down, half browned, home kitchen, natural light",
        DISH,
    )
    return f"wrote {DISH.name} ({DISH.stat().st_size // 1024} KB)"


def check_vision() -> str:
    return m.ask(
        "You are a line cook. How done is the chicken skin, and what should the cook do "
        "in the next 60 seconds? Two sentences.",
        images=[DISH],
    )


def check_sam() -> str:
    segs = asyncio.run(m.segment("chicken thigh", DISH))
    if not segs:
        return "no matches"
    return "; ".join(f"id {s.object_id} box {s.box} area {s.area}px conf {s.confidence}"
                     for s in segs)


def check_video() -> str:
    clip = OUT / "pan.mp4"
    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-loop", "1", "-i", str(DISH), "-t", "3",
         "-vf", "scale=720:-2,zoompan=z='1+0.002*on':d=75:s=720x720", "-r", "25",
         "-pix_fmt", "yuv420p", str(clip)],
        check=True,
    )
    return m.ask_video("What is cooking in this clip, and is anything burning?", clip)


def check_asr() -> str:
    aiff, wav = OUT / "say.aiff", OUT / "say.wav"
    subprocess.run(["say", "-o", str(aiff), "Chef, flip the chicken thighs now."], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(aiff), "-ac", "1",
                    "-ar", "24000", "-c:a", "pcm_s16le", "-map_metadata", "-1", str(wav)],
                   check=True)
    return m.transcribe(wav, keywords=["chicken thighs"])["transcript"]


CHECKS = {
    "text": check_text,
    "image": check_image,
    "vision": check_vision,
    "sam": check_sam,
    "video": check_video,
    "asr": check_asr,
}
NEEDS_DISH = {"vision", "sam", "video"}


def main() -> int:
    wanted = sys.argv[1:] or list(CHECKS)
    if NEEDS_DISH & set(wanted) and "image" not in wanted and not DISH.exists():
        wanted.insert(0, "image")
    failed = 0
    for name in wanted:
        t0 = time.monotonic()
        try:
            detail = CHECKS[name]()
            print(f"PASS {name:<6} {time.monotonic() - t0:5.1f}s  {detail.strip()[:300]}")
        except Exception as e:  # report every failure, keep going
            failed += 1
            print(f"FAIL {name:<6} {time.monotonic() - t0:5.1f}s  {type(e).__name__}: {e}"[:600])
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
