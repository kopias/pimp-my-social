"""The brand skill: everything the makeover learned, as a file any AI tool can load.

A skill folder in the Agent Skills format (SKILL.md with name + description
frontmatter, plus reference files). Drop it into Claude, or paste SKILL.md into
any assistant, and new posts, pages and photos come out in this brand's voice,
colours and photo style, with its real facts. Built from the profile and the
chosen direction by code, so it says exactly what the makeover used.
"""

from __future__ import annotations

import json
import shutil
import re
from pathlib import Path

from .directions import RESHOOT


def _slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:48] or "brand"


def skill_md(profile: dict, direction: dict, social: dict, base: str) -> str:
    name = _slug(profile["name"]) + "-brand"
    pal = direction["palette"]
    c = profile["contact"]
    v = profile["voice"]
    lines = [
        "---",
        f"name: {name}",
        f"description: Brand guide for {profile['name']} ({profile['category']}). Use when writing, "
        f"designing, photographing or posting anything for {profile['name']}: website copy, social "
        "posts, captions, product photos, emails, ads. Holds the voice, colours, fonts, photo style, "
        "products with exact prices, and the facts that must not be invented.",
        "---",
        "",
        f"# {profile['name']}",
        "",
        f"{profile['one_liner']}",
        "",
        f"- **What:** {profile['category']}",
        f"- **For:** {profile['audience']}",
    ]
    if c.get("address") or profile.get("location"):
        lines.append(f"- **Where:** {c.get('address') or profile['location']}")
    for label, key in (("Phone", "phone"), ("Email", "email"), ("Order", "order_url")):
        if c.get(key):
            lines.append(f"- **{label}:** {c[key]}")
    lines.append(f"- **Website:** {base}")
    if c.get("hours"):
        lines += ["", "**Hours:** " + "; ".join(c["hours"])]
    lines += [
        "", "## Rules that are not negotiable", "",
        "- Use only facts from this file or the business itself. Never invent prices, reviews, star "
        "ratings, awards, ingredients, discounts or events.",
        "- Prices exactly as listed under Products.",
        "- Product photos must show the real product: restyle the set and light, never the product.",
        "- At most one exclamation mark per piece. No ALL CAPS.",
        "", "## Voice", "",
        f"Sounds: {', '.join(v['adjectives'])}.", "",
        f"In their words: “{v['sample']}”" if v.get("sample") else "", "",
        "Do:", *[f"- {x}" for x in v["do"]], "", "Don't:", *[f"- {x}" for x in v["dont"]],
        "", "What makes them worth choosing:", *[f"- {x}" for x in profile["value_props"]],
        "", "## Look: " + direction["name"], "",
        direction["pitch"], "",
        "| Role | Colour |", "|---|---|",
        *[f"| {role} | `{hexv}` |" for role, hexv in pal.items()],
        "",
        f"- **Display type:** {direction['fonts']['display']} (Google Fonts)",
        f"- **Body type:** {direction['fonts']['body']} (Google Fonts)",
        f"- **Layout:** {direction['layout']}",
        "", "## Photography", "",
        f"Style: {direction['photo']}.", "",
        "To reshoot a product photo with an image model (Muse Image, or any edit model), "
        "use this prompt with the product name filled in:", "",
        "```", RESHOOT.format(subject="{product}", photo=direction["photo"]), "```",
        "", "## Products", "",
        "| Product | Price | About |", "|---|---|---|",
        *[f"| {p['name']} | {p['price'] or 'ask'} | {p['description']} |" for p in profile["products"]],
        "", "## Customers ask", "",
    ]
    for f in profile["faqs"]:
        lines += [f"**{f['q']}** {f['a']}", ""]
    tags = " ".join(social.get("hashtags") or profile.get("hashtags", []))
    lines += [
        "## Social", "",
        f"- Handle: @{social.get('handle', '')}" if social.get("handle") else "",
        f"- Bio: {social.get('bio', '')}" if social.get("bio") else "",
        f"- Hashtags: {tags}" if tags else "",
        "- Instagram: open the caption with a hook line; one product per post; 4:5 portrait.",
        "- Campaign: everything says one sentence underneath (see references/campaign.md). "
        "Never argue the product is good; show the person, end on the lockup.",
        "- Short video: remix formats that are working (see references/formats.md): keep the "
        "format's essence, swap in only your own products, prices and place; text above the "
        "bottom third and clear of the right-hand buttons; end on the logo and how to buy.",
        "- LinkedIn: the business and its people. X: short and specific.",
        "", "## Files in this skill", "",
        "- `references/brand.json`: the full brand profile",
        "- `references/palette.css`: colours and fonts as CSS variables",
        "- `references/examples.md`: the posts written in the makeover, as examples of the voice",
        "- `references/formats.md`: the video formats remixed for you, with their beats",
        "- `references/campaign.md`: your campaign idea, lockup and every piece's copy; "
        "`references/campaign-framework.md`: the rules to write more",
        "- `assets/logo.png` (and `logo-light.png`): the remade logo mark; set the name beside it "
        "in the display font",
        "",
    ]
    return "\n".join(x for x in lines if x is not None)


