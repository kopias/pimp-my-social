"""The campaign: social content in the "got milk?" register, grounded in this business.

Ported from the Loreto "got skills?" campaign (the reformer pilates film, the
robot crash, the poster roster), with every model swapped for a Meta one. The
framework lives in inspo/social/campaign/SKILL.md; this is the code that runs it.

The rule that decides everything: every piece is the same sentence underneath.
The customer believed a problem was a deficiency in them, and it was something
this business fixes all along: "You are not X. You are Y." Got Milk never argued
milk was nutritious, so nothing here argues the product is good. Situation, then
card.

Three registers, one lockup ("got ___?" over an accent rule over the address):

  poster       the roster. Glamorous people in their element, looking down the
               lens, closed fist against the chin (the Shaq pose; a pointing
               finger renders as the middle finger one time in three), wearing or
               holding the real product. Wry two-line headline, about forty words.
  deprivation  the robot crash. The world without what the business gives, as
               one gross, unambiguous physical event, and one deadpan line.
  film         the reformer. Observational, never a talking head: the failure,
               the face, the fix, the payoff with a glance to the lens. Ordinary,
               dignified casting; the instruction failed them, not their body.

Who does what:
  Muse Spark       the brief (thesis, roster, scenes, copy), every image check,
                   the review of the finished film
  Muse Image       every photograph; one cast reference is passed into every film
                   shot with the product photo, so the person and the product stay
                   the same across cuts (the seedance omni_reference trick)
  SAM 3.1          finds every hand so Spark can inspect it close up; lifts the
                   person off the set so the film moves in depth
  the browser      all type (pms/typeset.py). The image model never draws a letter.
"""

from __future__ import annotations

import asyncio
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

from muse import client as m

from . import typeset
from .photos import Shot, find
from .remix import short_link
from .social import cover
from .text import tidy_all

HERE = Path(__file__).resolve().parent.parent
FRAMEWORK = HERE / "inspo" / "social" / "campaign"
POSTER = (1080, 1350)
W, H, FPS = 1080, 1920, 30
BEAT_S, CARD_S = 3.4, 3.2
BANNED = re.compile(r"\b(AI|A\.I\.|artificial intelligence|algorithm|agent|best[- ]in[- ]class|"
                    r"game[- ]chang\w*|elevate\w*|unlock\w*)\b", re.I)
MONEY = re.compile(r"[$£€]\s?\d|\d+\s?%")

# --- 1. the brief ------------------------------------------------------------------

PERSON = {"type": "string", "description": "who, specifically: age, look, hair, build. Never a real or famous person"}
PRODUCT = {"type": "integer", "description": "index into the product list, or -1 for none"}
HOW = {"type": "string", "enum": ["worn", "held", "in frame", "none"]}

POSTER_ITEM = {
    "type": "object", "additionalProperties": False,
    "required": ["persona", "who", "discipline", "setting", "props", "expression", "product", "how",
                 "headline", "body", "caption"],
    "properties": {
        "persona": {"type": "string", "description": "two-word label, e.g. 'the boxer'"},
        "who": PERSON,
        "discipline": {"type": "string", "description": "what they are visibly brilliant at"},
        "setting": {"type": "string", "description": "a specific real place where that discipline happens"},
        "props": {"type": "string", "description": "one or two props that make the discipline read"},
        "expression": {"type": "string", "enum": ["calm faintly amused", "wry knowing", "proud cheeky"]},
        "product": PRODUCT, "how": HOW,
        "headline": {"type": "string", "description": "wry first-person aside, two lines split by |"},
        "body": {"type": "string", "description": "about forty words, first person"},
        "caption": {"type": "string", "description": "the post caption, in the brand voice"},
    },
}

BEAT_ITEM = {
    "type": "object", "additionalProperties": False,
    "required": ["role", "action", "framing", "caption"],
    "properties": {
        "role": {"type": "string", "enum": ["failure", "face", "fix", "payoff"]},
        "action": {"type": "string",
                   "description": "what physically happens, described mechanically, as a single frozen moment"},
        "framing": {"type": "string", "enum": ["wide", "medium", "close", "reaction close-up"]},
        "caption": {"type": "string", "description": "on-screen words, seven at most"},
    },
}

BRIEF_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["question", "thesis", "posters", "deprivation", "film", "hashtags"],
    "properties": {
        "question": {"type": "string", "description": "the lockup, lowercase: 'got ___?'"},
        "thesis": {"type": "object", "additionalProperties": False, "required": ["not_x", "is_y"],
                   "properties": {"not_x": {"type": "string", "description": "You are not ..."},
                                  "is_y": {"type": "string", "description": "You are ... / It was ..."}}},
        "posters": {"type": "array", "items": POSTER_ITEM},
        "deprivation": {
            "type": "object", "additionalProperties": False,
            "required": ["scene", "furniture", "line", "product", "how", "caption"],
            "properties": {
                "scene": {"type": "string", "description": "the one physical event, as a photograph"},
                "furniture": {"type": "string",
                              "description": "the real-world details that make the place believable"},
                "line": {"type": "string", "description": "one deadpan sentence"},
                "product": PRODUCT, "how": HOW,
                "caption": {"type": "string"},
            },
        },
        "film": {
            "type": "object", "additionalProperties": False,
            "required": ["title", "who", "wardrobe", "setting", "product", "how", "beats", "caption", "sound"],
            "properties": {
                "title": {"type": "string"},
                "who": PERSON,
                "wardrobe": {"type": "string", "description": "exactly what they wear before the fix"},
                "setting": {"type": "string", "description": "the one place the film happens, specifically"},
                "product": PRODUCT, "how": HOW,
                "beats": {"type": "array", "items": BEAT_ITEM},
                "caption": {"type": "string"},
                "sound": {"type": "string", "description": "what to pick from the app's licensed library"},
            },
        },
        "hashtags": {"type": "array", "items": {"type": "string"}},
    },
}

