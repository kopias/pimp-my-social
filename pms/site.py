"""The new website: Spark writes it, Muse Wonder builds it, code makes it findable.

- Copy (Muse Spark): headline, sections, product blurbs, search title and
  description, all held to the brand profile, so no invented claims.
- Design and code (Muse Wonder): one hand-built page in the chosen direction,
  from that copy and the reshot photos. Each direction is a template skill
  modelled on a real fashion site; Wonder gets the skill and the site's own
  screenshots. Wonder is the strongest coder in the Muse family, and a bespoke
  page is the part of a makeover people remember.
- The fidelity check (Muse Spark, eyes on): the built page is screenshotted on
  desktop and phone and judged against the template's screenshots and signature
  moves. Below the bar, Wonder revises from the list of differences.
- The findability layer (code, not a model, because it has to be right every
  time): meta and Open Graph tags, JSON-LD for the business, products and FAQs,
  robots.txt that welcomes search and AI crawlers, sitemap.xml, llms.txt, and
  WebMCP tools so browser agents can query the business directly.
"""

from __future__ import annotations

import html
import json
import re
import shutil
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image

from muse import client as m

from . import inspo, templates
from .audit import AI_BOTS
from .photos import Shot
from .text import tidy_all

COPY_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["seo_title", "meta_description", "h1", "h1_options", "kicker", "subhead", "cta", "about",
                 "products", "proof_heading", "faq_heading", "visit", "share_title"],
    "properties": {
        "seo_title": {"type": "string", "description": "40-60 chars: what + where/who + name"},
        "meta_description": {"type": "string", "description": "120-160 chars, specific"},
        "h1": {"type": "string", "description": "the hero headline, punchy, under 9 words"},
        "h1_options": {"type": "array", "items": {"type": "string"},
                       "description": "3 more hero headlines, each a different angle, same rules"},
        "kicker": {"type": "string", "description": "2-5 word label above the headline"},
        "subhead": {"type": "string", "description": "one or two sentences under the headline"},
        "cta": {"type": "object", "additionalProperties": False, "required": ["label", "kind"],
                "properties": {"label": {"type": "string"},
                               "kind": {"type": "string", "enum": ["call", "visit", "order", "email"]}}},
        "about": {"type": "object", "additionalProperties": False, "required": ["heading", "body"],
                  "properties": {"heading": {"type": "string"},
                                 "body": {"type": "string", "description": "2 short paragraphs, \\n\\n between"}}},
        "products": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["name", "blurb", "price", "alt"],
            "properties": {"name": {"type": "string"}, "blurb": {"type": "string"},
                           "price": {"type": "string"},
                           "alt": {"type": "string", "description": "alt text for its photo"}}}},
        "proof_heading": {"type": "string"},
        "faq_heading": {"type": "string"},
        "visit": {"type": "object", "additionalProperties": False, "required": ["heading", "body"],
                  "properties": {"heading": {"type": "string"}, "body": {"type": "string"}}},
        "share_title": {"type": "string", "description": "Open Graph title, under 60 chars"},
    },
}

COPY_PROMPT = """You are the copywriter on a website makeover for a small business. Write the \
new homepage copy in the brand's own voice ({voice}), sharper and more inviting than before.

Keep their personality and warmth, but write at a professional editorial standard: at most \
one exclamation mark on the whole page, no doubled punctuation, no ALL CAPS, no "(NEW!)"-style \
asides. A good magazine editor's version of how they talk.

Rules: every fact must come from the brand profile below. Same products, same prices exactly \
as written, same hours. No invented awards, numbers, reviews, ingredients or promises. Keep \
product names. Write for people first, and make the title and description match what \
customers search for ({keywords}).

Brand profile: {profile}"""


def write_copy(profile: dict) -> dict:
    raw = m.ask(COPY_PROMPT.format(voice=", ".join(profile["voice"]["adjectives"]),
                                   keywords="; ".join(profile["keywords"][:8]),
                                   profile=json.dumps(profile)),
                schema=COPY_SCHEMA, effort="medium", max_tokens=8000)
    return tidy_all(json.loads(raw))


