"""An AI-made cook-through clip for testing the browning pipeline without a stove.

    uv run scripts/make_test_clip.py          # -> fixtures/synthetic_sear.mp4
    uv run scripts/make_test_clip.py onions   # -> fixtures/synthetic_onions.mp4

Muse Image edits a starting photo through raw -> deep brown, each step from the
previous one so the framing holds, then ffmpeg crossfades the stills. The sear
starts from fixtures/pan.png (made by smoke.py); the onions start from a
top-down photo generated here. Fake pixels: good for checking the curves rise,
not for calibrating thresholds. ~$0.05-0.10.
"""

from __future__ import annotations

import argparse
import base64
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from muse import client as m  # noqa: E402

FIX = Path(__file__).resolve().parent.parent / "fixtures"
SEAR_KEEP = ("Keep the exact same photo: same camera angle, framing, pan, stove, lighting, "
             "and the same two chicken thighs in the same positions and shapes. Change only "
             "the colour of the chicken skin: ")
ONION_KEEP = ("Keep the exact same photo: same top-down camera, framing, pan, stove and "
              "lighting, the same amount of sliced onion in the same pan. Change only the "
              "onions: ")

# name -> (base image prompt or None for fixtures/pan.png, keep clause, stages)
CLIPS = {
    "sear": (None, SEAR_KEEP, [
        "raw and uncooked, pale pinkish-white, no browning at all.",
        "just starting to cook, pale cream with faint golden edges.",
        "light golden brown over about half of the skin.",
        "evenly golden brown and crisp-looking all over.",
        "deep mahogany brown, very dark at the edges, nearly overcooked.",
    ]),
    # Caramelising onions, with one uneven stage (the back of the pan catching)
    # that a stir evens out, then pushed on to burnt.
    "onions": (
        "Photo taken from directly above a home gas stove: a 28 cm stainless steel frying "
        "pan filled with a loose layer of thinly sliced raw white onions, glistening with a "
        "little oil. The whole pan is in frame with a strip of black stovetop around it. "
        "Ordinary warm kitchen light, phone photo, sharp, no hands, no utensils.",
        ONION_KEEP, [
            "softened and translucent, pale ivory, still no colour.",
            "light golden, evenly coloured across the pan.",
            "golden in the front half of the pan, but the onions at the back of the pan "
            "(top of the photo) have caught and are clearly darker brown than the rest.",
            "just stirred: evenly medium amber brown all across the pan, slices moved around.",
            "deep brown and jammy, fully caramelised, evenly coloured.",
            # "burnt" trips the content filter; describe the colour instead.
            "cooked too long: very dark brown, almost black at the tips, darkest at the back.",
        ]),
}
HOLD, FADE = 2.0, 0.6


def edit(src: Path, prompt: str, out: Path) -> Path:
    with open(src, "rb") as f:
        r = m.client().images.edit(
            model=m.IMAGE_MODEL, image=f, prompt=prompt, n=1,
            extra_body={"output_format": "png", "reasoning_strength": "low",
                        "tool_enablement": {"enable_web_search": False, "enable_shell": False,
                                            "enable_image_search": False}},
        )
    out.write_bytes(base64.b64decode(r.data[0].b64_json))
    return out


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("clip", nargs="?", default="sear", choices=list(CLIPS))
    p.add_argument("--reuse", action="store_true", help="keep stills already in fixtures/")
    args = p.parse_args()
    name = args.clip
    base, keep, stages = CLIPS[name]
    if base is None:
        src = FIX / "pan.png"
        if not src.exists():
            raise SystemExit("run `uv run scripts/smoke.py image` first")
    elif args.reuse and (FIX / f"{name}_base.png").exists():
        src = FIX / f"{name}_base.png"
    else:
        src = m.generate_image(base, FIX / f"{name}_base.png")
        print(f"base: {src.name}")
    stills, prev = [src] if base else [], src
    for i, stage in enumerate(stages):
        out = FIX / f"{name}_{i}.png"
        prev = out if args.reuse and out.exists() else edit(prev, keep + stage, out)
        stills.append(prev)
        print(f"stage {i}: {stage}")

    inputs, chain, offset = [], [], 0.0
    for p in stills:
        inputs += ["-loop", "1", "-t", str(HOLD + FADE), "-i", str(p)]
    norm = [f"[{i}]scale=1440:960:force_original_aspect_ratio=decrease,pad=1440:960:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=25,format=yuv420p[v{i}]" for i in range(len(stills))]
    last = "v0"
    for i in range(1, len(stills)):
        offset += HOLD
        chain.append(f"[{last}][v{i}]xfade=transition=fade:duration={FADE}:offset={offset:.2f}[x{i}]")
        last = f"x{i}"
    out = FIX / f"synthetic_{name}.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex",
                    ";".join(norm + chain), "-map", f"[{last}]", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", str(out)], check=True)
    print(f"wrote {out.relative_to(FIX.parent)}")


if __name__ == "__main__":
    main()
