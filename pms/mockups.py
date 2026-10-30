"""Sketches: the owner sees their own homepage in each look before choosing one.

For every direction on offer, Muse Wonder sketches the first screen and a bit of this
business's homepage on that template (its skill and screenshots in hand), with the
business's real copy and photos: the hero is their own photo reshot in the template's
photo brief (the preview), the rest are their original product photos. A real browser
screenshots it on desktop and phone, and that's the card the owner picks from.

Each sketch draws a variant, so two makeovers with the same inputs don't look the
same: which product leads, which of Spark's headlines, wide or tall hero crop, and one
small twist the template allows. The chosen sketch, variant and all, is the brief the
full build follows.
"""

from __future__ import annotations

import json
import random
import re
import shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image

from . import site, templates

TWISTS = [
    "the template exactly as captured",
    "lean a little harder on the accent colour: one band, link or button carries it",
    "more air: bigger margins, and one element fewer above the fold",
    "more confident type: the hero headline at the top of the template's size range",
    "the product row comes straight under the hero, before any story",
]

SKETCH_PROMPT = """You are sketching a homepage for "Pimp My Social", a show that makes over small \
businesses' websites. The owner will see this sketch as a thumbnail next to others and pick one, \
so it must be unmistakably the "{style}" look, modelled on {tname}, at that site's quality.

Build ONE complete HTML file (all CSS inline) with ONLY: the header (and any top bar the template \
has), the hero, and the first section below the hero. About one and a half screens tall. No \
footer, nothing else. {shot_note} Borrow {tname}'s DESIGN only: never its name, logo, photos or \
words, and never its menu labels ({tlabels}). Menu words come from what this business sells \
and has.

The template skill (the numbers are the spec):
{skill}

Palette (CSS variables, exactly): {palette}
Fonts (Google Fonts stand-ins): {fonts}. Link them: <link rel="stylesheet" href="{font_css}">

This sketch's variant:
- Hero image: {hero_img} ({hero_product}). Use it full strength; crop {crop}.
- Hero headline, word for word: "{headline}"
- Twist: {twist}

The business's name, set as the template sets its wordmark: "{name}"
Other copy you may use, word for word (JSON): {copy}
Products with their photos (name, price exactly as given, photo): {products}
Products WITHOUT a photo are listed in type only, never given another product's picture.
Only these image files exist. Never invent facts, offers, years or counts.
Text over a photo must read clearly at thumbnail size: if the photo is light or busy behind the words, add a soft gradient scrim or move the words to a calm area.

Reply with only the HTML document, starting with <!doctype html>."""


def leads(cards: list[dict], profile: dict, rng: random.Random) -> list[list[dict]]:
    """Two products per card, lead first, spread so neighbouring cards don't open on the same
    thing. Both get reshot in the card's look, so the sketch never shows a raw photo."""
    # Only products the studio will reshoot (it takes the first 4 with their own photo), so the
    # full build can lead with the same product the sketch did.
    with_photo, used = [], set()
    for p in profile["products"]:
        if p["photo"] >= 0 and p["photo"] not in used and len(with_photo) < 4:
            used.add(p["photo"])
            with_photo.append(p)
    if not with_photo:
        return [[] for _ in cards]
    order = with_photo[:]
    rng.shuffle(order)
    n = len(order)
    return [[order[k % n]] + ([order[(k + 1) % n]] if n > 1 else []) for k in range(len(cards))]


def variants(cards: list[dict], firsts: list[dict | None], copy: dict, rng: random.Random) -> list[dict]:
    """`firsts` are each card's lead product (or None)."""
    """One variant per card. Headlines and twists are dealt like cards from a shuffled deck,
    so neighbouring sketches differ and a repeat only comes once the deck runs out."""
    heads = [h for h in dict.fromkeys([copy["h1"], *copy.get("h1_options", [])]) if h]
    twists = TWISTS[:]
    rng.shuffle(heads)
    rng.shuffle(twists)
    return [{"hero_product": f["name"] if f else "", "hero_photo": f["photo"] if f else -1,
             "headline": heads[k % len(heads)], "crop": rng.choice(["wide", "tall"]),
             "twist": twists[k % len(twists)]} for k, f in enumerate(firsts)]


def _web(src: Path, dst: Path, side: int = 1400) -> tuple[int, int]:
    im = Image.open(src).convert("RGB")
    im.thumbnail((side, side))
    im.save(dst, "JPEG", quality=80)
    return im.size