BUILD_PROMPT = """You are the master builder on "Pimp My Social", a show that makes over small \
businesses' websites. Design and code this business's new homepage as ONE complete HTML file \
with all CSS inline in a <style> tag.

THE TEMPLATE. The owner picked the "{style}" direction, modelled on {tname} ({tsource}). Build \
this business's page ON that template, so anyone who knows {tname}'s site would recognise the \
design: the same header pattern, hero composition, type scale, casing and tracking, section \
order, product presentation and palette roles. {shot_note} Borrow the DESIGN only. Never use \
{tname}'s name, logo, photographs or copy: this business's own name, remade logo, photos and \
words go into the template's structure.

Here is the template skill. Treat the numbers as the spec and every signature move as required:
{skill}

Palette (CSS variables, exactly these values): {palette}
Fonts, already loaded from Google Fonts (the template's own faces are proprietary; these are \
the matched stand-ins): {fonts}

{approved}Where the anatomy calls for content the business doesn't have (a category row, a second \
campaign image, a founder's note), build it from the products, photos and copy given below, \
or leave that section out. Never invent facts to fill a slot.

Every word on the page is this business's. Navigation, category and section labels come from \
what it actually sells and has (its product types, About, Visit, FAQ, Contact). Never carry \
over the template site's own labels ({tlabels}) unless this business really has that thing. \
A product without a photo is listed in type (name and price) or left out of image grids; \
never fake an image tile with big lettering.

TYPOGRAPHY DETAIL, where the template is silent (the template's measured type always wins):
{typography}

LOGO. {logo}

Use EXACTLY this copy, word for word (JSON): {copy}

Testimonials to show if any (verbatim): {proof}
FAQs (verbatim; render as <details><summary> items): {faqs}
Contact: {contact}

Images, already in the site folder (use these paths; set width and height attributes; \
loading="lazy" on all but the hero). Each product has a wide and a tall crop; use whichever \
the template's layout needs. These are the ONLY image files; never reference any other path:
{images}

Hard requirements:
- Semantic HTML5: <header>, <main>, <section>s with headings, <footer>. Exactly one <h1>.
- Every <img> has the alt text given. Mobile-first and responsive down to 360px wide.
- In <head>, put the marker <!--PMS:HEAD--> where meta tags will be injected. Do NOT write \
<title>, meta description, Open Graph tags or JSON-LD yourself.
- Put <!--PMS:BODY_END--> right before </body>.
- Link the fonts: <link rel="stylesheet" href="{font_css}">
- No JavaScript, no external images, no frameworks, no lorem ipsum, no placeholder text. \
CSS animation is fine (respect prefers-reduced-motion).
- Never add facts that aren't given: no star ratings, review counts, awards, badges, \
"best in town" claims, prices, discounts or dates beyond the copy. Testimonials are shown as \
quotes only. Announcement bars carry real facts from the copy or contact (hours, location, \
how to order), never an invented offer.
- Text over a photo must read clearly: if the photo is light or busy behind the words, add a soft \
gradient scrim or move the words to a calm area of the image.
- A fixed or sticky header that sits transparent over the hero must stay legible over every \
later section: give it the page background and ink colours once it leaves the hero (a CSS \
scroll-driven animation or a solid header below the hero; no JavaScript).
- A footer with the business name, contact, hours, and the social links: {socials}.

Reply with only the HTML document, starting with <!doctype html>."""

REVISE_PROMPT = """You built this page on the "{style}" template (modelled on {tname}). A side-by-side \
check against the template found these differences. Fix every one, keep everything that already \
matches, never delete a section the template's anatomy calls for (fixes add or adjust), keep all \
copy, images, alt text, real prices, markers (<!--PMS:HEAD-->, <!--PMS:BODY_END-->) and the \
hard requirements from the original brief.

Differences to fix:
{fixes}

{shots_note}

The template skill again:
{skill}

The current page:
{page}

Reply with only the full corrected HTML document, starting with <!doctype html>."""


def logo_brief(mark: dict | None, name: str) -> str:
    if not mark:
        return (f"There is no logo file. Set the name \"{name}\" as a wordmark in the display "
                "font, in the header and footer, styled the way the template sets its wordmark.")
    return (f"The business's remade logo mark is img/logo.png ({mark['w']}x{mark['h']}, ink on "
            "transparent) with a reversed copy img/logo-light.png for dark sections and for use over "
            f"photos. Use the mark in the header beside the name \"{name}\" set the way the template "
            "sets its wordmark (the mark has no lettering of its own), 28 to 48px tall, with clear "
            "space; repeat it larger in the footer. Never put it in a box or pill, never add a "
            "shadow, never redraw it in CSS.")


def _template(direction: dict) -> dict:
    return templates.load(direction["id"]) if direction.get("id") in templates.SOURCES else direction


def _shot_note(t: dict) -> str:
    n = len(templates.shots(t["id"]))
    if n == 3:
        return ("The first three attached screenshots are the template site itself: desktop first "
                "screen, desktop one scroll down, phone.")
    if n == 1:
        return "The attached screenshot is the template site on a phone (desktop blocks capture)."
    return "No screenshots of this template are on file; build from the skill."


def _wonder(prompt: str, images: list[Path], effort: str = "medium") -> str:
    raw = m.ask(prompt, images=images, model=m.AGENT_MODEL, effort=effort, max_tokens=32000)
    match = re.search(r"<!doctype html.*</html>", raw, re.S | re.I)
    if not match:
        raise RuntimeError("Wonder didn't return an HTML document")
    return match.group(0)


APPROVED = """THE OWNER'S CHOICE. The owner picked this look from a sketch of their homepage \
(the LAST attached image; its HTML is below). Keep what they saw: the same header, the same hero \
composition with the same headline ("{headline}") and lead product ({hero}), the same first \
section and the same twist ({twist}). Swap the sketch's photos for the studio photos listed \
below and the typed wordmark for the logo; then build the rest of the page in the same hand.
The sketch's HTML:
{html}

"""


