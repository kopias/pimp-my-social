"""Re-run just the campaign on a finished makeover: uv run scripts/campaign.py <job id>"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import fields
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from pms import campaign  # noqa: E402
from pms.photos import Shot  # noqa: E402
from pms.pipeline import Job  # noqa: E402


def main() -> None:
    job = ROOT / "out" / "jobs" / sys.argv[1]
    state = json.loads((job / "job.json").read_text())
    prof = json.loads((job / "brand.json").read_text())
    direction = next(c for c in json.loads((job / "cards.json").read_text())
                     if c["id"] == state["data"]["direction"])
    keep = {f.name for f in fields(Shot)}
    shots = [Shot(**{k: v for k, v in s.items() if k in keep}) for s in state["data"]["shots"]]
    url = prof["contact"].get("order_url") or state["url"]
    t = time.time()
    out = campaign.make(prof, shots, direction, job / "campaign", url)
    j = Job.load(sys.argv[1])  # so the app shows it: same shape the pipeline writes
    u = j.url_of
    j.state["data"]["campaign"] = {
        **{k: out[k] for k in ("question", "thesis", "gate", "hashtags")},
        "pieces": [{**{k: v for k, v in p.items() if k not in ("image", "raw")},
                    "image": u(p["image"]), "raw": u(p["raw"])} for p in out["pieces"]],
        "film": {**{k: v for k, v in out["film"].items() if k not in ("mp4", "poster", "cast", "beats")},
                 "mp4": u(out["film"]["mp4"]), "poster": u(out["film"]["poster"]), "cast": u(out["film"]["cast"]),
                 "beats": [{**b, "image": u(b["image"])} for b in out["film"]["beats"]]},
    }
    j.save()
    print(json.dumps({k: out[k] for k in ("question", "thesis", "gate")}, indent=1))
    for p in out["pieces"]:
        print(p["kind"], p["persona"], "|", p["headline"], "| takes", p["takes"], p["check"]["note"][:120])
    print("film", out["film"]["mp4"], json.dumps(out["film"]["review"])[:600])
    print(f"{time.time() - t:.0f}s")


if __name__ == "__main__":
    main()