def sketch(card: dict, profile: dict, copy: dict, out: Path) -> dict:
    """One sketch: HTML, desktop thumbnail and phone shot. Returns paths."""
    v, t = card["variant"], templates.load(card["id"])
    shutil.rmtree(out, ignore_errors=True)
    (out / "img").mkdir(parents=True)
    # Only photos reshot in this look: the owner's raw photos never appear in a sketch.
    shot = {x["product"]: Path(x["path"]) for x in card.get("reshoots", []) if x.get("path")}
    hero_img = ""
    if v["hero_product"] in shot and shot[v["hero_product"]].exists():
        w, h = _web(shot[v["hero_product"]], out / "img" / "hero.jpg")
        hero_img = f"img/hero.jpg ({w}x{h})"
    prods = []
    for k, p in enumerate(profile["products"]):
        row = {"name": p["name"], "price": p["price"]}
        if p["name"] == v["hero_product"] and hero_img:
            row["photo"] = hero_img
        elif p["name"] in shot and shot[p["name"]].exists():
            w, h = _web(shot[p["name"]], out / "img" / f"p{k}.jpg", 900)
            row["photo"] = f"img/p{k}.jpg ({w}x{h})"
        prods.append(row)
    prompt = SKETCH_PROMPT.format(
        style=t["style"], tname=t["name"], shot_note=site._shot_note(t),
        tlabels=", ".join(site.template_labels(t["id"])) or "none on file", skill=t["skill"],
        palette=json.dumps(card["palette"]), fonts=json.dumps(card["fonts"]), font_css=card["font_css"],
        hero_img=hero_img or "none (set the hero in type and colour)", hero_product=v["hero_product"],
        crop=v["crop"], headline=v["headline"], twist=v["twist"], name=profile["name"],
        copy=json.dumps({k: copy[k] for k in ("kicker", "subhead", "cta", "about")}),
        products=json.dumps(prods))
    page = site._wonder(prompt, templates.shots(t["id"]), effort="low")
    # The same code checks the full build gets, plus a measured headline contrast, with one
    # chance to fix.
    (out / "index.html").write_text(page)
    shots = site.snapshot_screens(out / "index.html", out)
    problems = _problems(page, out, t["id"], profile, copy)
    if problems:
        try:
            fixed = site._wonder(prompt + "\n\nYour first sketch had these faults; fix them and change "
                                 "nothing else:\n- " + "\n- ".join(problems) + "\n\nThat sketch:\n" + page,
                                 templates.shots(t["id"]), effort="low")
            (out / "index.html").write_text(fixed)
            shots = site.snapshot_screens(out / "index.html", out)
            page = fixed
        except Exception as e:
            print(f"sketch fix {card['id']} failed: {e!r}"[:300])
    return {"html": str(out / "index.html"), "desktop": str(shots[0]), "phone": str(shots[1]),
            "weak_contrast": _contrast(out), "faults": _problems(page, out, t["id"], profile, copy)}


def _contrast(out: Path) -> float | None:
    f = out / "contrast.txt"
    return float(f.read_text()) if f.exists() and f.read_text().strip() else None


def _problems(page: str, out: Path, tid: str, profile: dict, copy: dict) -> list[str]:
    found = []
    borrowed = site.borrowed_labels(page, tid, profile)
    if borrowed:
        found.append(f"menu labels from the template site, not this business: {', '.join(borrowed)}")
    invented = site.invented_numbers(page, profile, copy)
    if invented:
        found.append(f"years or counts this business never gave: {', '.join(invented)}")
    missing = sorted({s for s in re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', page, re.I)
                      if not s.startswith(("http", "data:")) and not (out / s).exists()})
    if missing:
        found.append(f"image paths that don't exist: {', '.join(missing)}")
    weak = _contrast(out)
    if weak is not None and weak > 0.5:
        found.append(f"the hero headline barely reads: {round(weak * 100)}% of what's behind it is under 3:1 "
                     "contrast with the text. Add a soft gradient scrim behind it, darken that part of "
                     "the photo, change the text colour, or move it to a calm area")
    return found


def sketches(cards: list[dict], profile: dict, copy: dict, out_dir: Path) -> list[dict | None]:
    """All the sketches at once (Wonder calls in parallel)."""
    def one(c: dict) -> dict | None:
        try:
            return sketch(c, profile, copy, out_dir / f"sketch_{c['id']}")
        except Exception as e:
            print(f"sketch {c['id']} failed: {e!r}"[:300])
            return None
    with ThreadPoolExecutor(max_workers=6) as pool:
        return list(pool.map(one, cards))