def build_page(profile: dict, copy: dict, direction: dict, images: list[dict],
               font_css: str, mark: dict | None = None, approved: dict | None = None) -> str:
    t = _template(direction)
    shown = templates.shots(t["id"])
    approved_txt = ""
    if approved and Path(approved.get("html", "")).exists():
        v = approved.get("variant", {})
        approved_txt = APPROVED.format(headline=v.get("headline", copy["h1"]), hero=v.get("hero_product", ""),
                                       twist=v.get("twist", ""), html=Path(approved["html"]).read_text()[:40000])
        if Path(approved.get("desktop", "")).exists():
            shown = [*shown, Path(approved["desktop"])]
    img_lines = "\n".join(f"- {i['path']} ({i['w']}x{i['h']}): {i['what']}. alt: \"{i['alt']}\""
                          for i in images)
    prompt = BUILD_PROMPT.format(
        style=t.get("style", t["name"]), tname=t["name"], tsource=t.get("source", ""),
        shot_note=_shot_note(t), skill=t.get("skill", t.get("layout", "")),
        tlabels=", ".join(template_labels(t["id"])) or "none on file", approved=approved_txt,
        palette=json.dumps(direction["palette"]), fonts=json.dumps(direction["fonts"]),
        typography=inspo.typography(), logo=logo_brief(mark, profile["name"]),
        copy=json.dumps(copy), proof=json.dumps(profile["proof"]),
        faqs=json.dumps(profile["faqs"]), contact=json.dumps(profile["contact"]),
        images=img_lines, font_css=font_css, socials=json.dumps(profile.get("socials", {})),
    )
    return _wonder(prompt, shown)


# --- the fidelity check ----------------------------------------------------------

FIDELITY_ROUNDS = 2  # revisions after the first build, at most
GOOD_ENOUGH = 8

FIDELITY_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["scores", "overall", "signature", "fixes", "verdict"],
    "properties": {
        "scores": {"type": "object", "additionalProperties": False,
                   "required": ["header", "hero", "type", "palette", "sections", "products", "spacing",
                                "mobile", "polish"],
                   "properties": {k: {"type": "integer", "minimum": 0, "maximum": 10} for k in
                                  ["header", "hero", "type", "palette", "sections", "products", "spacing",
                                   "mobile", "polish"]}},
        "overall": {"type": "integer", "minimum": 0, "maximum": 10,
                    "description": "how recognisably the built page is the template, at the template's quality"},
        "signature": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["move", "present"],
            "properties": {"move": {"type": "string"}, "present": {"type": "boolean"}}}},
        "fixes": {"type": "array", "maxItems": 8, "items": {"type": "string"},
                  "description": "concrete changes, most important first, in CSS/HTML terms with sizes"},
        "verdict": {"type": "string", "description": "one sentence"},
    },
}

FIDELITY_PROMPT = """You are the design director checking a website makeover against the template \
it was built on: "{style}", modelled on {tname}. {order}

Judge how recognisably the built page IS this template, at the template's level of quality, \
with different content. Different photos, products, words and logo are expected and correct; \
never mark it down for those. Mark it down for: a different header pattern, hero composition or \
section order; wrong type scale, casing, weight or tracking; palette roles used differently; \
products presented differently; cramped or template-cheap spacing; anything broken (overlaps, \
unreadable text over photos, missing images, horizontal scroll on the phone). Words borrowed \
from the template site that this business doesn't have (its menu categories, collection names, \
offers) are a serious fault, not a match: cap overall at 5 and list them as fixes. So are fake \
image tiles made of big lettering, and a header whose words vanish against a later section.

The photographs are this business's own studio reshoots, the only images it has (often a \
garment without a model). Judge how they are cropped, sized and placed against the template, \
never what they show: never ask for a model, a portrait or new photography. Real prices, \
including a sale price beside a struck-through regular price, stay; never ask to remove them.

Score 0-10 each: header, hero, type, palette, sections, products, spacing, mobile, polish; then \
overall (10 = a {tname} designer would think it came from their studio). For each signature move \
below, say whether it is present. Then list the fixes, most important first, specific enough \
to code ("hero headline is 40px bold sans; make it 90px Cormorant Garamond 300, two lines, \
left-aligned at 7%").

Signature moves:
{signature}

Template skill, for the numbers:
{skill}"""


# Labels any shop's header has; a template's other menu words are its own business.
GENERIC_LABELS = {"search", "account", "bag", "cart", "log in", "login", "sign in", "menu", "wishlist",
                  "shop", "shop all", "new", "new in", "new arrivals", "about", "about us", "contact",
                  "contact us", "home", "stores", "help", "en", "close", "sale", "skip to content",
                  "skip to main content", "info", "collections", "my cart", "the brand", "stories", "english", "language",
                  "our story", "story", "journal", "visit", "faq", "gifts", "all"}


def template_labels(tid: str) -> list[str]:
    """The template site's own menu words, from its measured capture."""
    f = templates.ROOT / tid / "measured.json"
    if not f.exists():
        return []
    meas = json.loads(f.read_text())
    out = []
    for k in ("desktop", "mobile"):
        for lab in (meas.get(k) or {}).get("nav_labels", []):
            lab = re.sub(r"\s+", " ", lab).strip()
            low = lab.lower()
            if (2 < len(lab) <= 24 and re.fullmatch(r"[\w&'’ .-]+", lab) and low not in GENERIC_LABELS
                    and not re.search(r"\d|\$|£|€|usd|\(", low) and lab not in out):
                out.append(lab)
    return out