BRIEF_PROMPT = """You are the creative director on a social campaign for {name} ({category}, \
{location}). Read the framework below and follow it exactly, then the examples, then write the brief.

{framework}

THE BUSINESS (every fact you use comes from here; never invent prices, awards, reviews, numbers, \
or events, and never put a price in the copy):
{profile}

Products (index: name, what it is): {products}

Write:
- question: the lockup, in the got milk? shape: "got" plus one plain word from this business's \
world, lowercase, with a question mark. The word must be true of every piece in the campaign, so \
not one product or material unless everything shown is it.
- thesis: the misconfiguration flip for this business's customer.
- posters: exactly three, a roster. Three different people and disciplines whose world rhymes \
with this business's customers. Each wears or holds a real product from the list (choose the \
product that suits the persona; use each product at most once if you can).
- deprivation: one still.
- film: exactly four beats, roles in order failure, face, fix, payoff. The fix is where the \
product arrives. The payoff ends on a wry glance straight to the lens. The captions never say \
the thesis outright (don't reuse its words); they let the pictures make the jump.
- captions in the brand voice ({voice}): at most one emoji, no hashtags inside them.
- hashtags: 3 to 6.
{fixes}"""


def framework() -> str:
    return (FRAMEWORK / "SKILL.md").read_text().split("---", 2)[-1].strip()


def _words(s: str) -> int:
    return len(s.split())


def gate(b: dict, profile: dict) -> list[str]:
    """The copy rules, checked in code. Returns what's wrong."""
    bad = []
    q = b["question"].strip()
    if not re.fullmatch(r"got [a-z][a-z' -]{1,24}\?", q):
        bad.append(f'question "{q}" must be "got <word>?" in lowercase')
    if len(b["posters"]) != 3:
        bad.append("posters: exactly three")
    if [x["role"] for x in b["film"]["beats"]] != ["failure", "face", "fix", "payoff"]:
        bad.append("film beats: exactly four, in the order failure, face, fix, payoff")
    copy = []
    for p in b["posters"]:
        lines = [x for x in p["headline"].split("|") if x.strip()]
        if not 1 <= len(lines) <= 3 or max(len(x.strip()) for x in lines) > 30:
            bad.append(f'poster "{p["persona"]}": headline must be 2 lines of at most 30 characters, split by |')
        if not 25 <= _words(p["body"]) <= 60:
            bad.append(f'poster "{p["persona"]}": body is {_words(p["body"])} words; write about forty')
        copy += [p["headline"], p["body"]]
    copy += [b["deprivation"]["line"]] + [x["caption"] for x in b["film"]["beats"]]
    for x in b["film"]["beats"]:
        if _words(x["caption"]) > 7:
            bad.append(f'film caption "{x["caption"]}" is over seven words')
    for c in copy:
        if BANNED.search(c):
            bad.append(f'"{BANNED.search(c).group(0)}" is banned in the copy: "{c}"')
        if MONEY.search(c):
            bad.append(f'no prices or percentages in the copy: "{c}"')
    return bad


def brief(profile: dict, fixes: list[str] | None = None, usable: set[int] | None = None) -> dict:
    facts = {k: profile.get(k) for k in ("name", "one_liner", "category", "audience", "location",
                                        "value_props", "proof", "faqs")}
    # Only products with a studio photo: the image model is shown the real thing, never asked to imagine it.
    products = {i: f'{p["name"]}: {p["subject"]}' for i, p in enumerate(profile["products"])
                if usable is None or i in usable}
    for attempt in range(2):
        raw = m.ask(BRIEF_PROMPT.format(
            name=profile["name"], category=profile["category"], location=profile.get("location") or "",
            framework=framework(), profile=json.dumps(facts), products=json.dumps(products),
            voice=", ".join(profile["voice"]["adjectives"]),
            fixes=("\nThe last draft broke these rules; fix every one:\n- " + "\n- ".join(fixes)) if fixes else ""),
            schema=BRIEF_SCHEMA, effort="medium", max_tokens=12000)
        b = tidy_all(json.loads(raw))
        b["question"] = b["question"].strip().lower()
        b["hashtags"] = ["#" + h.lstrip("#").replace(" ", "") for h in b["hashtags"]]
        fixes = gate(b, profile)
        if not fixes:
            break
    b["gate"] = fixes or []  # anything still wrong after the retry is shown, not hidden
    n = len(profile["products"])
    for item in [*b["posters"], b["deprivation"], b["film"]]:
        if not (0 <= item["product"] < n) or item["how"] == "none" or (usable is not None and item["product"] not in usable):
            item["product"], item["how"] = -1, "none"
    return b


