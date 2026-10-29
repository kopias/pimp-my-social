"""The social kit: posts, captions and profile copy for each channel the owner picked.

Muse Spark plans each channel in the brand's voice from the profile (the same
no-invented-facts rule as the website), and picks which reshoot goes with which
post. Code then composes the images: crops for each format, and type-set cards
in the direction's own fonts and colours.
"""

from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path

import requests
from PIL import Image, ImageDraw, ImageFont

from muse import client as m

from .photos import Shot
from .text import tidy_all

CHANNELS = {
    "instagram": {"name": "Instagram", "posts": 6, "format": (1080, 1350)},
    "tiktok": {"name": "TikTok", "posts": 0, "format": (1080, 1920)},
    "facebook": {"name": "Facebook", "posts": 3, "format": (1200, 1200)},
    "linkedin": {"name": "LinkedIn", "posts": 2, "format": (1200, 1200)},
    "x": {"name": "X", "posts": 3, "format": (1600, 900)},
}

POST = {
    "type": "object", "additionalProperties": False,
    "required": ["photo", "kind", "overlay", "caption", "alt"],
    "properties": {
        "photo": {"type": "integer", "description": "index into the photo list"},
        "kind": {"type": "string", "enum": ["photo", "card"],
                 "description": "photo: the shot alone; card: the shot with the overlay text set on it"},
        "overlay": {"type": "string", "description": "for cards: under 8 words; else ''"},
        "caption": {"type": "string"},
        "alt": {"type": "string"},
    },
}

PLAN_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["handle", "bio", "hashtags", "channels", "video"],
    "properties": {
        "handle": {"type": "string", "description": "suggested @handle without @"},
        "bio": {"type": "string", "description": "profile bio, under 150 characters"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "channels": {
            "type": "array",
            "items": {"type": "object", "additionalProperties": False,
                      "required": ["channel", "posts"],
                      "properties": {"channel": {"type": "string", "enum": list(CHANNELS)},
                                     "posts": {"type": "array", "items": POST}}},
        },
        "video": {
            "type": "object", "additionalProperties": False,
            "required": ["hook", "lines", "caption", "end_card"],
            "properties": {
                "hook": {"type": "string", "description": "on-screen text for the first 2 seconds, under 7 words"},
                "lines": {"type": "array", "items": {
                    "type": "object", "additionalProperties": False, "required": ["photo", "say"],
                    "properties": {"photo": {"type": "integer"},
                                   "say": {"type": "string", "description": "one spoken sentence, under 12 words"}}},
                    "description": "4-5 voiceover lines, one shot each, 15-20 seconds in all"},
                "caption": {"type": "string"},
                "end_card": {"type": "string", "description": "closing line, under 8 words"},
            },
        },
    },
}

PLAN_PROMPT = """You are the social media lead on a makeover crew. Plan this small business's \
social presence in their voice ({voice}), at a professional standard: specific, warm, no \
filler, no emoji spam (at most two per caption), no ALL CAPS.

Channels: {channels}. Posts per channel: {counts}. Instagram captions open with a hook \
line; LinkedIn is about the business and its people; X is short.
Also write a 15-20 second vertical video (TikTok/Reels): a hook, then 4-5 spoken lines, \
one photo each, and an end card.

Facts only from the profile: the same products, prices exactly as written, hours, \
place. Never invent reviews, numbers, awards, discounts or events.

Photos you can use (index: what it shows): {photos}

Brand profile: {profile}"""


def plan(profile: dict, shots: list[Shot], channels: list[str]) -> dict:
    counts = {c: CHANNELS[c]["posts"] for c in channels if CHANNELS[c]["posts"]}
    photos = {i: s.product for i, s in enumerate(shots)}
    raw = m.ask(PLAN_PROMPT.format(voice=", ".join(profile["voice"]["adjectives"]),
                                   channels=", ".join(CHANNELS[c]["name"] for c in channels),
                                   counts=json.dumps(counts), photos=json.dumps(photos),
                                   profile=json.dumps(profile)),
                schema=PLAN_SCHEMA, effort="medium", max_tokens=12000)
    out = json.loads(raw)
    n = len(shots)
    for ch in out["channels"]:
        for p in ch["posts"]:
            p["photo"] = p["photo"] % n if n else -1
    for line in out["video"]["lines"]:
        line["photo"] = line["photo"] % n if n else -1
    out["channels"] = [c for c in out["channels"] if c["channel"] in channels]
    return tidy_all(out)