def borrowed_labels(page: str, tid: str, profile: dict) -> list[str]:
    """Template menu words that turned up in the page's header but mean nothing for this
    business (Mango's TEEN and KIDS on a shop that sells neither)."""
    head = " ".join(re.findall(r"<(?:header|nav)\b.*?</(?:header|nav)>", page, re.S | re.I))
    text = " " + re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", head)).lower() + " "
    known = json.dumps(profile, ensure_ascii=False).lower()
    return [lab for lab in template_labels(tid)
            if re.search(r"[^\w]" + re.escape(lab.lower()) + r"[^\w]", text) and lab.lower() not in known]


def swapped_photos(page: str, images: list[dict], products: list[str] = ()) -> list[str]:
    """A product shown with another product's photo (the jacket's tile using the shirt's
    picture because the jacket has none). Read from each <img>: its file says which product
    the photo is; its alt says which product the page claims it is."""
    owner = {i["path"]: i.get("product") for i in images if i.get("product")}
    names = {i["product"] for i in images if i.get("product")} | set(products)  # incl. ones with no photo
    out = []
    for tag in re.findall(r"<img\b[^>]*>", page, re.I):
        src = re.search(r'\bsrc="([^"]+)"', tag)
        alt = re.search(r'\balt="([^"]*)"', tag)
        if not src or not alt or src.group(1) not in owner:
            continue
        real, said = owner[src.group(1)], html.unescape(alt.group(1)).lower()
        if real.lower() not in said:
            out += [f"{n} shown with the photo of {real}" for n in names if n != real and n.lower() in said]
    return sorted(set(out))


