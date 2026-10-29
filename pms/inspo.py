"""The inspiration library (inspo/): design notes on real brand sites, for the builder.

Each direction names its references; the builder gets their notes, the typography
system and, when they've been captured on this machine, a screenshot of each as a
visual reference. Structure is borrowed, never content.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "inspo"

# id -> (notes file, screenshot prefix, url)
REFS = {
    "toteme": ("toteme.md", "toteme", "https://toteme.com/"),
    "lemaire": ("lemaire.md", "lemaire", "https://www.lemaire.fr/"),
    "studio_nicholson": ("studio-nicholson.md", "studionicholson", "https://www.studionicholson.com/"),
    "aime_leon_dore": ("aime-leon-dore.md", "ald", "https://www.aimeleondore.com/"),
    "our_legacy": ("our-legacy.md", "ourlegacy", "https://www.ourlegacy.com/"),
    "bode": ("bode.md", "bode", "https://bode.com/"),
    "story_mfg": ("story-mfg.md", "storymfg", "https://www.storymfg.com/"),
    "kotn": ("kotn.md", "kotn", "https://kotn.com/"),
}


def typography() -> str:
    return (ROOT / "typography.md").read_text()


def notes(ids: list[str]) -> str:
    return "\n\n".join((ROOT / "references" / REFS[i][0]).read_text() for i in ids if i in REFS)


def shots(ids: list[str], per_ref: int = 1) -> list[Path]:
    out = []
    for i in ids:
        if i in REFS:
            out += sorted((ROOT / "shots").glob(f"{REFS[i][1]}_*.jpg"))[:per_ref]
    return out
