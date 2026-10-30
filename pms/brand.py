"""Muse Spark reads the business: the brand profile everything else is built from.

Spark gets the before screenshots, the best candidate photos (from the site, the
shop's full catalogue when it publishes one, and the product posts Spark found in
the owner's feeds) and the text of the pages, and returns one structured profile: who they are, what they sell (each
product matched to one of the photos), how they talk, what customers ask. The
prompt holds it to what the site says. Nothing invented: no prices, awards,
reviews or claims that aren't on the page, because these words go on a real
business's site.
"""

from __future__ import annotations

import io
import json
import re
from dataclasses import dataclass
from pathlib import Path

import requests
from PIL import Image as PILImage

from muse import client as m

from .crawl import UA, Site, _allowed
from .text import tidy_all

MAX_PHOTOS = 10  # candidate photos from the rendered site
MAX_PER_PAGE = 3  # of those, from any one page
MAX_CATALOG_PHOTOS = 8  # more from the catalogue, products the pages didn't show
MAX_FEED_PHOTOS = 6  # product posts from the owner's feeds
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
            "type": "array", "description": "up to 8 products, services or offers they sell, covering their range",
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

Where each candidate photo comes from, and what we know about it:
{photo_notes}

Build the brand profile. Rules, because every word goes on a real business's site:
- Use only what the site, its catalogue and the owner's own posts show or say. Never invent \
prices, reviews, awards, numbers, locations or claims. Empty string or empty list when they don't say.
- Products: what they actually sell, chosen so that together they show their whole range \
(every kind of thing in the catalogue and the feed, not six of one kind). Prefer products with \
a clear photo. Match each to the candidate photo that shows it, or -1. A product seen only in \
the feed keeps its price '' unless its caption gives one. Prices from the catalogue are written \
the way the site writes prices.
- A post's caption is the owner's words about that product; a dated event in a caption is not \
a standing fact about the business.
- FAQs: questions a customer would ask, with answers taken from the site's text. Skip a \
question rather than guess its answer.
- Voice: how they sound now, so the makeover keeps it.

Colours seen in the rendered CSS, most used first: {colors}
Fonts: {fonts}
Social profiles linked: {socials}
{feeds}
The shop's catalogue (every product it publishes):
{catalog}

{pages}"""


@dataclass
class Photo:
    index: int
    url: str
    path: str
    alt: str
    width: int
    height: int
    source: str = "site"  # site | catalog | the feed's platform (instagram...)
    note: str = ""  # what we know about it: the catalogue entry, or the post and Spark's read of it


def _stem(url: str) -> str:
    """The file a CDN URL points at, without sizes or versions, to spot one photo twice."""
    name = re.sub(r"[?#].*$", "", url).rsplit("/", 1)[-1].lower()
    return re.sub(r"(_\d+x\d*|-\d+x\d+)(?=\.\w+$)", "", name)


def _fetch(url: str) -> PILImage.Image | None:
    if not _allowed(url):
        return None
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=15)
        r.raise_for_status()
        return PILImage.open(io.BytesIO(r.content)).convert("RGB")
    except Exception:
        return None


def download_photos(site: Site, out: Path, feed: list = (), limit: int = MAX_PHOTOS) -> list[Photo]:
    """Save the candidate photos locally as JPEG (the reshoot works from these): the site's
    biggest pictures, then catalogue products the pages didn't show, then the product posts
    from the owner's feeds (`feed`: sources.Post, already sorted by Spark)."""
    out.mkdir(parents=True, exist_ok=True)
    photos: list[Photo] = []

    def keep(im: PILImage.Image, url: str, alt: str, source: str, note: str) -> None:
        im.thumbnail((1600, 1600))
        path = out / f"{len(photos):02d}.jpg"
        im.save(path, "JPEG", quality=90)
        photos.append(Photo(len(photos), url, str(path), alt, im.width, im.height, source, note))

    per_page: dict[str, int] = {}
    for img in site.images:
        if len(photos) >= limit:
            break
        if per_page.get(img.page, 0) >= MAX_PER_PAGE:  # one product page's gallery shouldn't crowd out the range
            continue
        im = _fetch(img.url)
        if im:
            per_page[img.page] = per_page.get(img.page, 0) + 1
            keep(im, img.url, img.alt, "site", f"on the page {img.page}")
    seen = {_stem(p.url) for p in photos}
    added = 0
    for item in site.catalog:
        if added >= MAX_CATALOG_PHOTOS or not item["image"] or _stem(item["image"]) in seen:
            continue
        im = _fetch(item["image"])
        if im:
            seen.add(_stem(item["image"]))
            keep(im, item["image"], item["title"], "catalog", f"catalogue photo of \"{item['title']}\"")
            added += 1
    for post in list(feed)[:MAX_FEED_PHOTOS]:
        try:
            im = PILImage.open(post.image).convert("RGB")
        except Exception:
            continue
        what = "a product on its own" if post.kind == "product" else "a product being worn"
        note = f"{post.source} post{' from ' + post.date if post.date else ''}: {what}, " \
               f"\"{post.product}\" ({post.why})" + (f"; caption: \"{post.caption[:200]}\"" if post.caption else "")
        keep(im, post.url, post.product, post.source, note)
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


def _catalog_text(site: Site) -> str:
    if not site.catalog:
        return "none published"
    rows = []
    for c in site.catalog:
        price = c["price"] + (f" (was {c['compare_at']})" if c["compare_at"] and c["compare_at"] != c["price"] else "")
        rows.append(f"- {c['title']}" + (f" [{c['type']}]" if c["type"] else "") + f": {price}"
                    + ("" if c["available"] else ", sold out"))
    return "\n".join(rows)


def _feeds_text(feeds: list) -> str:
    """The owner's profiles (sources.Source) in a few lines: bio, followers, what they post."""
    lines = []
    for f in feeds:
        if f.status != "read":
            continue
        kinds: dict[str, int] = {}
        for p in f.posts:
            kinds[p.kind] = kinds.get(p.kind, 0) + 1
        lines.append(f"{f.name} @{f.handle}: " + (f"{f.followers} followers. " if f.followers else "")
                     + (f'Bio: "{f.bio}". ' if f.bio else "")
                     + "Recent posts: " + ", ".join(f"{n} {k.replace('_', ' ')}" for k, n in kinds.items()) + ".")
    return ("Their feeds:\n" + "\n".join(lines) + "\n") if lines else ""


def read_brand(site: Site, photos: list[Photo], feeds: list = ()) -> dict:
    notes = "\n".join(f"[{p.index}] {p.source}: {p.note}" for p in photos) or "none"
    prompt = PROMPT.format(last=max(len(photos) - 1, 0), colors=", ".join(site.colors),
                           fonts=", ".join(site.fonts), socials=", ".join(site.socials) or "none",
                           pages=_pages_text(site), photo_notes=notes, feeds=_feeds_text(feeds),
                           catalog=_catalog_text(site))
    images = [site.shots["desktop"], site.shots["phone"]] + [p.path for p in photos]
    raw = m.ask(prompt, images=images, schema=PROFILE_SCHEMA, effort="medium", max_tokens=12000)
    profile = json.loads(raw)
    n = len(photos)
    for prod in profile["products"]:
        if not 0 <= prod["photo"] < n:
            prod["photo"] = -1
    if not 0 <= profile["hero_photo"] < n:
        profile["hero_photo"] = -1
    return tidy_all(profile)