# --- fonts and composition -------------------------------------------------------

FONT_DIR = Path(__file__).resolve().parent.parent / "out" / "fonts"


def font(family: str, weight: int = 700) -> Path | None:
    """A TTF from Google Fonts, cached. Old user agents get TTF instead of WOFF2."""
    FONT_DIR.mkdir(parents=True, exist_ok=True)
    path = FONT_DIR / f"{re.sub(r'[^A-Za-z0-9]', '', family)}-{weight}.ttf"
    if path.exists():
        return path
    css = requests.get("https://fonts.googleapis.com/css2",
                       params={"family": f"{family}:wght@{weight}"},
                       headers={"User-Agent": "Mozilla/4.0"}, timeout=15)
    if css.status_code != 200:  # some families don't have every weight
        css = requests.get("https://fonts.googleapis.com/css2", params={"family": family},
                           headers={"User-Agent": "Mozilla/4.0"}, timeout=15)
    url = re.search(r"url\((https://[^)]+\.ttf)\)", css.text)
    if not url:
        return None
    path.write_bytes(requests.get(url.group(1), timeout=30).content)
    return path


def load_font(family: str, size: int, weight: int = 700) -> ImageFont.FreeTypeFont:
    try:
        p = font(family, weight)
        if p:
            return ImageFont.truetype(str(p), size)
    except (requests.RequestException, OSError):
        pass
    return ImageFont.load_default(size)


def cover(src: Path, size: tuple[int, int]) -> Image.Image:
    im = Image.open(src).convert("RGB")
    r = max(size[0] / im.width, size[1] / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    left, top = (im.width - size[0]) // 2, (im.height - size[1]) // 2
    return im.crop((left, top, left + size[0], top + size[1]))


def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


def card(photo: Path, text: str, direction: dict, size: tuple[int, int], name: str) -> Image.Image:
    """The photo with a headline set in the direction's display face on a colour band."""
    im = cover(photo, size)
    w, h = size
    pal = direction["palette"]
    band_h = int(h * 0.30)
    draw = ImageDraw.Draw(im, "RGBA")
    bg = _hex(pal["bg"])
    draw.rectangle((0, h - band_h, w, h), fill=(*bg, 240))
    display = load_font(direction["fonts"]["display"], int(w * 0.075))
    small = load_font(direction["fonts"]["body"], int(w * 0.026), 500)
    lines = textwrap.wrap(text, width=max(12, int(22 * 1080 / w * w / 1080)))[:3]
    y = h - band_h + int(band_h * 0.16)
    for line in lines:
        draw.text((int(w * 0.07), y), line, font=display, fill=_hex(pal["ink"]))
        y += int(display.size * 1.12)
    draw.rectangle((int(w * 0.07), h - int(band_h * 0.2), int(w * 0.07) + 60, h - int(band_h * 0.2) + 6),
                   fill=_hex(pal["accent"]))
    draw.text((int(w * 0.07) + 80, h - int(band_h * 0.2) - small.size // 2 + 3), name.upper(),
              font=small, fill=_hex(pal["muted"]))
    return im


def compose(social: dict, shots: list[Shot], direction: dict, name: str, out: Path) -> dict:
    """Write every post image; returns the plan with image paths filled in."""
    out.mkdir(parents=True, exist_ok=True)
    for ch in social["channels"]:
        size = CHANNELS[ch["channel"]]["format"]
        used: set[int] = set()
        for k, post in enumerate(ch["posts"]):
            if post["photo"] < 0:
                continue
            shot = shots[post["photo"]]
            src = Path(shot.portrait if size[1] > size[0] else shot.landscape)
            if post["photo"] in used and shot.detail:  # second appearance: the close-up
                src = Path(shot.detail)
            used.add(post["photo"])
            im = card(src, post["overlay"], direction, size, name) if post["kind"] == "card" and post["overlay"] \
                else cover(src, size)
            path = out / f"{ch['channel']}_{k + 1}.jpg"
            im.save(path, "JPEG", quality=88)
            post["image"] = str(path)
    return social
