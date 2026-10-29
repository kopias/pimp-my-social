"""Build a finished makeover's site on one or more templates and check each against the original.

    uv run scripts/template_qa.py <job id> sleeper rino_pelle   # these templates
    uv run scripts/template_qa.py <job id> --tags warm romantic  # what those tags map to
    uv run scripts/template_qa.py <job id> --all                 # all 25 (slow)

Reuses the job's brand profile, studio photos and remade logo, so only the site is
rebuilt. Each template gets out/template-qa/<job>/<id>/: the site, fidelity.json
(every round's scores and fixes) and compare.jpg (template above, built page below,
desktop first screen, then the top of the whole page, phone). summary.json ranks them.
"""

from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import fields
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pms import directions, site, templates  # noqa: E402
from pms.photos import Shot  # noqa: E402


def compare_sheet(tid: str, built: list[Path], out: Path) -> None:
    """Template row over built row: desktop 1, desktop 2, phone."""
    ref = {p.name: p for p in templates.shots(tid)}
    rows = [[ref.get("desktop_1.jpg"), ref.get("desktop_2.jpg"), ref.get("mobile_1.jpg")], built]
    W, H, PW, PH, pad = 720, 450, 208, 450, 12
    sheet = Image.new("RGB", (2 * W + PW + 4 * pad, 2 * H + 3 * pad + 40), "#EDEBE6")
    d = ImageDraw.Draw(sheet)
    for r, row in enumerate(rows):
        y = 40 + pad + r * (H + pad)
        d.text((pad, y - 30 if r == 0 else y - 14), ("TEMPLATE: " + templates.load(tid)["name"]) if r == 0
               else "BUILT", fill="#111")
        for c, p in enumerate(row):
            w, h = (PW, PH) if c == 2 else (W, H)
            x = pad + c * (W + pad)
            if p and Path(p).exists():
                im = Image.open(p).convert("RGB")
                im = im.resize((w, int(im.height * w / im.width)))
                sheet.paste(im.crop((0, 0, w, h)), (x, y))
            else:
                d.rectangle((x, y, x + w, y + h), outline="#999")
                d.text((x + 10, y + 10), "not captured (bot check)", fill="#777")
    sheet.save(out, quality=82)


def one(job: Path, tid: str, base: Path) -> dict:
    state = json.loads((job / "job.json").read_text())
    prof = json.loads((job / "brand.json").read_text())
    keep = {f.name for f in fields(Shot)}
    shots = [Shot(**{k: v for k, v in s.items() if k in keep}) for s in state["data"]["shots"]]
    mark = None
    if (job / "logo" / "mark.png").exists():
        w, h = Image.open(job / "logo" / "mark.png").size
        mark = {"mark": str(job / "logo" / "mark.png"), "mark_light": str(job / "logo" / "mark_light.png"),
                "w": w, "h": h}
    direction = {"id": tid, **directions.DIRECTIONS[tid], "font_css": directions.font_css(directions.DIRECTIONS[tid])}
    out = base / tid
    site.clear(out)
    t = time.time()
    built = site.build(prof, direction, shots, state["url"], out, mark)
    checks = json.loads((out / "fidelity.json").read_text())
    best = max(checks, key=lambda c: c["overall"]) if checks else None
    if best:
        compare_sheet(tid, [Path(p) for p in best["shots"]], out / "compare.jpg")
    res = {**(built.get("fidelity") or {}), "template": tid, "name": direction["name"],
           "seconds": round(time.time() - t)}
    print(json.dumps(res), flush=True)
    return res


def main() -> None:
    job = ROOT / "out" / "jobs" / sys.argv[1]
    args = sys.argv[2:]
    if "--all" in args:
        ids = list(templates.SOURCES)
    elif "--tags" in args:
        ids = [templates.match(args[args.index("--tags") + 1:])]
    else:
        ids = args
    base = ROOT / "out" / "template-qa" / sys.argv[1]
    base.mkdir(parents=True, exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda tid: one(job, tid, base), ids))
    summary = base / "summary.json"
    prev = json.loads(summary.read_text()) if summary.exists() else {}
    prev.update({r["template"]: r for r in results})
    summary.write_text(json.dumps(prev, indent=1))


if __name__ == "__main__":
    main()
