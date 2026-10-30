"""Pick your paint job: the style directions for the makeover.

Each direction is a template skill modelled on a real fashion site (25 of them, in
inspo/templates/): palette roles, a Google Fonts pairing matched to the site's own
type, a measured anatomy, and a photography brief Muse Image follows for every
product shot. The owner's style tags narrow the field to the templates that carry
them; Spark picks the three that suit the business best from that shortlist; one
more is drawn at random, the wildcard, because sometimes the look you'd never ask
for is the one. Each card gets a real preview: their own hero photo reshot in that
direction.
"""

from __future__ import annotations

import json
import random
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from muse import client as m

from . import templates

STYLE_TAGS = ["minimal", "bold", "warm", "luxury", "playful", "retro", "dark", "natural",
              "techy", "editorial", "bright", "calm", "romantic", "street", "heritage"]

# Every direction is one of the 25 template skills (pms/templates.py): a real fashion
# site, measured, with its palette, type, anatomy and photo brief.
DIRECTIONS: dict[str, dict] = templates.all_templates()


PICK_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["picks"],
    "properties": {"picks": {
        "type": "array", "description": "exactly as many as asked, best fit first",
        "items": {"type": "object", "additionalProperties": False, "required": ["id", "why"],
                  "properties": {"id": {"type": "string", "enum": list(DIRECTIONS)},
                                 "why": {"type": "string",
                                         "description": "one sentence to the owner"}}}}},
}

PICK_PROMPT = """You are the art director on a makeover crew. Pick the {n} style directions that \
would suit this business best, best fit first, and make them different enough from each other \
that the owner has a real choice. Each is modelled on a real fashion site. Weigh who their \
customers are, what they sell, their price point and how they sound. {tags}

Business: {profile}

Directions: {directions}"""


def font_css(d: dict) -> str:
    f = d["fonts"]
    fams = [f["display"], f["body"]] + ([f["label"]] if f.get("label") else [])
    axes = f.get("axes", {})

    def fam(name: str) -> str:
        ax = axes.get(name, "wght@400;500;600;700")
        return "family=" + name.replace(" ", "+") + (":" + ax if ax else "")
    return "https://fonts.googleapis.com/css2?" + "&".join(fam(n) for n in dict.fromkeys(fams)) + "&display=swap"


def how_many(exact: int) -> int:
    """Options to show, 3 to 6 including the wildcard, from how many templates carry every
    tag the owner asked for: a precise ask (one exact fit) gets a short, sure list; a
    broad one (or no tags) gets range."""
    return max(3, min(6, exact + 2))


def pick(profile: dict, tags: list[str], rng: random.Random | None = None) -> list[dict]:
    """Spark's picks plus one random wildcard, as cards: 3 to 6 in all.

    Never the same twice: the shortlist is shuffled and, when it's long, sampled, so two
    makeovers with the same tags meet different templates in a different order."""
    rng = rng or random.Random()
    summary = {k: profile[k] for k in ("name", "one_liner", "category", "audience", "voice",
                                       "value_props")}
    # The tags decide the shortlist: every template carrying the most of them, topped
    # up to 6 by the next best, so Spark chooses by fit inside what the owner asked for.
    ranked = templates.rank(tags) if tags else [(0, k) for k in DIRECTIONS]
    best = ranked[0][0]
    short = [k for n, k in ranked if n == best and n > 0] or [k for _, k in ranked]
    exact = len(short) if tags else len(DIRECTIONS)
    short += [k for n, k in ranked if k not in short and n > 0][:max(0, 6 - len(short))]
    rng.shuffle(short)
    short = short[:10]
    total = how_many(exact)
    n = min(total - 1, len(short))
    menu = {k: {"name": f"{v['style']} (modelled on {v['name']})", "tags": v["tags"], "pitch": v["pitch"],
                "layout": v["layout"][:400]} for k, v in DIRECTIONS.items() if k in short}
    menu = {k: menu[k] for k in short}  # Spark sees them in the shuffled order
    tag_line = (f"The owner chose these style tags; lean toward them: {', '.join(tags)}."
                if tags else "The owner chose no style tags.")
    schema = json.loads(json.dumps(PICK_SCHEMA))
    schema["properties"]["picks"]["items"]["properties"]["id"]["enum"] = list(menu)
    raw = m.ask(PICK_PROMPT.format(n=n, tags=tag_line, profile=json.dumps(summary),
                                   directions=json.dumps(menu)), schema=schema, effort="low")
    seen, cards = set(), []
    for p in json.loads(raw)["picks"]:
        if p["id"] in DIRECTIONS and p["id"] not in seen and len(cards) < n:
            seen.add(p["id"])
            cards.append({"id": p["id"], "why": p["why"], "wildcard": False})
    rest = [k for k in short if k not in seen]
    while len(cards) < n and rest:  # Spark returned fewer than asked
        k = rest.pop(0)
        seen.add(k)
        cards.append({"id": k, "why": "", "wildcard": False})
    rest = [k for k in DIRECTIONS if k not in seen]
    if rest:
        k = rng.choice(rest)
        cards.append({"id": k, "why": "The wildcard: not the obvious choice, which is the point.",
                      "wildcard": True})
    # The card carries the tokens; the builder reads the full skill from the library.
    return [{**c, **{k: v for k, v in DIRECTIONS[c["id"]].items() if k != "skill"},
             "font_css": font_css(DIRECTIONS[c["id"]])} for c in cards]


RESHOOT = ("Reshoot this exact {subject} as a professional product photograph. Keep the "
           "{subject} itself identical: same shape, colours, labels, details and proportions. "
           "Replace only the setting, light and camera: {photo}. Shot on a full-frame camera "
           "with an 85mm lens. Photorealistic, no text, no logos added, no people.")


def preview(card: dict, photo: Path, subject: str, out: Path, tries: int = 2) -> Path:
    """One product photo, reshot in this direction (one Muse Image edit, $0.01). Muse Image
    turns down some requests in a burst with a bare 400 that succeeds moments later, so retry."""
    for k in range(tries):
        try:
            return m.edit_image(photo, RESHOOT.format(subject=subject or "product", photo=card["photo"]), out)
        except Exception:
            if k == tries - 1:
                raise
            time.sleep(2 + 3 * k)


def previews(cards: list[dict], photos: list[list[tuple[Path, str]]], out_dir: Path) -> list[list[Path | None]]:
    """Each card's products (lead first), reshot in that card's direction, all at once."""
    out_dir.mkdir(parents=True, exist_ok=True)
    jobs = [(c, k, photo, subject) for c, row in zip(cards, photos) for k, (photo, subject) in enumerate(row)]

    def one(job: tuple) -> Path | None:
        c, k, photo, subject = job
        try:
            return preview(c, photo, subject, out_dir / f"preview_{c['id']}_{k}.png")
        except Exception as e:
            print(f"preview {c['id']}/{k} failed: {e!r}"[:300])
            return None
    with ThreadPoolExecutor(max_workers=4) as pool:
        done = list(pool.map(one, jobs))
    # Muse Image refuses some edits in a burst; once the burst is over, the misses
    # usually go through one at a time.
    for i, job in enumerate(jobs):
        if done[i] is None:
            time.sleep(3)
            done[i] = one(job)
    out, i = [], 0
    for row in photos:
        out.append(done[i:i + len(row)])
        i += len(row)
    return out
