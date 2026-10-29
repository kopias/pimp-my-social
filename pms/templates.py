"""The template library: 25 modern fashion sites, each written up as a build skill.

Source list: Linguise, "Top 25 fashion website design for inspiration". Every site
was captured and measured in a real browser (scripts/capture_templates.py), and its
skill (inspo/templates/<id>/SKILL.md) is the spec a makeover is built to: a JSON
block of tokens (palette, fonts, measured type, layout, photo brief and the
signature moves the fidelity check looks for), then the anatomy in prose.

The owner's style tags map to templates by overlap; Spark breaks ties by fit.
"""

from __future__ import annotations

import json
import re
from functools import cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "inspo" / "templates"

SOURCES = {
    "cos": "https://www.cos.com/en-us",
    "sandy_liang": "https://www.sandyliang.info/",
    "ganni": "https://www.ganni.com/us/home",
    "khy": "https://www.khy.com/",
    "lisa_says_gah": "https://lisasaysgah.com/",
    "sezane": "https://www.sezane.com/us-en",
    "blandin_delloye": "https://www.blandindelloye.com/",
    "me_em": "https://www.meandem.com/us",
    "farm_rio": "https://farmrio.com/",
    "dior": "https://www.dior.com/en_us",
    "maison_labiche": "https://www.maisonlabiche.com/",
    "idioma": "https://idioma.world/",
    "sleeper": "https://the-sleeper.com/",
    "olive": "https://www.oliveclothing.com/",
    "rouvenat": "https://rouvenat.com/",
    "mango": "https://shop.mango.com/us",
    "flannels": "https://www.flannels.com/",
    "everlane": "https://www.everlane.com/",
    "valentino": "https://www.valentino.com/en-us/",
    "tiffany": "https://www.tiffany.com/",
    "carolina_herrera": "https://www.carolinaherrera.com/us/en",
    "bouguessa": "https://bouguessa.com/",
    "net_a_porter": "https://www.net-a-porter.com/en-us/",
    "madina_visconti": "https://madinavisconti.com/",
    "rino_pelle": "https://rino-pelle.com/",
}

TOKENS = re.compile(r"```json\n(.*?)\n```", re.S)


@cache
def load(tid: str) -> dict:
    """The template's tokens, plus `skill` (the prose after the token block) and `source`."""
    text = (ROOT / tid / "SKILL.md").read_text()
    m = TOKENS.search(text)
    t = json.loads(m.group(1))
    body = text[m.end():].strip()
    head = re.sub(r"^---.*?---\s*", "", text[:m.start()], flags=re.S).strip()
    return {**t, "source": SOURCES[tid], "skill": head + "\n\n" + body}


def all_templates() -> dict[str, dict]:
    return {tid: load(tid) for tid in SOURCES}


def shots(tid: str) -> list[Path]:
    """Desktop first screen, one scroll down, and the phone screen, where captured.
    Blocked desktop captures are skipped (they're an error page, not the design)."""
    d = ROOT / tid
    meas = json.loads((d / "measured.json").read_text()) if (d / "measured.json").exists() else {}
    names = ["mobile_1.jpg"] if meas.get("blocked") else ["desktop_1.jpg", "desktop_2.jpg", "mobile_1.jpg"]
    return [d / n for n in names if (d / n).exists()]


def rank(tags: list[str]) -> list[tuple[int, str]]:
    """Templates by how many of the owner's tags they carry, best first (stable order)."""
    return sorted(((len(set(tags) & set(t["tags"])), tid) for tid, t in all_templates().items()),
                  key=lambda x: -x[0])


def match(tags: list[str]) -> str:
    """The single best template for a set of style tags (first in file order on a tie)."""
    return rank(tags)[0][1]