# --- 2. photographs ----------------------------------------------------------------

# Every clause after the subject defeats a specific failure; see SKILL.md, "The traps".
PLAIN = ("A plain straight photograph of a real person in a real place. No paper, no page, no "
         "book, no magazine, no border, no frame. No text, no lettering, no signs, no logos, no "
         "watermark.")

POSTER_SHOT = ("Waist up photograph shot on a 35mm camera, the subject filling most of the frame "
               "from the waist upward and standing in the right two thirds of the frame, calm "
               "uncluttered space on the left. {who}, strikingly good-looking and charismatic, cast "
               "like a celebrity in a national print campaign, {wearing}in {setting}, {props} recognisable "
               "but softly out of focus behind them. They look straight into the lens with a "
               "{expression} half smile. Their closed fist rests against their chin and jaw so the "
               "back of the hand sits clearly beside the face; no finger is extended. Sharp focus "
               "on the eyes and the back of the hand. {light}, clean and bright. " + PLAIN)

DEPRIVATION_SHOT = ("{scene}. {furniture}. Shot like a press photograph on a long lens: real, "
                    "specific, slightly overcast daylight, the event in the centre of the frame "
                    "and nothing staged-looking. Everything generic and unbranded: no real "
                    "company's products, no logos, numbers only on bibs or signage if the scene "
                    "needs them. {wearing}No text, no lettering, no watermark, no border.")

CAST_SHOT = ("Full-length reference photograph of {who}, wearing {wardrobe}, standing straight "
             "and relaxed, arms by their sides, facing the camera, on a plain light grey studio "
             "ground with soft even light. Natural, ordinary and dignified, not a fashion model "
             "pose. " + PLAIN)

BEAT_SHOT = ("{action}. The same person as image 1: same face, hair, skin and build. {wardrobe} "
             "Setting: {setting}. {framing} An observational documentary photograph, as if the "
             "camera is simply there: available light, natural colour, nobody looks at the camera"
             "{glance}. No haze, no god rays, no colour grading, no cinematic look, no posed "
             "fashion styling. {catchlights}" + PLAIN)

FRAMINGS = {"wide": "Wide shot, the whole body and the place around them.",
            "medium": "Medium shot from the waist up.",
            "close": "Close shot of the hands and what they are doing.",
            "reaction close-up": "Tight close-up of the face, eyes sharp."}


def _subject(profile: dict, i: int) -> str:
    p = profile["products"][i]
    return f'{p["name"]} ({p["subject"]})'


def _wearing(item: dict, profile: dict, sentence: bool = False) -> str:
    if item["product"] < 0:
        return ""
    what = f'the exact {profile["products"][item["product"]]["subject"]} from the reference photo'
    verb = {"worn": "wearing", "held": "holding", "in frame": "with"}.get(item["how"], "with")
    phrase = (f"{verb} {what}, identical in colour, pattern, fabric and every detail, nothing "
              f"added or changed on it")
    return (phrase[0].upper() + phrase[1:] + ". ") if sentence else phrase + ", "


SOFTEN = """An image generator's content filter refused this prompt. Rewrite it so a strict filter \
accepts it: keep the subject, setting, wardrobe, framing and the physical event, but describe any \
damage, mishap or failure mildly and concretely (no words like split, burst, rip, crash, collapse, \
injury, broken, exposed, tight, strain, body). Keep every sentence that starts with "No". Return only \
the new prompt.

Prompt: {prompt}"""


def _shoot(prompt: str, refs: list[str], out: Path) -> Path:
    def go(p: str) -> Path:
        return m.edit_images(refs, p, out) if refs else m.generate_image(p, out, size="1024x1536")
    try:
        return go(prompt)
    except Exception as e:
        # The filter used to say "content"; since late Oct 2026 a refusal can also come back as
        # the bare 400 "request was invalid" that survives the client's retries.
        if "content" not in str(e).lower() and "invalid" not in str(e).lower():
            raise
        print(f"campaign: {out.stem} refused ({str(e)[:60]}); Spark rewrites the prompt once")
        return go(m.ask(SOFTEN.format(prompt=prompt), effort="low", max_tokens=2000).strip())


# --- 3. checks ---------------------------------------------------------------------

CHECK_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["hands_ok", "hands_note", "page_border", "lettering", "product_match", "reads", "note"],
    "properties": {
        "hands_ok": {"type": "boolean"},
        "hands_note": {"type": "string"},
        "page_border": {"type": "boolean", "description": "looks like a printed page, magazine, frame or screen"},
        "lettering": {"type": "array", "description": "every patch of letters or numbers, in percent of the frame",
                      "items": {"type": "object", "additionalProperties": False,
                                "required": ["x", "y", "w", "h", "kind"],
                                "properties": {**{k: {"type": "number"} for k in "xywh"},
                                               "kind": {"type": "string", "enum": ["garbled", "natural"],
                                                        "description": "natural: numbers that belong in the scene (a tape measure, a race bib, a clock); garbled: invented words or signage"}}}},
        "product_match": {"type": "integer", "description": "1-10; 10 if there is no product to match"},
        "reads": {"type": "boolean", "description": "the intended situation reads at a glance"},
        "note": {"type": "string"},
    },
}

