"""An AI-made cook-through clip for testing the browning pipeline without a stove.

    uv run scripts/make_test_clip.py        # -> fixtures/synthetic_sear.mp4

Muse Image edits fixtures/pan.png (made by smoke.py) through raw -> deep brown,
each step from the previous one so the framing holds, then ffmpeg crossfades the
stills. Fake pixels: good for checking the curves rise, not for calibrating
thresholds. ~$0.05.
"""

from __future__ import annotations

import base64
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from muse import client as m  # noqa: E402

FIX = Path(__file__).resolve().parent.parent / "fixtures"
KEEP = ("Keep the exact same photo: same camera angle, framing, pan, stove, lighting, and "
        "the same two chicken thighs in the same positions and shapes. Change only the "
        "colour of the chicken skin: ")
STAGES = [
    "raw and uncooked, pale pinkish-white, no browning at all.",
    "just starting to cook, pale cream with faint golden edges.",
    "light golden brown over about half of the skin.",
    "evenly golden brown and crisp-looking all over.",
    "deep mahogany brown, very dark at the edges, nearly overcooked.",
]
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
    src = FIX / "pan.png"
    if not src.exists():
        raise SystemExit("run `uv run scripts/smoke.py image` first")
    stills, prev = [], src
    for i, stage in enumerate(STAGES):
        prev = edit(prev, KEEP + stage, FIX / f"sear_{i}.png")
        stills.append(prev)
        print(f"stage {i}: {stage}")

    inputs, chain, offset = [], [], 0.0
    for p in stills:
        inputs += ["-loop", "1", "-t", str(HOLD + FADE), "-i", str(p)]
    norm = [f"[{i}]scale=1440:960,setsar=1,fps=25,format=yuv420p[v{i}]" for i in range(len(stills))]
    last = "v0"
    for i in range(1, len(stills)):
        offset += HOLD
        chain.append(f"[{last}][v{i}]xfade=transition=fade:duration={FADE}:offset={offset:.2f}[x{i}]")
        last = f"x{i}"
    out = FIX / "synthetic_sear.mp4"
    subprocess.run(["ffmpeg", "-y", "-v", "error", *inputs, "-filter_complex",
                    ";".join(norm + chain), "-map", f"[{last}]", "-c:v", "libx264",
                    "-pix_fmt", "yuv420p", str(out)], check=True)
    print(f"wrote {out.relative_to(FIX.parent)}")


if __name__ == "__main__":
    main()