def invented_numbers(page: str, *sources: dict) -> list[str]:
    """Years and "100+"-style counts in the page's visible text that appear nowhere in what
    the business gave us: the classic way a template example ("since 1984") leaks in."""
    body = re.sub(r"<(script|style)\b.*?</\1>", " ", page, flags=re.S | re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", body))
    known = " ".join(json.dumps(x, ensure_ascii=False) for x in sources)
    found = re.findall(r"\b(?:19|20)\d\d\b|\b\d[\d,]*\+", text)
    return sorted({n for n in found if n.rstrip("+") not in known})


def _lum(rgb: tuple) -> float:
    c = [v / 255 for v in rgb[:3]]
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


HEADLINE_JS = """() => { const h = document.querySelector('h1'); if (!h) return null;
  const r = h.getBoundingClientRect(); const m = getComputedStyle(h).color.match(/[\\d.]+/g).map(Number);
  return {x: r.left, y: r.top, w: r.width, h: r.height, rgb: m.slice(0, 3)}; }"""


def headline_contrast(shot: Path, box: dict | None) -> float | None:
    """How much of what sits behind the hero headline is too close to the text's colour to
    read (WCAG 3:1, the large-text floor): the share of background pixels under 3:1, 0 to 1.
    Letters are the pixels (nearly) exactly the text's colour and are left out. Measured, not judged."""
    if not box or box["w"] < 4 or box["h"] < 4:
        return None
    im = Image.open(shot).convert("RGB")
    x0, y0 = max(0, int(box["x"])), max(0, int(box["y"]))
    x1, y1 = min(im.width, int(box["x"] + box["w"])), min(im.height, int(box["y"] + box["h"]))
    if x1 - x0 < 4 or y1 - y0 < 4:
        return None
    rgb = tuple(box["rgb"])
    t = _lum(rgb)
    # letters = pixels (nearly) exactly the text colour; everything else is what they sit on
    ground = [q for q in im.crop((x0, y0, x1, y1)).resize((80, 24), Image.NEAREST).get_flattened_data()
              if sum((a - b) ** 2 for a, b in zip(q, rgb)) > 12 ** 2]
    if not ground:
        return None
    weak = sum((max(t, _lum(q)) + 0.05) / (min(t, _lum(q)) + 0.05) < 3 for q in ground)
    return round(weak / len(ground), 2)


def snapshot_screens(page: Path, out_dir: Path) -> list[Path]:
    """Just the first screen on desktop and on a phone: a sketch's thumbnail. Also measures
    the hero headline's contrast on desktop (written to contrast.txt beside the shots)."""
    from playwright.sync_api import sync_playwright
    shots = [out_dir / "desktop.jpg", out_dir / "phone.jpg"]
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        for path, vp, mobile in ((shots[0], {"width": 1440, "height": 900}, False),
                                 (shots[1], {"width": 390, "height": 844}, True)):
            ctx = b.new_context(viewport=vp, is_mobile=mobile, has_touch=mobile,
                                device_scale_factor=2 if mobile else 1)
            pg = ctx.new_page()
            pg.goto(page.resolve().as_uri(), wait_until="load", timeout=60_000)
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(500)
            pg.screenshot(path=path, quality=78)
            if not mobile:
                ratio = headline_contrast(path, pg.evaluate(HEADLINE_JS))
                (out_dir / "contrast.txt").write_text("" if ratio is None else str(ratio))
            ctx.close()
        b.close()
    return shots


def snapshot(page: Path, out_dir: Path, tag: str) -> list[Path]:
    """The built page as a visitor sees it: the desktop first screen, the whole desktop page
    top to bottom (so the check sees every section, not just two screens), and a phone."""
    from playwright.sync_api import sync_playwright
    out_dir.mkdir(parents=True, exist_ok=True)
    shots = []
    with sync_playwright() as p:
        b = p.chromium.launch(channel="chrome")
        for name, vp, mobile in (("desktop", {"width": 1440, "height": 900}, False),
                                 ("mobile", {"width": 390, "height": 844}, True)):
            ctx = b.new_context(viewport=vp, is_mobile=mobile, has_touch=mobile,
                                device_scale_factor=2 if mobile else 1)
            pg = ctx.new_page()
            pg.goto(page.resolve().as_uri(), wait_until="load", timeout=60_000)
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(600)
            if mobile:
                shots.append(out_dir / f"{tag}_mobile.jpg")
                pg.screenshot(path=shots[-1], quality=70)
            else:
                shots.append(out_dir / f"{tag}_desktop_1.jpg")
                pg.screenshot(path=shots[-1], quality=72)
                # lazy images load as they scroll in; walk the page once first
                pg.evaluate("""async () => { for (let y = 0; y < document.body.scrollHeight; y += 700) {
                  scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); } scrollTo(0, 0); }""")
                pg.wait_for_timeout(500)
                full = out_dir / f"{tag}_desktop_full.png"
                pg.screenshot(path=full, full_page=True)
                im = Image.open(full).convert("RGB")
                im = im.resize((960, round(im.height * 960 / im.width)))
                shots.append(out_dir / f"{tag}_desktop_full.jpg")
                im.crop((0, 0, 960, min(im.height, 7200))).save(shots[-1], quality=70)
                full.unlink()
            ctx.close()
        b.close()
    return shots


def fidelity(direction: dict, built_shots: list[Path]) -> dict:
    t = _template(direction)
    ref = templates.shots(t["id"])
    names = {"desktop_1.jpg": "desktop first screen", "desktop_2.jpg": "desktop one scroll down",
             "mobile_1.jpg": "phone"}
    if ref:
        order = (f"Images 1-{len(ref)} are the TEMPLATE site ({', '.join(names[p.name] for p in ref)}). "
                 f"Images {len(ref) + 1}-{len(ref) + 3} are the BUILT page (desktop first screen, the WHOLE "
                 "desktop page top to bottom, phone). The template shots only show its first two screens; "
                 "judge lower sections against the skill's anatomy.")
    else:
        order = ("No screenshots of the template are on file; judge from the skill. The images are the "
                 "BUILT page (desktop first screen, the WHOLE desktop page top to bottom, phone).")
    raw = m.ask(FIDELITY_PROMPT.format(style=t.get("style", t["name"]), tname=t["name"], order=order,
                                       signature="\n".join(f"- {x}" for x in t.get("signature", [])),
                                       skill=t.get("skill", "")),
                images=[*ref, *built_shots], schema=FIDELITY_SCHEMA, effort="medium", max_tokens=6000)
    return json.loads(raw)


def revise(direction: dict, page: str, fixes: list[str], built_shots: list[Path]) -> str:
    t = _template(direction)
    ref = templates.shots(t["id"])
    note = (f"Attached: the template ({len(ref)} screenshots) then your current page (desktop first "
            "screen, the whole desktop page, phone)." if ref else
            "Attached: your current page (desktop first screen, the whole desktop page, phone).")
    prompt = REVISE_PROMPT.format(style=t.get("style", t["name"]), tname=t["name"],
                                  fixes="\n".join(f"{i + 1}. {f}" for i, f in enumerate(fixes)),
                                  shots_note=note, skill=t.get("skill", ""), page=page)
    return _wonder(prompt, [*ref, *built_shots])


# --- the findability layer -----------------------------------------------------


def _abs(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")


def jsonld(profile: dict, copy: dict, base: str, images: list[dict], logo: str | None) -> list[dict]:
    c = profile["contact"]
    biz: dict = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness" if c.get("address") else "Organization",
        "@id": base + "#business", "name": profile["name"], "url": base,
        "description": copy["meta_description"],
    }
    hero = next((i for i in images if i["role"] == "hero"), images[0] if images else None)
    if hero:
        biz["image"] = _abs(base, hero["path"])
    if logo:
        biz["logo"] = logo
    if c.get("address"):
        biz["address"] = {"@type": "PostalAddress", "streetAddress": c["address"]}
    if c.get("phone"):
        biz["telephone"] = c["phone"]
    if c.get("email"):
        biz["email"] = c["email"]
    if c.get("hours"):
        biz["openingHours"] = c["hours"]
    if profile.get("socials"):
        biz["sameAs"] = list(profile["socials"].values())
    out = [biz]
    by_name = {i.get("product"): i for i in images}
    for p in profile["products"]:
        item: dict = {"@context": "https://schema.org", "@type": "Product", "name": p["name"],
                      "description": p["description"], "brand": {"@id": base + "#business"}}
        if p["name"] in by_name:
            item["image"] = _abs(base, by_name[p["name"]]["path"])
        price = re.search(r"\$\s?(\d+(?:\.\d{2})?)", p["price"] or "")
        if price:
            item["offers"] = {"@type": "Offer", "price": price.group(1), "priceCurrency": "USD",
                              "availability": "https://schema.org/InStock", "url": base}
        out.append(item)
    if profile["faqs"]:
        out.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": f["q"],
             "acceptedAnswer": {"@type": "Answer", "text": f["a"]}} for f in profile["faqs"]]})
    return out