CHECK_PROMPT = """Image 1 is a photograph for a social campaign. It should show: {intent}
{refs}{hands}
Check it the way a photo editor would before it goes out:
- hands: count the fingers on every hand. Any extra, missing, fused or bent-wrong finger fails. \
Any single extended finger, or any gesture that could read as rude, fails.
- page_border: does it look like a photo of a printed page, magazine spread, frame or screen?
- lettering: list every patch of letters or numbers anywhere in it, and say whether it is \
natural to the scene (a tape measure, a race bib) or garbled invented text.
- product_match: {product}
- reads: does the situation read at a glance, as described?"""


def _hand_crops(img: Path, out: Path) -> list[Path]:
    """SAM 3.1 finds every hand; each is cropped with some wrist so Spark can count fingers."""
    try:
        segs = asyncio.run(m.segment("hand", img))
    except Exception as e:
        print(f"campaign: SAM hands failed: {e!r}"[:200])
        return []
    crops = []
    with Image.open(img) as im:
        for k, s in enumerate(sorted(segs, key=lambda s: -(s.confidence or 0))[:4]):
            if (s.confidence or 0) < 0.4:
                continue
            l, t, r, b = s.box
            pad = int(max(r - l, b - t) * 0.35)
            c = im.crop((max(0, l - pad), max(0, t - pad), min(im.width, r + pad), min(im.height, b + pad)))
            p = out.with_name(f"{out.stem}_hand{k}.jpg")
            c.convert("RGB").save(p, quality=90)
            crops.append(p)
    return crops


def check(img: Path, intent: str, product_ref: str | None) -> dict:
    hands = _hand_crops(img, img)
    refs = ("Image 2 is the real product it must match.\n" if product_ref else "")
    first_hand = 3 if product_ref else 2
    hands_txt = (f"Images {first_hand} onward are close-ups of each hand SAM found in image 1.\n"
                 if hands else "")
    raw = m.ask(CHECK_PROMPT.format(
        intent=intent, refs=refs, hands=hands_txt,
        product=("does the product in image 1 match image 2 in colour, pattern, cut and details? "
                 "Be strict: a different pattern scale or shape is a 5 or below."
                 if product_ref else "there is no product to match; answer 10.")),
        images=[img, *([product_ref] if product_ref else []), *hands], schema=CHECK_SCHEMA,
        effort="low", max_tokens=3000)
    c = json.loads(raw)
    c["hands_checked"] = len(hands)
    return c


def passes(c: dict) -> bool:
    return c["hands_ok"] and not c["page_border"] and c["product_match"] >= 7 and c["reads"]


def _shoot_checked(prompt: str, refs: list[str], out: Path, intent: str, product_ref: str | None) -> dict:
    """Shoot, check, and reshoot once if the shot itself is wrong (a bad hand, a page border, the
    wrong product). Lettering alone never costs a reshoot: it's patched, which keeps the cast."""
    takes = []
    for k in range(2):
        p = out.with_name(f"{out.stem}_take{k + 1}.png")
        try:
            _shoot(prompt, refs, p)
        except Exception as e:
            print(f"campaign: shot failed ({out.stem}): {e!r}"[:300])
            continue
        c = check(p, intent, product_ref)
        takes.append({"path": str(p), "check": c})
        if passes(c):
            break
    if not takes:
        raise RuntimeError(f"Muse Image couldn't make {out.stem}")
    best = max(takes, key=lambda t: (passes(t["check"]), t["check"]["hands_ok"], t["check"]["product_match"]))
    return {**best, "takes": len(takes)}


def patch(img: Path, boxes: list[dict], out: Path) -> Path:
    """Feathered local defocus over stray lettering: it reads as depth of field, not a block."""
    im = Image.open(img).convert("RGB")
    if not boxes:
        im.save(out)
        return out
    blurred = im.filter(ImageFilter.GaussianBlur(18))
    mask = Image.new("L", im.size, 0)
    from PIL import ImageDraw
    d = ImageDraw.Draw(mask)
    for b in boxes:
        x0, y0 = b["x"] / 100 * im.width, b["y"] / 100 * im.height
        x1, y1 = x0 + b["w"] / 100 * im.width, y0 + b["h"] / 100 * im.height
        pad = 0.25 * max(x1 - x0, y1 - y0, 20)
        d.ellipse((x0 - pad, y0 - pad, x1 + pad, y1 + pad), fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(24))
    Image.composite(blurred, im, mask).save(out)
    return out


# --- 4. type -----------------------------------------------------------------------


def _accent(direction: dict) -> str:
    pal = direction["palette"]
    return pal["accent"] if pal["accent"].lower() != pal["ink"].lower() else pal["accent2"]


