"""Replay a measured clip through the Spark judge, checkpoint by checkpoint.

    uv run scripts/browning.py fixtures/synthetic_sear.mp4 --food "chicken thigh"   # first
    uv run scripts/judge.py synthetic_sear \\
        --step "Sear the chicken thighs skin-side down until deep golden, 6-8 minutes." \\
        --speedup 40

Reads out/<name>/{readings.json,prepared.mp4}. At each checkpoint the judge sees
only the readings up to that moment plus that frame, as it would live.
--speedup maps clip seconds to cooking minutes for compressed test clips (the
AI clip squeezes a 7-minute sear into ~10 s). Writes out/<name>/verdicts.json.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from muse import judge as j  # noqa: E402
from muse.browning import Reading  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def frame_jpg(video: Path, frame: int, fps: float, out: Path) -> Path:
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", f"{frame / fps:.3f}", "-i", str(video),
                    "-frames:v", "1", "-q:v", "3", str(out)], check=True)
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("name", help="folder under out/ written by scripts/browning.py")
    p.add_argument("--step", required=True)
    p.add_argument("--fps", type=float, default=4, help="fps the clip was prepared at")
    p.add_argument("--speedup", type=float, default=1.0)
    p.add_argument("--checkpoints", type=int, default=8)
    args = p.parse_args()

    d = ROOT / "out" / args.name
    readings = [Reading(**r) for r in json.loads((d / "readings.json").read_text())]
    frames = sorted({r.frame for r in readings})

    t0 = time.monotonic()
    spec = j.watch_spec(args.step)
    print(f"spec ({time.monotonic() - t0:.1f}s): {spec.food!r} -> {spec.target_shade} "
          f"(BI {spec.target_bi:.0f}), {spec.minutes_min:g}-{spec.minutes_max:g} min, "
          f"then {spec.turn_action}; protein={spec.protein}")
    print(f"  watch for: {spec.watch_for}\n")

    picks = [frames[round(i * (len(frames) - 1) / (args.checkpoints - 1))]
             for i in range(args.checkpoints)]
    out = []
    for f in picks:
        so_far = [r for r in readings if r.frame <= f]
        elapsed = f / args.fps * args.speedup / 60
        img = frame_jpg(d / "prepared.mp4", f, args.fps, d / f"judge_{f:04d}.jpg")
        t = time.monotonic()
        v = j.verdict(spec, so_far, img, fps=args.fps / args.speedup, elapsed_min=elapsed)
        dt = time.monotonic() - t
        prog = " ".join(f"{k}:{x:.2f}" for k, x in v.progress.items())
        print(f"{elapsed:4.1f} min  [{prog}]  {v.state:<9} {v.action:<10} {dt:4.1f}s  \"{v.say}\"")
        out.append({"frame": f, "elapsed_min": elapsed, "latency_s": dt, **v.as_dict()})
    (d / "verdicts.json").write_text(json.dumps({"spec": spec.__dict__, "verdicts": out}, indent=1))
    print(f"\nwrote out/{args.name}/verdicts.json")


if __name__ == "__main__":
    main()