def head_tags(profile: dict, copy: dict, base: str, images: list[dict], logo: str | None) -> str:
    e = html.escape
    share = next((i for i in images if i["role"] == "share"), None)
    tags = [
        f"<title>{e(copy['seo_title'])}</title>",
        f'<meta name="description" content="{e(copy["meta_description"])}">',
        '<meta name="viewport" content="width=device-width, initial-scale=1">',
        f'<link rel="canonical" href="{e(base)}">',
        '<meta name="robots" content="index, follow, max-image-preview:large">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:site_name" content="{e(profile["name"])}">',
        f'<meta property="og:title" content="{e(copy["share_title"])}">',
        f'<meta property="og:description" content="{e(copy["meta_description"])}">',
        f'<meta property="og:url" content="{e(base)}">',
        '<meta name="twitter:card" content="summary_large_image">',
        '<link rel="alternate" type="text/plain" href="/llms.txt" title="llms.txt">',
    ]
    if share:
        tags.append(f'<meta property="og:image" content="{e(_abs(base, share["path"]))}">')
        tags.append(f'<meta property="og:image:width" content="{share["w"]}">')
        tags.append(f'<meta property="og:image:height" content="{share["h"]}">')
    for block in jsonld(profile, copy, base, images, logo):
        tags.append('<script type="application/ld+json">'
                    + json.dumps(block, ensure_ascii=False).replace("</", "<\\/") + "</script>")
    return "\n".join(tags)


def robots_txt(base: str) -> str:
    lines = ["# Search engines and AI assistants are welcome here.", ""]
    for bot in AI_BOTS:
        lines += [f"User-agent: {bot}", "Allow: /", ""]
    lines += ["User-agent: *", "Allow: /", "", f"Sitemap: {_abs(base, 'sitemap.xml')}", ""]
    return "\n".join(lines)


def sitemap_xml(base: str) -> str:
    today = date.today().isoformat()
    urls = [base, _abs(base, "llms.txt")]
    body = "".join(f"<url><loc>{html.escape(u)}</loc><lastmod>{today}</lastmod></url>" for u in urls)
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{body}</urlset>\n'


def llms_txt(profile: dict, copy: dict, base: str) -> str:
    c = profile["contact"]
    lines = [f"# {profile['name']}", "", f"> {profile['one_liner']}", ""]
    facts = [("What", profile["category"]), ("For", profile["audience"]),
             ("Where", c.get("address") or profile.get("location")), ("Phone", c.get("phone")),
             ("Email", c.get("email")), ("Order", c.get("order_url"))]
    lines += [f"- {k}: {v}" for k, v in facts if v]
    if c.get("hours"):
        lines += ["", "## Hours", ""] + [f"- {h}" for h in c["hours"]]
    lines += ["", "## Products", ""]
    lines += [f"- {p['name']}" + (f" ({p['price']})" if p["price"] else "") + f": {p['description']}"
              for p in profile["products"]]
    if profile["faqs"]:
        lines += ["", "## Questions customers ask", ""]
        for f in profile["faqs"]:
            lines += [f"### {f['q']}", "", f["a"], ""]
    lines += ["", "## For AI agents", "",
              f"- Homepage: {base}",
              "- This site registers WebMCP tools (list_products, get_product, "
              "get_business_info, find_answer, how_to_order) on document.modelContext.", ""]
    return "\n".join(lines)