def _esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _lockup_css(scale: float, colour: str, accent: str, display: str) -> str:
    return f"""
 .lock{{position:absolute;left:0;right:0;text-align:center;color:{colour}}}
 .lock .q{{font-family:"{display}",Georgia,serif;font-weight:400;font-size:{72 * scale:.0f}px;
   line-height:1;letter-spacing:-.015em}}
 .lock .rule{{width:{200 * scale:.0f}px;height:3px;background:{accent};margin:{24 * scale:.0f}px auto {20 * scale:.0f}px}}
 .lock .url{{font-family:"JetBrains Mono",monospace;font-size:{22 * scale:.0f}px;letter-spacing:.06em;opacity:.9}}"""


def _lockup(question: str, url: str, style: str) -> str:
    return (f'<div class="lock" style="{style}"><div class="q">{_esc(question)}</div>'
            f'<div class="rule"></div><div class="url">{_esc(url)}</div></div>')


def poster_page(img: Path, item: dict, question: str, url: str, direction: dict, out: Path) -> dict:
    disp, body = direction["fonts"]["display"], direction["fonts"]["body"]
    lines = [x.strip() for x in item["headline"].split("|") if x.strip()]
    # Each line is set on one line, sized so the longest fits the column: a headline that
    # wraps on its own runs into the face.
    size = int(min({1: 72, 2: 66, 3: 56}.get(len(lines), 46), 600 / (0.43 * max(len(x) for x in lines))))
    css = f"""
 #p>img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;object-position:50% 30%}}
 .scrim{{position:absolute;inset:0;background:
   linear-gradient(100deg,rgba(14,13,12,.74) 0%,rgba(14,13,12,.5) 26%,rgba(14,13,12,.12) 48%,rgba(14,13,12,0) 62%),
   linear-gradient(0deg,rgba(10,10,10,.8) 0%,rgba(10,10,10,.18) 24%,rgba(10,10,10,0) 36%)}}
 .copy{{position:absolute;left:70px;top:82px;width:600px;display:flex;flex-direction:column;gap:28px}}
 .head{{font-family:"{disp}",Georgia,serif;font-weight:400;font-size:{size}px;line-height:1.06;
   color:#fff;letter-spacing:-.015em;text-shadow:0 2px 28px rgba(0,0,0,.5);white-space:nowrap}}
 .body{{width:410px;font-family:"{body}",system-ui,sans-serif;font-size:21px;line-height:1.58;
   color:rgba(255,255,255,.93);text-shadow:0 1px 14px rgba(0,0,0,.6);text-wrap:pretty}}
 {_lockup_css(0.92, "#fff", _accent(direction), disp)}"""
    html = (f'<img src="{img.name}"><div class="scrim"></div><div class="copy">'
            f'<div class="head">{"<br>".join(_esc(x) for x in lines)}</div>'
            f'<div class="body">{_esc(item["body"])}</div></div>'
            + _lockup(question, url, "bottom:64px"))
    return {"html": html, "css": css, "out": out, "w": POSTER[0], "h": POSTER[1],
            "fonts": [direction["font_css"]], "assets": [img]}


def deprivation_page(img: Path, line: str, question: str, url: str, direction: dict, out: Path) -> dict:
    disp = direction["fonts"]["display"]
    css = f"""
 #p>img{{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}}
 .scrim{{position:absolute;inset:0;background:
   linear-gradient(180deg,rgba(10,10,10,.62) 0%,rgba(10,10,10,.12) 26%,rgba(10,10,10,0) 40%),
   linear-gradient(0deg,rgba(10,10,10,.78) 0%,rgba(10,10,10,.16) 24%,rgba(10,10,10,0) 36%)}}
 .line{{position:absolute;left:90px;right:90px;top:84px;text-align:center;font-family:"{disp}",Georgia,serif;
   font-weight:400;font-style:italic;font-size:56px;line-height:1.1;color:#fff;letter-spacing:-.01em;
   text-shadow:0 2px 24px rgba(0,0,0,.55);text-wrap:balance}}
 {_lockup_css(0.92, "#fff", _accent(direction), disp)}"""
    html = (f'<img src="{img.name}"><div class="scrim"></div><div class="line">{_esc(line)}</div>'
            + _lockup(question, url, "bottom:64px"))
    return {"html": html, "css": css, "out": out, "w": POSTER[0], "h": POSTER[1],
            "fonts": [direction["font_css"]], "assets": [img]}


def caption_page(text: str, direction: dict, out: Path) -> dict:
    css = f"""
 .shade{{position:absolute;left:0;right:0;bottom:0;height:46%;
   background:linear-gradient(0deg,rgba(0,0,0,0) 0%,rgba(0,0,0,.42) 42%,rgba(0,0,0,.42) 58%,rgba(0,0,0,0) 100%)}}
 .cap{{position:absolute;left:90px;right:170px;bottom:330px;text-align:center;
   font-family:"{direction['fonts']['body']}",system-ui,sans-serif;font-weight:600;font-size:52px;
   line-height:1.22;color:#fff;letter-spacing:-.005em;text-wrap:balance;
   text-shadow:0 2px 3px rgba(0,0,0,.45),0 0 34px rgba(0,0,0,.55)}}"""
    return {"html": f'<div class="shade"></div><div class="cap">{_esc(text)}</div>', "css": css, "out": out, "w": W, "h": H,
            "transparent": True, "fonts": [direction["font_css"]]}


