"""Pick your paint job: editorial style directions for the makeover.

A small library of looks, each a complete kit: palette roles, a Google Fonts pairing,
a layout idea, and a photography brief that Muse Image follows for every product
shot. Spark picks the three that suit the business (steered by any style tags the
owner chose); one more is drawn at random, the wildcard, because sometimes the
look you'd never ask for is the one. Each card gets a real preview: their own hero
photo reshot in that direction.
"""

from __future__ import annotations

import json
import random
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from muse import client as m

STYLE_TAGS = ["minimal", "bold", "warm", "luxury", "playful", "retro", "dark", "natural",
              "techy", "editorial", "bright", "calm"]

DIRECTIONS: dict[str, dict] = {
    "gallery": {
        "name": "Gallery", "tags": ["minimal", "calm", "editorial", "natural"],
        "pitch": "Quiet confidence. Lots of air, one beautiful photo at a time.",
        "palette": {"bg": "#F4F1EA", "surface": "#EAE5DA", "ink": "#1B1A17", "muted": "#6E685D",
                    "accent": "#9A6B3F", "accent2": "#2F4A3A"},
        "fonts": {"display": "Fraunces", "body": "Inter"},
        "layout": "asymmetric editorial grid, oversized serif headlines, generous whitespace, "
                  "captions in small caps",
        "photo": "soft north-window daylight, linen and pale stone surfaces, shallow depth of "
                 "field at f/2, muted natural tones, quiet negative space",
    },
    "front_page": {
        "name": "Front Page", "tags": ["editorial", "bold", "retro"],
        "pitch": "Your business as the day's headline story.",
        "palette": {"bg": "#F3EFE6", "surface": "#E7E1D3", "ink": "#111111", "muted": "#5C5850",
                    "accent": "#C8102E", "accent2": "#111111"},
        "fonts": {"display": "Playfair Display", "body": "IBM Plex Sans"},
        "layout": "newspaper columns, rules between sections, a masthead, pull quotes, "
                  "drop caps, dateline details",
        "photo": "direct on-camera flash, high contrast, crisp shadows, slightly grainy "
                 "magazine print feel, bold crop",
    },
    "night_shift": {
        "name": "Night Shift", "tags": ["dark", "luxury", "bold"],
        "pitch": "Low light, high gloss. Feels like an invitation.",
        "palette": {"bg": "#0E0E10", "surface": "#18181B", "ink": "#F3EEE6", "muted": "#9C968C",
                    "accent": "#D9C29A", "accent2": "#7A5C3A"},
        "fonts": {"display": "Cormorant Garamond", "body": "Manrope"},
        "layout": "full-bleed dark sections, thin gold rules, centered serif display type, "
                  "slow fades",
        "photo": "low-key studio lighting, single rim light, deep black backdrop, glossy "
                 "highlights, shallow depth of field, cinematic",
    },
    "sunday_market": {
        "name": "Sunday Market", "tags": ["warm", "natural", "playful"],
        "pitch": "Sunlit, handmade, good to be around.",
        "palette": {"bg": "#FBF3E4", "surface": "#F3E3C7", "ink": "#2B2118", "muted": "#7A6A58",
                    "accent": "#C65D3B", "accent2": "#6B7A3A"},
        "fonts": {"display": "DM Serif Display", "body": "DM Sans"},
        "layout": "rounded cards, hand-drawn underlines, stacked photo collages, warm "
                  "section colour blocks",
        "photo": "golden hour sunlight, warm wood and ceramic props, natural textures, soft "
                 "shadows, shallow depth of field, lived-in",
    },
    "riso_pop": {
        "name": "Riso Pop", "tags": ["playful", "bold", "bright", "retro"],
        "pitch": "Loud, joyful, impossible to scroll past.",
        "palette": {"bg": "#FFF4E0", "surface": "#FFE3B8", "ink": "#1D1B4C", "muted": "#5A577E",
                    "accent": "#FF5FA2", "accent2": "#2F5DFF"},
        "fonts": {"display": "Bricolage Grotesque", "body": "Space Grotesk"},
        "layout": "chunky type, sticker shapes, offset drop shadows, tilted cards, colour "
                  "blocked sections",
        "photo": "saturated solid colour backdrop, hard direct light, bold graphic shadow, "
                 "playful high-key product shot",
    },
    "swiss_utility": {
        "name": "Swiss Utility", "tags": ["minimal", "techy", "bright"],
        "pitch": "Precise, honest, every detail where you expect it.",
        "palette": {"bg": "#FFFFFF", "surface": "#F2F2F2", "ink": "#111111", "muted": "#6B6B6B",
                    "accent": "#FF4F00", "accent2": "#111111"},
        "fonts": {"display": "Inter Tight", "body": "Inter"},
        "layout": "strict 12-column grid, big numerals, monospace labels, spec tables, "
                  "hairline borders",
        "photo": "seamless white sweep, even soft-box light, catalogue precision, true "
                 "colour, subtle floor shadow",
    },
    "chrome": {
        "name": "Chrome", "tags": ["techy", "bold", "retro", "bright"],
        "pitch": "Y2K gloss for brands that want to feel like the future.",
        "palette": {"bg": "#E9ECF2", "surface": "#D9DEE8", "ink": "#0D0F1A", "muted": "#5B6275",
                    "accent": "#7B5CFF", "accent2": "#00C2FF"},
        "fonts": {"display": "Unbounded", "body": "Inter"},
        "layout": "glassy panels, gradient strokes, pill buttons, big rounded type, "
                  "floating product renders",
        "photo": "glossy reflective surface, iridescent gradient backdrop, crisp specular "
                 "highlights, futuristic studio",
    },
    "coastal": {
        "name": "Coastal", "tags": ["calm", "bright", "natural", "luxury"],
        "pitch": "Fresh air and good taste. Easy to trust.",
        "palette": {"bg": "#EEF4F3", "surface": "#DCE9E7", "ink": "#0F3D3E", "muted": "#5E7B7A",
                    "accent": "#D88C5A", "accent2": "#0F3D3E"},
        "fonts": {"display": "Libre Caslon Text", "body": "Karla"},
        "layout": "airy split layouts, soft rounded images, thin serif headings, "
                  "pale tinted sections",
        "photo": "bright airy daylight, reflected water light, pale sand and white linen, "
                 "soft shadows, relaxed",
    },
}

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
would suit this business best, best fit first. Weigh who their customers are, what they sell \
and how they sound. {tags}