# WebMCP: typed tools a browser agent can call instead of scraping the page. The
# data comes from an inline JSON block, so the tools always match the page.
WEBMCP_JS = r"""
(() => {
  const data = JSON.parse(document.getElementById('pms-data').textContent);
  const text = (v) => ({ content: [{ type: 'text', text: typeof v === 'string' ? v : JSON.stringify(v, null, 2) }] });
  const norm = (s) => String(s || '').toLowerCase();
  const tools = [
    { name: 'list_products', description: `Everything ${data.name} sells, with prices as listed.`,
      inputSchema: { type: 'object', properties: {} },
      annotations: { readOnlyHint: true },
      execute: () => text(data.products.map(({ name, price, description }) => ({ name, price, description }))) },
    { name: 'get_product', description: 'Details for one product by name (partial names work).',
      inputSchema: { type: 'object', properties: { name: { type: 'string' } }, required: ['name'] },
      annotations: { readOnlyHint: true },
      execute: ({ name }) => {
        const p = data.products.find((x) => norm(x.name).includes(norm(name)));
        return p ? text(p) : { ...text(`No product matching "${name}". Try list_products.`), isError: true };
      } },
    { name: 'get_business_info', description: `Address, phone, email, opening hours and links for ${data.name}.`,
      inputSchema: { type: 'object', properties: {} },
      annotations: { readOnlyHint: true },
      execute: () => text({ name: data.name, about: data.about, ...data.contact, socials: data.socials }) },
    { name: 'find_answer', description: 'Answer a customer question from the business\'s own FAQ.',
      inputSchema: { type: 'object', properties: { question: { type: 'string' } }, required: ['question'] },
      annotations: { readOnlyHint: true },
      execute: ({ question }) => {
        const words = norm(question).split(/\W+/).filter((w) => w.length > 3);
        const ranked = data.faqs.map((f) => [words.filter((w) => norm(f.q + ' ' + f.a).includes(w)).length, f])
          .sort((a, b) => b[0] - a[0]);
        return ranked.length && ranked[0][0] ? text(ranked[0][1])
          : text('No answer on file. Use get_business_info to contact the business.');
      } },
    { name: 'how_to_order', description: 'How a customer can buy, order or book, and how to reach the business.',
      inputSchema: { type: 'object', properties: {} },
      annotations: { readOnlyHint: true },
      execute: () => text({ order: data.contact.order_url || null, phone: data.contact.phone || null,
                            email: data.contact.email || null, address: data.contact.address || null }) },
  ];
  // The standard is document.modelContext; some early builds used navigator. Both, if present.
  const ctx = document.modelContext || navigator.modelContext;
  if (ctx && ctx.registerTool) for (const t of tools) { try { ctx.registerTool(t); } catch (e) { console.warn('WebMCP', t.name, e); } }
  // Until browsers ship WebMCP, agents and tests can reach the same tools here.
  window.webmcp = { tools: tools.map(({ name, description, inputSchema }) => ({ name, description, inputSchema })),
                    call: (name, args = {}) => tools.find((t) => t.name === name).execute(args) };
})();
"""


def body_end(profile: dict, copy: dict) -> str:
    data = {"name": profile["name"], "about": profile["one_liner"], "contact": profile["contact"],
            "socials": profile.get("socials", {}),
            "products": [{k: p[k] for k in ("name", "price", "description")} for p in profile["products"]],
            "faqs": profile["faqs"]}
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return (f'<script type="application/json" id="pms-data">{blob}</script>\n'
            f"<script>{WEBMCP_JS}</script>")


def enforce(page: str, images: list[dict]) -> str:
    """Hold Wonder's page to the rules the audit checks: one H1, alt on every image,
    lang set. Fix rather than fail."""
    page = re.sub(r"<html(?![^>]*\blang=)", '<html lang="en"', page, count=1, flags=re.I)
    h1s = list(re.finditer(r"<h1\b", page, re.I))
    for mt in reversed(h1s[1:]):  # demote extra H1s
        end = page.find("</h1>", mt.end())
        page = page[:end] + "</h2>" + page[end + 5:]
        page = page[:mt.start()] + "<h2" + page[mt.start() + 3:]
    alts = {i["path"]: i["alt"] for i in images}

    def fix_img(mt: re.Match) -> str:
        tag = mt.group(0)
        if re.search(r'\balt="[^"]+', tag):
            return tag
        src = re.search(r'src="([^"]+)"', tag)
        alt = html.escape(alts.get(src.group(1), "") if src else "")
        tag = re.sub(r'\salt="[^"]*"', "", tag)
        return tag.replace("<img", f'<img alt="{alt}"', 1)
    return re.sub(r"<img\b[^>]*>", fix_img, page, flags=re.I)


def inject(page: str, head: str, end: str) -> str:
    page = page.replace("<!--PMS:HEAD-->", head) if "<!--PMS:HEAD-->" in page else \
        re.sub(r"</head>", head + "\n</head>", page, count=1, flags=re.I)
    page = page.replace("<!--PMS:BODY_END-->", end) if "<!--PMS:BODY_END-->" in page else \
        re.sub(r"</body>", end + "\n</body>", page, count=1, flags=re.I)
    return page


def _web_jpeg(src: Path, dst: Path, max_side: int) -> tuple[int, int]:
    im = Image.open(src).convert("RGB")
    im.thumbnail((max_side, max_side))
    im.save(dst, "JPEG", quality=82, optimize=True, progressive=True)
    return im.size