def endcard_page(question: str, url: str, direction: dict, out: Path) -> dict:
    pal = direction["palette"]
    css = f"""
 #p{{background:{pal['ink']}}}
 .glow{{position:absolute;inset:0;background:radial-gradient(ellipse 70% 55% at 50% 44%,rgba(255,255,255,.06),transparent 70%)}}
 {_lockup_css(1.8, pal['bg'], _accent(direction), direction['fonts']['display'])}"""
    return {"html": '<div class="glow"></div>' + _lockup(question, url, "top:50%;transform:translateY(-50%)"),
            "css": css, "out": out, "w": W, "h": H, "fonts": [direction["font_css"]]}


# --- 5. the film -------------------------------------------------------------------


def _ease(t: float) -> float:
    return t * t * (3 - 2 * t)


class Plate:
    """One still, moving: a slow push, and with SAM's person mask, the person comes
    forward faster than the set behind them (parallax), so a still reads as a shot."""

    def __init__(self, path: Path, k: int):
        self.base = cover(path, (int(W * 1.14), int(H * 1.14)))
        self.side = 1 if k % 2 else -1
        self.front = None
        tmp = path.with_suffix(".sam.jpg")
        self.base.save(tmp, quality=90)
        try:
            seg, mask = asyncio.run(find("person", tmp))
            if seg is not None and (seg.confidence or 0) >= 0.5 and 0.04 < mask.mean() < 0.75:
                a = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))
                self.front = self.base.convert("RGBA")
                self.front.putalpha(a)
        except Exception as e:
            print(f"campaign: SAM lift failed: {e!r}"[:200])
        tmp.unlink(missing_ok=True)

    def frame(self, p: float) -> Image.Image:
        e = _ease(p)

        def win(z: float, drift: float) -> tuple[int, int, int, int]:
            cw, ch = W * z, H * z
            x = (self.base.width - cw) / 2 + drift
            y = (self.base.height - ch) / 2
            return int(x), int(y), int(x + cw), int(y + ch)
        back = self.base.crop(win(1.12 - 0.05 * e, self.side * 24 * e)).resize((W, H), Image.BILINEAR)
        if self.front is not None:
            fr = self.front.crop(win(1.12 - 0.10 * e, self.side * 44 * e)).resize((W, H), Image.BILINEAR)
            back.paste(fr, (0, 0), fr)
        return back


def cut_film(stills: list[Path], captions: list[Path], endcard: Path, out: Path) -> dict:
    """Hard cuts, like the reformer film: four beats, then the lockup on a slow push."""
    mp4 = out / "film.mp4"
    total = BEAT_S * len(stills) + CARD_S
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "21", "-pix_fmt", "yuv420p",
         "-maxrate", "8M", "-bufsize", "16M", "-c:a", "aac", "-t", f"{total:.3f}",
         "-movflags", "+faststart", str(mp4)], stdin=subprocess.PIPE)
    timeline, poster = [], None
    n = round(BEAT_S * FPS)
    for k, (s, c) in enumerate(zip(stills, captions)):
        plate = Plate(s, k)
        cap = Image.open(c).convert("RGBA")
        timeline.append({"start_s": round(k * BEAT_S, 2), "seconds": BEAT_S})
        for f in range(n):
            im = plate.frame(f / n)
            t = f / FPS
            if t > 0.45:  # the picture lands first, then the words
                a = min(1.0, (t - 0.45) / 0.25)
                layer = cap if a >= 1 else Image.fromarray(
                    (np.asarray(cap) * np.array([1, 1, 1, a])).astype(np.uint8), "RGBA")
                im.paste(layer, (0, 0), layer)
            if poster is None and t >= 1.2:
                poster = im.copy()
            ff.stdin.write(im.convert("RGB").tobytes())
    card = Image.open(endcard).convert("RGB").resize((int(W * 1.04), int(H * 1.04)), Image.LANCZOS)
    m_ = round(CARD_S * FPS)
    for f in range(m_):
        z = 1.04 - 0.035 * _ease(f / m_)  # the window shrinks: a slow push in on the lockup
        cw, ch = W * z, H * z
        x, y = (card.width - cw) / 2, (card.height - ch) / 2
        ff.stdin.write(card.crop((int(x), int(y), int(x + cw), int(y + ch))).resize((W, H), Image.BILINEAR).tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg failed to encode the film")
    poster_path = out / "film_poster.jpg"
    poster.convert("RGB").save(poster_path, quality=86)
    return {"mp4": str(mp4), "poster": str(poster_path), "duration_s": round(total, 1), "timeline": timeline}


REVIEW_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["thesis", "hook", "continuity", "legibility", "grounded", "overall", "verdict", "fixes"],
    "properties": {
        **{k: {"type": "integer", "description": "1-10"} for k in
           ("thesis", "hook", "continuity", "legibility", "grounded", "overall")},
        "verdict": {"type": "string", "description": "two sentences to the owner"},
        "fixes": {"type": "array", "items": {"type": "string"}},
    },
}

