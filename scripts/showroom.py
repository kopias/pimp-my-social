"""The showroom: finished makeovers a hosted Pimp My Social shows without spending anything.

    uv run scripts/showroom.py add 993e81e2fd --note "Fictional demo bakery"
    uv run scripts/showroom.py add d8d098bfdd --note "A real Oakland boutique" --private
    uv run scripts/showroom.py publish d8d098bfdd        # once the owner has said yes
    uv run scripts/showroom.py list
    uv run scripts/showroom.py stage /tmp/pms-showroom    # the folder to copy to the server

The list lives in out/showroom.json. A private entry is copied to the server but not
listed or served until it's published, so a real business's makeover can be ready to go
the moment its owner agrees. Staging rewrites the absolute paths in each job's JSON
(this machine's home folder) to paths relative to the repo.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out"
JOBS = OUT / "jobs"
LIST = OUT / "showroom.json"
SKIP = {"pimp-my-social-kit.zip.tmp"}


def load() -> list[dict]:
    return json.loads(LIST.read_text()) if LIST.exists() else []


def save(items: list[dict]) -> None:
    LIST.write_text(json.dumps(items, indent=1) + "\n")


def _check(jid: str) -> dict:
    if not re.fullmatch(r"[a-f0-9]{10}", jid) or not (JOBS / jid / "job.json").exists():
        raise SystemExit(f"No job {jid} in out/jobs.")
    st = json.loads((JOBS / jid / "job.json").read_text())
    if st.get("status") != "done":
        raise SystemExit(f"{jid} isn't finished ({st.get('status')}); the showroom only takes finished makeovers.")
    return st


def add(jid: str, note: str, private: bool) -> None:
    st = _check(jid)
    items = [x for x in load() if x["id"] != jid]
    items.append({"id": jid, "note": note, "public": not private, "url": st.get("url", "")})
    save(items)
    print(f"{jid} {'(private) ' if private else ''}added: {st['data'].get('brand', {}).get('name')}")


def publish(jid: str, public: bool = True) -> None:
    items = load()
    for x in items:
        if x["id"] == jid:
            x["public"] = public
            save(items)
            print(f"{jid} is now {'public' if public else 'private'}")
            return
    raise SystemExit(f"{jid} isn't in the showroom; add it first.")


def stage(dest: Path) -> None:
    """Copy every listed job (public or not) and the list into `dest`/out, paths scrubbed."""
    if dest.exists():
        shutil.rmtree(dest)
    (dest / "jobs").mkdir(parents=True)
    home = str(Path.home())
    for x in load():
        src = JOBS / x["id"]
        shutil.copytree(src, dest / "jobs" / x["id"], ignore=shutil.ignore_patterns("*.tmp", ".DS_Store"))
        for f in (dest / "jobs" / x["id"]).rglob("*.json"):
            text = f.read_text()
            clean = text.replace(str(ROOT) + "/", "").replace(home, "~")
            if clean != text:
                f.write_text(clean)
        left = [str(f) for f in (dest / "jobs" / x["id"]).rglob("*") if f.is_file() and f.suffix in (".json", ".html", ".md", ".txt", ".css", ".js")
                and home in f.read_text(errors="ignore")]
        if left:
            raise SystemExit(f"Still names this machine's home folder: {left[:3]}")
    shutil.copy(LIST, dest / "showroom.json")
    size = sum(f.stat().st_size for f in dest.rglob("*") if f.is_file())
    print(f"staged {len(load())} makeovers in {dest} ({size / 1e6:.0f} MB)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("id"); a.add_argument("--note", default=""); a.add_argument("--private", action="store_true")
    p = sub.add_parser("publish"); p.add_argument("id")
    h = sub.add_parser("hide"); h.add_argument("id")
    sub.add_parser("list")
    s = sub.add_parser("stage"); s.add_argument("dest", type=Path)
    args = ap.parse_args()
    if args.cmd == "add":
        add(args.id, args.note, args.private)
    elif args.cmd == "publish":
        publish(args.id)
    elif args.cmd == "hide":
        publish(args.id, False)
    elif args.cmd == "list":
        for x in load():
            print(f"{x['id']}  {'public ' if x['public'] else 'private'}  {x['url']}  {x['note']}")
    else:
        stage(args.dest)


if __name__ == "__main__":
    main()
