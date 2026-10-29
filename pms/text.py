"""House style for every word we ship: the old site's punctuation habits stop here.

Models mirror the voice they're shown, and a small business's site often shouts
("Saturdays only!! (NEW!)"). Prompts ask for restraint; this makes sure of it,
without touching facts: it only changes punctuation and shouting.
"""

from __future__ import annotations

import re
from typing import Any

SKIP_KEYS = {"url", "order_url", "email", "phone", "handle", "image", "path", "price"}


def tidy(s: str, max_bangs: int = 1) -> str:
    s = re.sub(r"\s*\((?:new|NEW|New)!*\)", "", s)  # "(NEW!)" asides
    s = re.sub(r"([!?])\1+", r"\1", s)  # "!!" -> "!"
    s = re.sub(r"!\?|\?!", "?", s)
    seen = 0

    def bang(mt: re.Match) -> str:
        nonlocal seen
        seen += 1
        return "!" if seen <= max_bangs else "."
    s = re.sub(r"!", bang, s)
    # Shouting: a run of 2+ all-caps words, or one long one. A lone short one is
    # probably an acronym (BBQ, FAQ) and stays.
    s = re.sub(r"\b[A-Z]{2,}(?:[\s,]+[A-Z]{2,})+\b|\b[A-Z]{5,}\b",
               lambda mt: re.sub(r"[A-Z]+", lambda w: w.group(0).capitalize(), mt.group(0)), s)
    return re.sub(r"\.\.+(?!\.)", ".", s).strip()


def tidy_all(x: Any, key: str = "") -> Any:
    """tidy() every string in a JSON-like structure, except contact details and URLs."""
    if isinstance(x, dict):
        return {k: tidy_all(v, k) for k, v in x.items()}
    if isinstance(x, list):
        return [tidy_all(v, key) for v in x]
    if isinstance(x, str) and key not in SKIP_KEYS and not x.startswith(("http", "#")):
        return tidy(x)
    return x