def build(profile: dict, direction: dict, shots: list[Shot], base_url: str, out: Path,
          mark: dict | None = None, copy: dict | None = None, approved: dict | None = None) -> dict:
    """The whole site folder. Returns paths and timings for the report."""
    out.mkdir(parents=True, exist_ok=True)
    (out / "img").mkdir(exist_ok=True)
    base = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}/"
    copy = copy or write_copy(profile)
    alts = {p["name"]: p["alt"] for p in copy["products"]}
    images: list[dict] = []
    for k, s in enumerate(shots):
        stem = re.sub(r"[^a-z0-9]+", "-", s.product.lower()).strip("-")
        w, h = _web_jpeg(Path(s.landscape), out / "img" / f"{stem}.jpg", 1600)
        images.append({"path": f"img/{stem}.jpg", "w": w, "h": h, "product": s.product,
                       "what": f"professional photo of {s.product}, wide crop",
                       "alt": alts.get(s.product) or s.product, "role": "hero" if k == 0 else "product"})
        if s.portrait and Path(s.portrait).exists():
            w, h = _web_jpeg(Path(s.portrait), out / "img" / f"{stem}-tall.jpg", 1600)
            images.append({"path": f"img/{stem}-tall.jpg", "w": w, "h": h, "product": s.product,
                           "what": f"professional photo of {s.product}, tall crop",
                           "alt": alts.get(s.product) or s.product, "role": "tall"})
    if images:  # a 1200x630 share card from the hero
        im = Image.open(out / images[0]["path"])
        r = max(1200 / im.width, 630 / im.height)
        im = im.resize((round(im.width * r), round(im.height * r)))
        left, top = (im.width - 1200) // 2, (im.height - 630) // 2
        im.crop((left, top, left + 1200, top + 630)).save(out / "img" / "share.jpg", quality=85)
        images.append({"path": "img/share.jpg", "w": 1200, "h": 630, "role": "share",
                       "what": "share image", "alt": profile["name"]})
    logo = None
    if mark:  # the remade logo, never the old one
        shutil.copy(mark["mark"], out / "img" / "logo.png")
        shutil.copy(mark["mark_light"], out / "img" / "logo-light.png")
        logo = _abs(base, "img/logo.png")
    page_imgs = [i for i in images if i["role"] != "share"]
    logos = [{"path": "img/logo.png", "alt": profile["name"]},
             {"path": "img/logo-light.png", "alt": profile["name"]}]
    page = enforce(build_page(profile, copy, direction, page_imgs, direction["font_css"], mark, approved),
                   page_imgs + logos)
    # Hold it to the template: screenshot, compare, revise, keep the best.
    checks, best = [], None
    for r in range(FIDELITY_ROUNDS + 1):
        (out / "index.html").write_text(page)
        try:
            shots_r = snapshot(out / "index.html", out / "_fidelity", f"r{r}")
            fid = fidelity(direction, shots_r)
        except Exception as e:  # the check must never sink the build
            print(f"fidelity check failed: {e!r}"[:300])
            best = best or (page, None)
            break
        borrowed = borrowed_labels(page, direction.get("id", ""), profile)
        if borrowed:  # caught in code, so it never depends on the reviewer noticing
            fid["borrowed"] = borrowed
            fid["overall"] = min(fid["overall"], 5)
            fid["fixes"] = [f"Remove the template site's own menu labels {', '.join(borrowed)}: this business "
                            "doesn't sell or have those. Use its real product types and pages."] + fid["fixes"]
        missing = sorted({src for src in re.findall(r'<img\b[^>]*\bsrc="([^"]+)"', page, re.I)
                          if not src.startswith(("http", "data:")) and not (out / src).exists()})
        if missing:
            fid["missing_images"] = missing
            fid["overall"] = min(fid["overall"], 6)
            fid["fixes"] = [f"These image paths don't exist: {', '.join(missing)}. Use only the listed "
                            "image files."] + fid["fixes"]
        swapped = swapped_photos(page, page_imgs, [p["name"] for p in profile["products"]])
        if swapped:
            fid["swapped_photos"] = swapped
            fid["overall"] = min(fid["overall"], 5)
            fid["fixes"] = ["Never show a product with another product's photo (" + "; ".join(swapped) + "). "
                            "Products without their own photo are listed in type only."] + fid["fixes"]
        invented = invented_numbers(page, profile, copy)
        if invented:
            fid["invented"] = invented
            fid["overall"] = min(fid["overall"], 5)
            fid["fixes"] = [f"Remove {', '.join(invented)}: no such year or number appears in this business's "
                            "facts. Never invent dates or counts."] + fid["fixes"]
        checks.append({"round": r, **fid, "shots": [str(p) for p in shots_r]})
        if best is None or best[1] is None or fid["overall"] > best[1]["overall"]:
            best = (page, fid)
        if fid["overall"] >= GOOD_ENOUGH or r == FIDELITY_ROUNDS:
            break
        try:
            page = enforce(revise(direction, page, fid["fixes"], shots_r), page_imgs + logos)
        except Exception as e:
            print(f"revision failed: {e!r}"[:300])
            break
    page = best[0]
    (out / "fidelity.json").write_text(json.dumps(checks, indent=1))
    page = inject(page, head_tags(profile, copy, base, images, logo), body_end(profile, copy))
    (out / "index.html").write_text(page)
    (out / "robots.txt").write_text(robots_txt(base))
    (out / "sitemap.xml").write_text(sitemap_xml(base))
    (out / "llms.txt").write_text(llms_txt(profile, copy, base))
    (out / "copy.json").write_text(json.dumps(copy, indent=1))
    fid = best[1] or {}
    return {"copy": copy, "images": images, "base": base,
            "fidelity": {"template": direction.get("name"), "style": direction.get("style"),
                         "overall": fid.get("overall"), "scores": fid.get("scores"),
                         "verdict": fid.get("verdict"), "rounds": len(checks),
                         "history": [c["overall"] for c in checks]}}


def clear(out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