REVIEW_PROMPT = """You are the creative director. This 9:16 film for {name} is meant to say, \
without ever saying it outright: "You are not {not_x}. {is_y}." It is observational, in the \
register of a good metaphor commercial, and ends on the lockup "{question}". The file is silent \
on purpose: sound is picked in the app.

Score 1-10: thesis (does the flip land without a product claim?), hook (does the first second \
stop the scroll?), continuity (is it the same person, clothes and place across shots?), \
legibility on a phone, grounded (from the fix onward, is the product shown exactly {product}, one \
of {products}?), overall. Be honest; a 10 is rare.

The clothes before the fix ({before}) are deliberately generic, not the business's products: \
that is the point of the film. Don't mark them down for it. Do mark it down if the product changes \
between the fix and the payoff."""


def review(mp4: str, b: dict, f: dict, profile: dict) -> dict:
    prod = profile["products"][f["product"]]["name"] if f["product"] >= 0 else "none"
    raw = m.ask_video(REVIEW_PROMPT.format(
        name=profile["name"], not_x=b["thesis"]["not_x"], is_y=b["thesis"]["is_y"], question=b["question"],
        products=json.dumps([p["name"] for p in profile["products"]]), product=prod, before=f["wardrobe"]),
        mp4, schema=REVIEW_SCHEMA, effort="medium", max_tokens=5000)
    return json.loads(raw)


# --- 6. the whole campaign ---------------------------------------------------------

FILM_ROUNDS, GOOD_ENOUGH = 2, 7


def shoot_beats(f: dict, cast: str, ref, profile: dict, where: Path) -> list[dict]:
    fixed_from = 2  # failure, face: before; fix, payoff: with the product

    def beat(k_b: tuple[int, dict]) -> dict:
        k, bt = k_b
        with_product = k >= fixed_from and f["product"] >= 0
        wardrobe = (f"Now {_wearing(f, profile)[:-2]}." if with_product and f["how"] == "worn"
                    else f"Wearing {f['wardrobe']}." + (f" {_wearing(f, profile, True)}" if with_product else ""))
        prompt = BEAT_SHOT.format(
            action=bt["action"], wardrobe=wardrobe, setting=f["setting"], framing=FRAMINGS[bt["framing"]],
            glance=(", except at the very end they glance straight into the lens with a wry half smile"
                    if bt["role"] == "payoff" else ""),
            catchlights=("Two small bright pinpoint reflections in the eyes as catchlights, no light "
                         "fixture visible, nothing crossing the face. " if "close" in bt["framing"] else ""))
        refs = [cast] + ([ref(f["product"])] if with_product else [])
        return _shoot_checked(prompt, refs, where / f"beat{k + 1}.png", f'{bt["action"]} ({bt["framing"]})',
                              ref(f["product"]) if with_product else None)
    with ThreadPoolExecutor(max_workers=4) as pool:
        return list(pool.map(beat, enumerate(f["beats"])))


FILM_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["beats", "caption", "title"],
               "properties": {"beats": {"type": "array", "items": BEAT_ITEM}, "caption": {"type": "string"},
                              "title": {"type": "string"}}}

REVISE_PROMPT = """You are revising a four-beat film for {name}. The creative director watched the \
cut and wants these fixes: {fixes}

Rewrite the beats (and the caption and title if needed). Keep the same person ({who}), the same \
setting ({setting}), the same before-wardrobe ({wardrobe}) and the same product, because the cast \
is already shot. Roles stay in order: failure, face, fix, payoff. Follow the framework:

{framework}

The film now: {film}"""


def revise_film(b: dict, f: dict, fixes: list[str], profile: dict) -> dict:
    raw = m.ask(REVISE_PROMPT.format(name=profile["name"], fixes=json.dumps(fixes), who=f["who"],
                                     setting=f["setting"], wardrobe=f["wardrobe"], framework=framework(),
                                     film=json.dumps({k: f[k] for k in ("title", "beats", "caption")})),
                schema=FILM_SCHEMA, effort="medium", max_tokens=6000)
    new = tidy_all(json.loads(raw))
    if [x["role"] for x in new["beats"]] != ["failure", "face", "fix", "payoff"]:
        return f
    return {**f, **new}


