"""Run Pimp My Social locally.

    uv run scripts/serve.py                 # http://localhost:8000
    uv run scripts/serve.py --demo          # also lets the crawler reach the local demo site
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import uvicorn

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--port", type=int, default=8000)
    p.add_argument("--demo", action="store_true",
                   help="allow localhost URLs (the demo bakery); never use on a public server")
    args = p.parse_args()
    if args.demo:
        os.environ["PMS_ALLOW_PRIVATE"] = "1"
    print(f"\n  http://localhost:{args.port}\n")
    uvicorn.run("server.app:app", host="127.0.0.1", port=args.port)


if __name__ == "__main__":
    main()
