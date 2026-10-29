"""The logo, pimped: their current logo is the reference, the new site gets a remake.

Spark reads what the logo is about (the motif people would recognise). Muse Image
redraws it as one clean flat mark in the direction's ink, with no lettering (image
models garble type; the name is set in the site's display font instead). Code keys
out the background so the mark sits on any section, in ink or reversed. Spark then
compares old and new: a remake that lost the original's idea is thrown away and the
site falls back to a typeset wordmark, never to the old logo.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import numpy as np
import requests
from PIL import Image

from muse import client as m

from .crawl import UA, _allowed

READ_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["readable", "motif", "keep", "letters"],
    "properties": {
        "readable": {"type": "boolean", "description": "false if this isn't really a logo or is unreadable"},
        "motif": {"type": "string", "description": "the core visual idea, one short phrase"},
        "keep": {"type": "string", "description": "what a redesign must keep for customers to recognise it"},
        "letters": {"type": "string", "description": "any single initial or numeral that is part of the mark itself (not the name text), else empty"},
    },
}

READ_PROMPT = """This is the current logo of {name}, a {category}. A designer will redraw it \
as a premium mark. Describe its core idea: the motif customers recognise, and what the \
redesign must keep. Ignore taglines and the business name set as text."""

CHECK_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["keeps_idea", "note"],
    "properties": {"keeps_idea": {"type": "boolean"},
                   "note": {"type": "string", "description": "one sentence to the owner on what changed"}},
}

CHECK_PROMPT = """Image 1 is {name}'s current logo. Image 2 is a redesigned mark. Does the \
redesign keep the original's core idea ({motif}) so a regular customer would recognise it? \
Lettering is intentionally removed; judge the mark. Be strict: a different motif fails."""

REDRAW = ("Redesign this logo as a premium, minimal brand mark, the way a top design studio would "
          "refine it for a {category}. Keep the core idea: {motif}. Must keep: {keep}. Redraw it "
          "with clean, confident, consistent strokes, balanced and precise, and a stroke weight that stays clear at 32 pixels tall. {letters}Remove all "
          "words, taglines and website addresses. One flat colour, {ink}, on a plain flat {bg} "
          "background. No gradients, no shadows, no outlines of a badge, no mockup, no texture. "
          "Centred with generous empty margin.")


def fetch(url: str | None, out: Path) -> Path | None:
    """Their current logo as a trimmed transparent PNG, or None."""
    if not url or not _allowed(url):
        return None
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=15)
        r.raise_for_status()
        im = Image.open(io.BytesIO(r.content)).convert("RGBA")
    except Exception:
        return None
    if im.width < 32 or im.height < 32:  # a favicon is too small to redraw from
        return None
    box = _content_box(im)
    if box:
        im = im.crop(box)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    return out


def _content_box(im: Image.Image) -> tuple[int, int, int, int] | None:
    """Bounds of everything that isn't transparent or near-white."""
    a = np.asarray(im).astype(int)
    ink = (a[..., 3] > 16) & (a[..., :3].min(axis=2) < 235)
    ys, xs = np.nonzero(ink)
    if not len(xs):
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _on_white(src: Path, out: Path) -> Path:
    im = Image.open(src).convert("RGBA")
    pad = max(im.size) // 4
    canvas = Image.new("RGBA", (im.width + 2 * pad, im.height + 2 * pad), "white")
    canvas.alpha_composite(im, (pad, pad))
    canvas.convert("RGB").save(out)
    return out


def _hex(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))  # type: ignore[return-value]


def key_out(src: Path, ink: str, out_dark: Path, out_light: Path, light: str) -> tuple[int, int]:
    """Background to transparent; the mark recoloured flat in ink (and a reversed copy)."""
    a = np.asarray(Image.open(src).convert("RGB")).astype(float)
    corners = np.concatenate([a[:8, :8].reshape(-1, 3), a[:8, -8:].reshape(-1, 3),
                              a[-8:, :8].reshape(-1, 3), a[-8:, -8:].reshape(-1, 3)])
    bg = np.median(corners, axis=0)
    dist = np.sqrt(((a - bg) ** 2).sum(axis=2))
    alpha = np.clip((dist - 30) / 90, 0, 1)  # soft edge: anti-aliasing survives
    ys, xs = np.nonzero(alpha > 0.2)
    if not len(xs):
        raise RuntimeError("the redraw came back blank")
    pad = 12
    y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, a.shape[0])
    x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, a.shape[1])
    alpha = alpha[y0:y1, x0:x1]
    for colour, path in ((ink, out_dark), (light, out_light)):
        rgba = np.zeros((*alpha.shape, 4), dtype=np.uint8)
        rgba[..., :3] = _hex(colour)
        rgba[..., 3] = (alpha * 255).astype(np.uint8)
        Image.fromarray(rgba, "RGBA").save(path)
    return int(x1 - x0), int(y1 - y0)


def remake(logo_url: str | None, profile: dict, direction: dict, out: Path) -> dict:
    """Returns {original, mark, mark_light, w, h, motif, note} or {original, mark: None, note}."""
    out.mkdir(parents=True, exist_ok=True)
    original = fetch(logo_url, out / "original.png")
    result: dict = {"original": str(original) if original else None, "mark": None,
                    "note": "No usable logo on the current site, so the name is set as a wordmark."}
    if not original:
        return result
    ref = _on_white(original, out / "original_on_white.png")
    read = json.loads(m.ask(READ_PROMPT.format(name=profile["name"], category=profile["category"]),
                            images=[ref], schema=READ_SCHEMA, effort="low"))
    if not read["readable"]:
        result["note"] = "The current logo couldn't be read, so the name is set as a wordmark."
        return result
    pal = direction["palette"]
    letters = (f"Keep the {read['letters']} as part of the mark. " if read["letters"].strip() else "")
    prompt = REDRAW.format(category=profile["category"], motif=read["motif"], keep=read["keep"],
                           letters=letters, ink=pal["ink"], bg=pal["bg"])
    try:
        raw = m.edit_image(ref, prompt, out / "redraw.png", size="1024x1024")
        w, h = key_out(raw, pal["ink"], out / "mark.png", out / "mark_light.png", pal["bg"])
    except Exception as e:
        print(f"logo redraw failed: {e!r}"[:300])
        result["note"] = "The redraw didn't come out clean, so the name is set as a wordmark."
        return result
    check = json.loads(m.ask(CHECK_PROMPT.format(name=profile["name"], motif=read["motif"]),
                             images=[ref, out / "redraw.png"], schema=CHECK_SCHEMA, effort="low"))
    result.update(motif=read["motif"], note=check["note"])
    if check["keeps_idea"]:
        result.update(mark=str(out / "mark.png"), mark_light=str(out / "mark_light.png"), w=w, h=h)
    else:
        result["note"] = ("The redraw lost the original's idea, so the name is set as a wordmark. "
                          + check["note"])
    return result
