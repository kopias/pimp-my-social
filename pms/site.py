"""The new website: Spark writes it, Muse Wonder builds it, code makes it findable.

- Copy (Muse Spark): headline, sections, product blurbs, search title and
  description, all held to the brand profile, so no invented claims.
- Design and code (Muse Wonder): one hand-built page in the chosen direction,
  from that copy and the reshot photos. Wonder is the strongest coder in the
  Muse family, and a bespoke page is the part of a makeover people remember.
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

from . import inspo
from .audit import AI_BOTS
from .photos import Shot
from .text import tidy_all

COPY_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["seo_title", "meta_description", "h1", "kicker", "subhead", "cta", "about",
                 "products", "proof_heading", "faq_heading", "visit", "share_title"],
    "properties": {
        "seo_title": {"type": "string", "description": "40-60 chars: what + where/who + name"},
        "meta_description": {"type": "string", "description": "120-160 chars, specific"},
        "h1": {"type": "string", "description": "the hero headline, punchy, under 9 words"},
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
with all CSS inline in a <style> tag. The bar is the best brand houses in the world: it should \
feel as considered as the reference sites below, not like a template. Restraint is the point: \
fewer, larger things, type set with care, space doing the work boxes and shadows do on cheap sites.

Direction: "{dname}". {layout}.
Palette (use as CSS variables): {palette}
Fonts, already loaded from Google Fonts: display "{display}", body "{body}".

REFERENCES. The attached screenshots are real brand sites this direction is modelled on. \
Borrow their STRUCTURE (grid, rhythm, type scale, navigation pattern, how products and \
prices sit). Never borrow their content: no logos, names, photos or copy from them.
{ref_notes}

TYPOGRAPHY. Follow this system exactly; it is what makes the page read as premium:
{typography}

LOGO. {logo}

Use EXACTLY this copy, word for word (JSON): {copy}

Testimonials to show if any (verbatim): {proof}
FAQs (verbatim; render as <details><summary> items): {faqs}
Contact: {contact}

Images, already in the site folder (use these paths; set width and height attributes; \
loading="lazy" on all but the hero):
{images}

Hard requirements:
- Semantic HTML5: <header>, <main>, <section>s with headings, <footer>. Exactly one <h1>.
- Every <img> has the alt text given. Mobile-first and responsive down to 360px wide.
- In <head>, put the marker <!--PMS:HEAD--> where meta tags will be injected. Do NOT write \
<title>, meta description, Open Graph tags or JSON-LD yourself.
- Put <!--PMS:BODY_END--> right before </body>.
- Link the fonts: <link rel="stylesheet" href="{font_css}">
- No JavaScript, no external images, no frameworks, no lorem ipsum, no placeholder text.
- Never add facts that aren't given: no star ratings, review counts, awards, badges, \
"best in town" claims, prices or dates beyond the copy. Testimonials are shown as quotes only.
- A footer with the business name, contact, hours, and the social links: {socials}.

Reply with only the HTML document, starting with <!doctype html>."""


def logo_brief(mark: dict | None, name: str) -> str:
    if not mark:
        return (f"There is no logo file. Set the name \"{name}\" as a wordmark in the display "
                "font, in the header and footer.")
    return (f"The business's remade logo mark is img/logo.png ({mark['w']}x{mark['h']}, ink on "
            "transparent) with a reversed copy img/logo-light.png for dark sections. Use the mark "
            f"in the header beside the name \"{name}\" set in the display font (the mark has no "
            "lettering of its own), 32 to 48px tall, with clear space; repeat it larger in the "
            "footer. Never put it in a box or pill, never add a shadow, never redraw it in CSS.")


def build_page(profile: dict, copy: dict, direction: dict, images: list[dict],
               font_css: str, mark: dict | None = None) -> str:
    img_lines = "\n".join(f"- {i['path']} ({i['w']}x{i['h']}): {i['what']}. alt: \"{i['alt']}\""
                          for i in images)
    refs = direction.get("refs", [])
    prompt = BUILD_PROMPT.format(
        ref_notes=inspo.notes(refs) or "(no reference notes for this direction)",
        typography=inspo.typography(), logo=logo_brief(mark, profile["name"]),
        dname=direction["name"], layout=direction["layout"], palette=json.dumps(direction["palette"]),
        display=direction["fonts"]["display"], body=direction["fonts"]["body"],
        copy=json.dumps(copy), proof=json.dumps(profile["proof"]),
        faqs=json.dumps(profile["faqs"]), contact=json.dumps(profile["contact"]),
        images=img_lines, font_css=font_css, socials=json.dumps(profile.get("socials", {})),
    )
    raw = m.ask(prompt, images=inspo.shots(refs)[:3], model=m.AGENT_MODEL, effort="medium",
                max_tokens=32000)
    match = re.search(r"<!doctype html.*</html>", raw, re.S | re.I)
    if not match:
        raise RuntimeError("Wonder didn't return an HTML document")
    return match.group(0)


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
          mark: dict | None = None) -> dict:
    """The whole site folder. Returns paths and timings for the report."""
    out.mkdir(parents=True, exist_ok=True)
    (out / "img").mkdir(exist_ok=True)
    base = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}/"
    copy = write_copy(profile)
    alts = {p["name"]: p["alt"] for p in copy["products"]}
    images: list[dict] = []
    for k, s in enumerate(shots):
        stem = re.sub(r"[^a-z0-9]+", "-", s.product.lower()).strip("-")
        w, h = _web_jpeg(Path(s.landscape), out / "img" / f"{stem}.jpg", 1600)
        images.append({"path": f"img/{stem}.jpg", "w": w, "h": h, "product": s.product,
                       "what": f"professional photo of {s.product}",
                       "alt": alts.get(s.product) or s.product, "role": "hero" if k == 0 else "product"})
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
    page = build_page(profile, copy, direction, page_imgs, direction["font_css"], mark)
    page = enforce(page, page_imgs + [{"path": "img/logo.png", "alt": profile["name"]},
                                      {"path": "img/logo-light.png", "alt": profile["name"]}])
    page = inject(page, head_tags(profile, copy, base, images, logo), body_end(profile, copy))
    (out / "index.html").write_text(page)
    (out / "robots.txt").write_text(robots_txt(base))
    (out / "sitemap.xml").write_text(sitemap_xml(base))
    (out / "llms.txt").write_text(llms_txt(profile, copy, base))
    (out / "copy.json").write_text(json.dumps(copy, indent=1))
    return {"copy": copy, "images": images, "base": base}


def clear(out: Path) -> None:
    if out.exists():
        shutil.rmtree(out)
