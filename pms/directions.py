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
        "type": "array", "description": "exactly 3, best fit first",
        "items": {"type": "object", "additionalProperties": False, "required": ["id", "why"],
                  "properties": {"id": {"type": "string", "enum": list(DIRECTIONS)},
                                 "why": {"type": "string",
                                         "description": "one sentence to the owner"}}}}},
}

PICK_PROMPT = """You are the art director on a makeover crew. Pick the 3 style directions that \
would suit this business best, best fit first. Each is modelled on a real fashion site. Weigh \
who their customers are, what they sell, their price point and how they sound. {tags}

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


def pick(profile: dict, tags: list[str], rng: random.Random | None = None) -> list[dict]:
    """Three picks from Spark plus one random wildcard, as cards."""
    rng = rng or random.Random()
    summary = {k: profile[k] for k in ("name", "one_liner", "category", "audience", "voice",
                                       "value_props")}
    # The tags decide the shortlist: every template carrying the most of them, topped
    # up to 6 by the next best, so Spark chooses by fit inside what the owner asked for.
    ranked = templates.rank(tags) if tags else [(0, k) for k in DIRECTIONS]
    best = ranked[0][0]
    short = [k for n, k in ranked if n == best and n > 0] or [k for _, k in ranked]
    short += [k for n, k in ranked if k not in short and n > 0][:max(0, 6 - len(short))]
    menu = {k: {"name": f"{v['style']} (modelled on {v['name']})", "tags": v["tags"], "pitch": v["pitch"],
                "layout": v["layout"][:400]} for k, v in DIRECTIONS.items() if k in short}
    tag_line = (f"The owner chose these style tags; lean toward them: {', '.join(tags)}."
                if tags else "The owner chose no style tags.")
    schema = json.loads(json.dumps(PICK_SCHEMA))
    schema["properties"]["picks"]["items"]["properties"]["id"]["enum"] = list(menu)
    raw = m.ask(PICK_PROMPT.format(tags=tag_line, profile=json.dumps(summary),
                                   directions=json.dumps(menu)), schema=schema, effort="low")
    seen, cards = set(), []
    for p in json.loads(raw)["picks"]:
        if p["id"] in DIRECTIONS and p["id"] not in seen:
            seen.add(p["id"])
            cards.append({"id": p["id"], "why": p["why"], "wildcard": False})
    rest = [k for k in short if k not in seen] + [k for k in DIRECTIONS if k not in short and k not in seen]
    while len(cards) < 3 and rest:  # Spark returned fewer than asked
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


def preview(card: dict, photo: Path, subject: str, out: Path) -> Path:
    """Their hero photo, reshot in this direction (one Muse Image edit, $0.01)."""
    return m.edit_image(photo, RESHOOT.format(subject=subject or "product", photo=card["photo"]), out)


def previews(cards: list[dict], photo: Path, subject: str, out_dir: Path) -> list[Path | None]:
    out_dir.mkdir(parents=True, exist_ok=True)

    def one(c: dict) -> Path | None:
        try:
            return preview(c, photo, subject, out_dir / f"preview_{c['id']}.png")
        except Exception as e:
            print(f"preview {c['id']} failed: {e!r}"[:300])
            return None
    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(one, cards))