def make(profile: dict, shots: list[Shot], direction: dict, out: Path, url: str) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    by_name = {s.product: s for s in shots if s.portrait}
    b = brief(profile, usable={i for i, p in enumerate(profile["products"]) if p["name"] in by_name})
    (out / "brief.json").write_text(json.dumps(b, indent=1))

    def ref(i: int) -> str | None:
        if i < 0:
            return None
        s = by_name.get(profile["products"][i]["name"])
        return s.portrait if s else None
    for item in [*b["posters"], b["deprivation"], b["film"]]:
        if item["product"] >= 0 and not ref(item["product"]):  # no studio shot of it: don't fake it
            item["product"], item["how"] = -1, "none"
    light = direction["photo"].split(",")[0]
    link = short_link(url)

    # Posters, the deprivation still and the film's cast reference are independent.
    jobs = {}
    for k, p in enumerate(b["posters"]):
        jobs[f"poster{k + 1}"] = (
            POSTER_SHOT.format(who=p["who"], wearing=_wearing(p, profile), setting=p["setting"],
                               props=p["props"], expression=p["expression"], light=light),
            [r for r in [ref(p["product"])] if r],
            f'{p["who"]}, {p["discipline"]}, fist against the chin, looking into the lens', ref(p["product"]))
    dp = b["deprivation"]
    jobs["deprivation"] = (DEPRIVATION_SHOT.format(scene=dp["scene"], furniture=dp["furniture"],
                                                   wearing=_wearing(dp, profile, True)),
                           [r for r in [ref(dp["product"])] if r], dp["scene"], ref(dp["product"]))
    f = b["film"]
    jobs["cast"] = (CAST_SHOT.format(who=f["who"], wardrobe=f["wardrobe"]), [],
                    f'a full-length reference photo of {f["who"]}', None)
    with ThreadPoolExecutor(max_workers=4) as pool:
        shot = dict(zip(jobs, pool.map(lambda kv: _shoot_checked(kv[1][0], kv[1][1], out / f"{kv[0]}.png",
                                                                   kv[1][2], kv[1][3]), jobs.items())))

    # Lettering is patched, never reshot (that would trade an approved cast for a dice roll).
    def clean(name: str, s: dict, where: Path) -> Path:
        return patch(Path(s["path"]), [x for x in s["check"]["lettering"] if x["kind"] == "garbled"],
                     where / f"{name}_clean.png")
    for name in [*(f"poster{k + 1}" for k in range(len(b["posters"]))), "deprivation"]:
        shot[name]["clean"] = clean(name, shot[name], out)

    q = b["question"]
    pages = [poster_page(shot[f"poster{k + 1}"]["clean"], p, q, link, direction, out / f"poster{k + 1}_final.png")
             for k, p in enumerate(b["posters"])]
    pages.append(deprivation_page(shot["deprivation"]["clean"], dp["line"], q, link, direction,
                                  out / "deprivation_final.png"))
    pages.append(endcard_page(q, link, direction, out / "endcard.png"))
    typeset.render(pages)
    for p in [*(out / f"poster{k + 1}_final.png" for k in range(len(b["posters"]))), out / "deprivation_final.png"]:
        Image.open(p).convert("RGB").save(p.with_suffix(".jpg"), quality=90)

    # The film: every beat is shot from the one cast reference (and the product photo from
    # the fix onward), so the person stays the same across cuts. If Spark's review is weak,
    # the beats are rewritten from its notes and reshot once, on the same cast.
    cast = shot["cast"]["path"]
    cuts = []
    for r in range(FILM_ROUNDS):
        where = out / f"film{r + 1}"
        where.mkdir(exist_ok=True)
        beats = shoot_beats(f, cast, ref, profile, where)
        for k, s_ in enumerate(beats):
            s_["clean"] = clean(f"beat{k + 1}", s_, where)
        typeset.render([caption_page(bt["caption"], direction, where / f"cap{k + 1}.png")
                        for k, bt in enumerate(f["beats"])])
        film = cut_film([s_["clean"] for s_ in beats], [where / f"cap{k + 1}.png" for k in range(len(beats))],
                        out / "endcard.png", where)
        film["review"] = review(film["mp4"], b, f, profile)
        cuts.append({"film": film, "spec": f, "beats": beats})
        if film["review"]["overall"] >= GOOD_ENOUGH or r == FILM_ROUNDS - 1:
            break
        f = revise_film(b, f, film["review"]["fixes"], profile)
    best = max(cuts, key=lambda c: c["film"]["review"]["overall"])
    film, f, beats = best["film"], best["spec"], best["beats"]
    film["rounds"] = [c["film"]["review"]["overall"] for c in cuts]

    def disclose(caption: str) -> str:  # realistic AI people: the platforms' label
        return caption if "made with ai" in caption.lower() else caption.rstrip() + "\n\nMade with AI"
    pieces = [{"kind": "poster", "persona": p["persona"], "headline": p["headline"].replace("|", " "),
               "body": p["body"], "caption": disclose(p["caption"]),
               "image": str(out / f"poster{k + 1}_final.jpg"), "raw": shot[f"poster{k + 1}"]["path"],
               "check": shot[f"poster{k + 1}"]["check"], "takes": shot[f"poster{k + 1}"]["takes"],
               "product": profile["products"][p["product"]]["name"] if p["product"] >= 0 else None}
              for k, p in enumerate(b["posters"])]
    pieces.append({"kind": "deprivation", "persona": "deprivation", "headline": dp["line"], "body": "",
                   "caption": dp["caption"], "image": str(out / "deprivation_final.jpg"),
                   "raw": shot["deprivation"]["path"], "check": shot["deprivation"]["check"],
                   "takes": shot["deprivation"]["takes"],
                   "product": profile["products"][dp["product"]]["name"] if dp["product"] >= 0 else None})
    result = {"question": q, "thesis": b["thesis"], "gate": b["gate"], "hashtags": b["hashtags"],
              "pieces": pieces,
              "film": {**film, "title": f["title"], "caption": disclose(f["caption"]), "sound": f["sound"],
                       "cast": cast, "beats": [{**bt, "image": str(s["clean"]), "check": s["check"],
                                                "takes": s["takes"]} for bt, s in zip(f["beats"], beats)],
                       "product": profile["products"][f["product"]]["name"] if f["product"] >= 0 else None}}
    (out / "campaign.json").write_text(json.dumps(result, indent=1, default=str))
    return result
