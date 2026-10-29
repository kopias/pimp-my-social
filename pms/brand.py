"""Muse Spark reads the business: the brand profile everything else is built from.

Spark gets the before screenshots, the best candidate photos and the text of the
pages, and returns one structured profile: who they are, what they sell (each
product matched to one of the photos), how they talk, what customers ask. The
prompt holds it to what the site says. Nothing invented: no prices, awards,
reviews or claims that aren't on the page, because these words go on a real
business's site.
"""

from __future__ import annotations

import io
import json
from dataclasses import dataclass
from pathlib import Path

import requests
from PIL import Image as PILImage

from muse import client as m

from .crawl import UA, Site, _allowed

MAX_PHOTOS = 10  # candidate photos shown to Spark
MAX_TEXT = 14000  # characters of page text

PROFILE_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["name", "one_liner", "category", "audience", "location", "contact", "products",
                 "voice", "value_props", "proof", "faqs", "keywords", "hashtags",
                 "hero_photo", "colors", "gaps"],
    "properties": {
        "name": {"type": "string"},
        "one_liner": {"type": "string", "description": "what they do, for whom, in under 20 words"},
        "category": {"type": "string", "description": "e.g. 'bakery', 'online piano lessons'"},
        "audience": {"type": "string"},
        "location": {"type": "string", "description": "city/region if the site says, else ''"},
        "contact": {
            "type": "object", "additionalProperties": False,
            "required": ["address", "phone", "email", "hours", "order_url"],
            "properties": {
                "address": {"type": "string"}, "phone": {"type": "string"},
                "email": {"type": "string"},
                "hours": {"type": "array", "items": {"type": "string"},
                          "description": "one line per day or range, as the site states"},
                "order_url": {"type": "string",
                              "description": "absolute URL for buying/booking/ordering, else ''"},
            },
        },
        "products": {
            "type": "array", "description": "up to 6 products, services or offers the site sells",
            "items": {
                "type": "object", "additionalProperties": False,
                "required": ["name", "description", "price", "photo", "subject"],
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string", "description": "from the site, 1-2 sentences"},
                    "price": {"type": "string", "description": "exactly as the site shows it, else ''"},
                    "photo": {"type": "integer",
                              "description": "index of the candidate photo that shows it, -1 if none"},
                    "subject": {"type": "string",
                                "description": "the physical thing in that photo, as a short noun "
                                               "phrase for an object segmenter: 'croissant', "
                                               "'ceramic mug', 'piano keyboard'"},
                },
            },
        },
        "voice": {
            "type": "object", "additionalProperties": False,
            "required": ["adjectives", "do", "dont", "sample"],
            "properties": {
                "adjectives": {"type": "array", "items": {"type": "string"}},
                "do": {"type": "array", "items": {"type": "string"}},
                "dont": {"type": "array", "items": {"type": "string"}},
                "sample": {"type": "string", "description": "a sentence in their voice, from the site"},
            },
        },
        "value_props": {"type": "array", "items": {"type": "string"}},
        "proof": {"type": "array", "items": {"type": "string"},
                  "description": "testimonials, numbers, press quoted on the site; [] if none"},
        "faqs": {
            "type": "array", "description": "5-8 questions customers ask, answered ONLY from the site",
            "items": {"type": "object", "additionalProperties": False, "required": ["q", "a"],
                      "properties": {"q": {"type": "string"}, "a": {"type": "string"}}},
        },
        "keywords": {"type": "array", "items": {"type": "string"},
                     "description": "8-12 search phrases real customers would type"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "hero_photo": {"type": "integer", "description": "best candidate photo for a hero, -1 if none"},
        "colors": {"type": "array", "items": {"type": "string"},
                   "description": "the brand's own colours as hex, from the screenshots and logo"},
        "gaps": {"type": "array", "items": {"type": "string"},
                 "description": "what a customer can't find out from this site that they'd want to"},
    },
}

PROMPT = """You are the lead of a makeover crew, inspecting a small business's website before \
a redesign. The screenshots are the homepage (desktop, then phone). The other images are \
candidate photos from the site, numbered 0 to {last} in the order given. The text below is \
from the site's pages.

Build the brand profile. Rules, because every word goes on a real business's site:
- Use only what the site shows or says. Never invent prices, reviews, awards, numbers, \
locations or claims. Empty string or empty list when the site doesn't say.
- Products: what they actually sell. Match each to the candidate photo that shows it, or -1.
- FAQs: questions a customer would ask, with answers taken from the site's text. Skip a \
question rather than guess its answer.
- Voice: how they sound now, so the makeover keeps it.

Colours seen in the rendered CSS, most used first: {colors}
Fonts: {fonts}
Social profiles linked: {socials}

{pages}"""


@dataclass
class Photo:
    index: int
    url: str
    path: str
    alt: str
    width: int
    height: int


def download_photos(site: Site, out: Path, limit: int = MAX_PHOTOS) -> list[Photo]:
    """Save the top candidate photos locally as JPEG (the reshoot works from these)."""
    out.mkdir(parents=True, exist_ok=True)
    photos: list[Photo] = []
    for img in site.images:
        if len(photos) >= limit:
            break
        if not _allowed(img.url):
            continue
        try:
            r = requests.get(img.url, headers={"User-Agent": UA}, timeout=15)
            r.raise_for_status()
            im = PILImage.open(io.BytesIO(r.content)).convert("RGB")
        except Exception:
            continue
        im.thumbnail((1600, 1600))
        path = out / f"{len(photos):02d}.jpg"
        im.save(path, "JPEG", quality=90)
        photos.append(Photo(len(photos), img.url, str(path), img.alt, im.width, im.height))
    return photos


def _pages_text(site: Site) -> str:
    parts, budget = [], MAX_TEXT
    for p in site.pages:
        block = f"--- {p.url}\nTitle: {p.title}\nDescription: {p.description}\n" \
                f"Headings: {' | '.join(p.headings[:20])}\n{p.text}"
        parts.append(block[:budget])
        budget -= len(parts[-1])
        if budget <= 0:
            break
    return "\n\n".join(parts)


def read_brand(site: Site, photos: list[Photo]) -> dict:
    prompt = PROMPT.format(last=max(len(photos) - 1, 0), colors=", ".join(site.colors),
                           fonts=", ".join(site.fonts), socials=", ".join(site.socials) or "none",
                           pages=_pages_text(site))
    images = [site.shots["desktop"], site.shots["phone"]] + [p.path for p in photos]
    raw = m.ask(prompt, images=images, schema=PROFILE_SCHEMA, effort="medium", max_tokens=12000)
    profile = json.loads(raw)
    n = len(photos)
    for prod in profile["products"]:
        if not 0 <= prod["photo"] < n:
            prod["photo"] = -1
    if not 0 <= profile["hero_photo"] < n:
        profile["hero_photo"] = -1
    return profile