Business: {profile}

Directions: {directions}"""


def font_css(d: dict) -> str:
    fams = [d["fonts"]["display"], d["fonts"]["body"]]
    q = "&".join("family=" + f.replace(" ", "+") + ":wght@400;500;600;700" for f in dict.fromkeys(fams))
    return f"https://fonts.googleapis.com/css2?{q}&display=swap"


def pick(profile: dict, tags: list[str], rng: random.Random | None = None) -> list[dict]:
    """Three picks from Spark plus one random wildcard, as cards."""
    rng = rng or random.Random()
    summary = {k: profile[k] for k in ("name", "one_liner", "category", "audience", "voice",
                                       "value_props")}
    menu = {k: {"name": v["name"], "tags": v["tags"], "pitch": v["pitch"]} for k, v in DIRECTIONS.items()}
    tag_line = (f"The owner chose these style tags; lean toward them: {', '.join(tags)}."
                if tags else "The owner chose no style tags.")
    raw = m.ask(PICK_PROMPT.format(tags=tag_line, profile=json.dumps(summary),
                                   directions=json.dumps(menu)), schema=PICK_SCHEMA, effort="low")
    seen, cards = set(), []
    for p in json.loads(raw)["picks"]:
        if p["id"] in DIRECTIONS and p["id"] not in seen:
            seen.add(p["id"])
            cards.append({"id": p["id"], "why": p["why"], "wildcard": False})
    rest = [k for k in DIRECTIONS if k not in seen]
    while len(cards) < 3 and rest:  # Spark returned fewer than asked
        k = rest.pop(rng.randrange(len(rest)))
        seen.add(k)
        cards.append({"id": k, "why": "", "wildcard": False})
    if rest:
        k = rng.choice(rest)
        cards.append({"id": k, "why": "The wildcard: not the obvious choice, which is the point.",
                      "wildcard": True})
    return [{**c, **DIRECTIONS[c["id"]], "font_css": font_css(DIRECTIONS[c["id"]])} for c in cards]


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