def palette_css(direction: dict) -> str:
    vars_ = "\n".join(f"  --{k}: {v};" for k, v in direction["palette"].items())
    return (f"@import url('{direction['font_css']}');\n\n:root {{\n{vars_}\n"
            f"  --font-display: '{direction['fonts']['display']}', serif;\n"
            f"  --font-body: '{direction['fonts']['body']}', sans-serif;\n}}\n")


def examples_md(social: dict) -> str:
    out = ["# Example posts from the makeover", ""]
    for ch in social.get("channels", []):
        out += [f"## {ch['channel'].title() if ch['channel'] != 'x' else 'X'}", ""]
        for p in ch["posts"]:
            out += [p["caption"], "", "---", ""]
    return "\n".join(out)


def formats_md(remixes: list | None) -> str:
    out = ["# Video formats remixed for this brand", ""]
    for r in remixes or []:
        f, g = r["format"], r["best"]["grounded"]
        out += [f"## {g['title']} ({f['name']})", "", f"Essence: {f['essence']}", "",
                "Why it works: " + "; ".join(f["why_it_works"]), "", "Beats:", ""]
        out += [f"- {b['seconds']}s {b['shot']} ({b['motion']}): {b['text'] or '(no text)'}"
                for b in g["beats"]]
        out += ["", f"Caption: {g['caption']}", "", f"Sound: {g['sound']}", ""]
    return "\n".join(out)


def campaign_md(camp: dict, direction: dict) -> str:
    pal = direction["palette"]
    accent = pal["accent"] if pal["accent"].lower() != pal["ink"].lower() else pal["accent2"]
    out = ["# Your campaign", "", f"The idea: {camp['thesis']['not_x']} {camp['thesis']['is_y']}", "",
           f"The lockup: `{camp['question']}` in {direction['fonts']['display']}, over a 200px rule in "
           f"{accent}, over your address in a monospace. Three elements, nothing else.", "", "## The pieces", ""]
    for p in camp["pieces"]:
        out += [f"### {p['persona']} ({p['kind']})", "", f"Headline: {p['headline']}", ""]
        out += [f"Body: {p['body']}", ""] if p["body"] else []
        out += [f"Caption: {p['caption']}", ""]
    f = camp["film"]
    out += [f"### Film: {f['title']}", ""] + [f"- {b['role']}: {b['action']} / “{b['caption']}”" for b in f["beats"]]
    out += ["", f"Caption: {f['caption']}", "", f"Sound: {f['sound']}", ""]
    return "\n".join(out)


def write(profile: dict, direction: dict, social: dict, base: str, out: Path,
          remixes: list | None = None, mark: dict | None = None, camp: dict | None = None) -> Path:
    folder = out / (_slug(profile["name"]) + "-brand")
    (folder / "references").mkdir(parents=True, exist_ok=True)
    (folder / "SKILL.md").write_text(skill_md(profile, direction, social, base))
    (folder / "references" / "brand.json").write_text(json.dumps(profile, indent=1))
    (folder / "references" / "palette.css").write_text(palette_css(direction))
    (folder / "references" / "examples.md").write_text(examples_md(social))
    (folder / "references" / "formats.md").write_text(formats_md(remixes))
    if camp:
        (folder / "references" / "campaign.md").write_text(campaign_md(camp, direction))
        fw = Path(__file__).resolve().parent.parent / "inspo" / "social" / "campaign" / "SKILL.md"
        (folder / "references" / "campaign-framework.md").write_text(fw.read_text().split("---", 2)[-1].strip())
    if mark:
        (folder / "assets").mkdir(exist_ok=True)
        shutil.copy(mark["mark"], folder / "assets" / "logo.png")
        shutil.copy(mark["mark_light"], folder / "assets" / "logo-light.png")
    return folder
