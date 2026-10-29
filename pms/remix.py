"""Remix a hit: popular posts, reverse engineered, rebuilt for this business.

The method is evidence first, the way you'd reverse engineer anything:

1. Extract. A post that's working is taken apart into its essence: the hook
   pattern, the beats, how long each holds, how the camera moves, how text sits,
   what the sound does, and why it works. What belongs to the original creator
   (their face, words, audio, outfit) is listed as "drop". Muse Spark watches the
   post; Muse Voice Transcribe hears any spoken words so the script's shape is
   captured too. Every spec lands in inspo/social/formats/, so the library grows
   and future makeovers have examples to build from.
2. Ground. Spark rebuilds the essence with only this business's material: their
   products, prices exactly as listed, their town, the new studio photos and the
   remade logo. Code checks every price on screen against the profile.
3. Shoot. A format that needs an angle the studio didn't take (a flat lay, a
   hanger shot) gets it from Muse Image, editing the reshot photo so the product
   stays identical.
4. Cut. Frames are drawn here and piped to ffmpeg: punch-ins on the beat, whip
   pans, slow pushes on texture, platform-native text. Sound is chosen in the
   app, from the platform's licensed library, so the file ships silent with a
   suggestion.
5. Review. Spark watches the cut against the spec (did it keep the essence, is
   everything on screen true) and one revision follows its notes if it's weak.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import textwrap
from concurrent.futures import ThreadPoolExecutor
from datetime import date
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from muse import client as m

from .photos import Shot
from .social import _hex, cover, load_font
from .text import tidy_all

LIBRARY = Path(__file__).resolve().parent.parent / "inspo" / "social" / "formats"
W, H, FPS = 1080, 1920, 30
SAFE_RIGHT = 170  # TikTok/Reels buttons
GOOD_ENOUGH = 7
MAX_ANGLES = 3
SHOTS = ["hero", "detail", "angle", "price_card", "text_card", "logo"]
MOTIONS = ["punch", "push", "whip", "pan", "cut", "hold", "drift", "dissolve"]
STYLES = ["native", "label", "headline", "campaign"]
DISSOLVE_S = 0.7

# --- 1. extract -------------------------------------------------------------------

BEAT = {
    "type": "object", "additionalProperties": False,
    "required": ["role", "shot", "seconds", "motion", "text"],
    "properties": {
        "role": {"type": "string", "enum": ["hook", "build", "payoff", "cta"]},
        "shot": {"type": "string", "enum": SHOTS,
                 "description": "hero: the product whole; detail: a close-up; angle: a different "
                                "camera set-up; price_card/text_card: a full-frame type card; logo: "
                                "the brand landing frame"},
        "seconds": {"type": "number"},
        "motion": {"type": "string", "enum": MOTIONS},
        "text": {"type": "string", "description": "on-screen text as a pattern with {slots}, or ''"},
    },
}

FORMAT_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["name", "seen_on", "essence", "why_it_works", "hook", "beats", "text_style",
                 "look", "people", "sound", "voiceover", "needs", "keep", "drop"],
    "properties": {
        "name": {"type": "string", "description": "a short generic name for the format"},
        "seen_on": {"type": "array", "items": {"type": "string"}},
        "essence": {"type": "string", "description": "one sentence: the transferable idea"},
        "why_it_works": {"type": "array", "items": {"type": "string"}},
        "hook": {"type": "object", "additionalProperties": False,
                 "required": ["pattern", "on_screen", "first_frame"],
                 "properties": {"pattern": {"type": "string"}, "on_screen": {"type": "boolean"},
                                "first_frame": {"type": "string"}}},
        "beats": {"type": "array", "items": BEAT},
        "text_style": {"type": "string", "enum": STYLES,
                       "description": "native: platform-style caption boxes; label: small tracked "
                                      "caps; headline: big display type; campaign: sparse centred "
                                      "serif, like a luxury commercial"},
        "people": {"type": "boolean",
                   "description": "true if the format needs a person wearing or using the product"},
        "look": {"type": "string", "enum": ["clean", "film"],
                 "description": "film: letterboxed, graded, grain, like a cinema commercial"},
        "sound": {"type": "string", "description": "what the sound does, generically (no track names)"},
        "voiceover": {"type": "boolean"},
        "needs": {"type": "array", "items": {"type": "string"},
                  "description": "what a business must truly have to use this format"},
        "keep": {"type": "array", "items": {"type": "string"}},
        "drop": {"type": "array", "items": {"type": "string"},
                 "description": "everything specific to the original creator"},
    },
}

EXTRACT_PROMPT = """Reverse engineer this social post. Work from evidence: what is actually on \
screen, frame by frame, and what is heard. Then abstract it into a reusable FORMAT any business \
could use: the hook as a pattern with {{slots}}, each beat (shot type, seconds, camera motion, \
on-screen text pattern), the text style, what the sound does, and why it works.

Separate essence from instance. "keep" is what makes it work. "drop" is everything that \
belongs to the original creator: their face, name, words, audio, outfit, location, jokes. \
Never copy the creator's words; write patterns.
{speech}"""


def library() -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted(LIBRARY.glob("*.json"))]


def _has_audio(video: Path) -> bool:
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                        "stream=index", "-of", "csv=p=0", str(video)], capture_output=True, text=True)
    return bool(r.stdout.strip())


def extract(post: Path, out: Path) -> dict:
    """A post (video or image) to a format spec, saved into the library."""
    out.mkdir(parents=True, exist_ok=True)
    is_video = post.suffix.lower() in (".mp4", ".mov", ".webm", ".m4v")
    speech = ""
    if is_video:
        mp4 = out / "post.mp4"  # the Files API wants mp4
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(post), "-t", "90", "-vf",
                        "scale=-2:960", "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac",
                        str(mp4)], check=True)
        if _has_audio(mp4):
            wav = out / "post.wav"
            subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(mp4), "-vn", "-ac", "1",
                            "-ar", "16000", "-c:a", "pcm_s16le", str(wav)], check=True)
            try:
                heard = m.transcribe(wav).get("transcript", "").strip()
            except Exception as e:
                print(f"remix: transcribe failed: {e!r}"[:200])
                heard = ""
            speech = (f'\nMuse Voice Transcribe heard this speech in it: "{heard}". Use it for the '
                      "script's SHAPE (length, rhythm, structure), never its words." if heard
                      else "\nThere is no speech in it; the sound is music or ambience.")
        raw = m.ask_video(EXTRACT_PROMPT.format(speech=speech), mp4, schema=FORMAT_SCHEMA,
                          effort="medium", max_tokens=8000)
    else:
        raw = m.ask(EXTRACT_PROMPT.format(speech="It is a still post (a photo or carousel frame); "
                                          "render it as a short video format with the same idea."),
                    images=[post], schema=FORMAT_SCHEMA, effort="medium", max_tokens=8000)
    spec = json.loads(raw)
    slug = re.sub(r"[^a-z0-9]+", "-", spec["name"].lower()).strip("-")[:40] or "format"
    spec["id"] = f"{slug}-{hashlib.sha1(post.read_bytes()).hexdigest()[:6]}"
    spec["source"] = f"reverse engineered from a post supplied by an owner, {date.today().isoformat()}"
    spec["speech_heard"] = bool(speech and "heard this" in speech)
    LIBRARY.mkdir(parents=True, exist_ok=True)
    (LIBRARY / f"{spec['id']}.json").write_text(json.dumps(spec, indent=1))
    return spec


# --- 2. ground ----------------------------------------------------------------------

PICK_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["picks"],
    "properties": {"picks": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["id", "why"],
        "properties": {"id": {"type": "string"}, "why": {"type": "string"}}}}},
}

PICK_PROMPT = """You run social for a makeover crew. Pick the {n} post formats from this library \
that would work best for this business, best first. Only pick a format if the business truly has \
what it needs (its "needs"): don't pick a price format without a real price.

Business: {profile}

Library: {formats}"""

GROUND_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["title", "hook", "beats", "caption", "hashtags", "sound", "facts_used"],
    "properties": {
        "title": {"type": "string", "description": "a name for this remix, e.g. 'Linen fit check'"},
        "hook": {"type": "string", "description": "the filled hook text"},
        "beats": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["shot", "product", "angle", "seconds", "motion", "text"],
            "properties": {
                "shot": {"type": "string", "enum": SHOTS},
                "product": {"type": "integer", "description": "index into the product photo list"},
                "angle": {"type": "string",
                          "description": "for shot=angle: the new camera set-up, e.g. 'flat lay from "
                                         "directly above on raw linen'; else ''"},
                "seconds": {"type": "number"},
                "motion": {"type": "string", "enum": MOTIONS},
                "text": {"type": "string", "description": "filled on-screen text, or ''"}}}},
        "caption": {"type": "string", "description": "the post caption, in the brand voice"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "sound": {"type": "string", "description": "what kind of sound to pick in the app, generically"},
        "facts_used": {"type": "array", "items": {"type": "string"},
                       "description": "every fact shown, each traceable to the profile"},
    },
}

GROUND_PROMPT = """Rebuild this post format for {name}. Keep the format's ESSENCE and beat \
structure (its keep list); replace everything else with this business's own material.

Format: {spec}

Rules:
- Every fact on screen comes from the profile: product names, prices exactly as written, the \
town, how things are made. Never invent discounts, reviews, numbers, sizes or claims.
- Fill every {{slot}}. "{{where to buy}}" is their real website or shop address.
- Use the product photos by index (index: product): {photos}. For shot=angle, describe a new \
camera set-up for that product that suits the format and the brand's look ({photo_brief}); keep \
to {max_angles} distinct angles at most.
{people}
- On-screen text: short. Native style is lowercase and conversational; label style is a few \
words; headline style is under 6 words.
- {logo}
- Caption in the brand voice ({voice}); at most two emoji; 3 to 6 relevant hashtags.
{fixes}
Profile: {profile}"""


def pick(profile: dict, n: int = 2, prefer: list[str] | None = None) -> list[dict]:
    lib = {f["id"]: f for f in library()}
    chosen = [lib[i] for i in (prefer or []) if i in lib][:n]
    if len(chosen) < n:
        menu = {k: {x: v[x] for x in ("name", "essence", "needs")} for k, v in lib.items()
                if v not in chosen}
        summary = {k: profile[k] for k in ("name", "category", "audience", "products", "location")}
        raw = m.ask(PICK_PROMPT.format(n=n - len(chosen), profile=json.dumps(summary),
                                       formats=json.dumps(menu)), schema=PICK_SCHEMA, effort="low")
        for p in json.loads(raw)["picks"]:
            if p["id"] in lib and lib[p["id"]] not in chosen and len(chosen) < n:
                chosen.append({**lib[p["id"]], "why": p["why"]})
    return chosen


PRICE = re.compile(r"[$£€]\s?\d[\d,]*(?:\.\d{2})?")


def check_prices(g: dict, profile: dict) -> list[str]:
    """Drop any on-screen price that isn't in the profile. Returns what was removed."""
    listed = {re.sub(r"\s", "", x) for p in profile["products"] for x in PRICE.findall(p["price"] or "")}
    removed = []
    for b in g["beats"]:
        for found in PRICE.findall(b["text"]):
            if re.sub(r"\s", "", found) not in listed:
                removed.append(found)
                b["text"] = PRICE.sub("", b["text"]).strip(" ,-·")
    return removed


def ground(spec: dict, profile: dict, shots: list[Shot], direction: dict, has_logo: bool,
           fixes: list[str] | None = None) -> dict:
    facts = {k: profile[k] for k in ("name", "one_liner", "category", "location", "contact",
                                     "products", "value_props")}
    logo = ("The logo frame shows the remade logo mark and the name; its text is where to buy."
            if has_logo else "The logo frame shows the name as a wordmark; its text is where to buy.")
    raw = m.ask(GROUND_PROMPT.format(
        name=profile["name"], spec=json.dumps({k: spec[k] for k in ("name", "essence", "hook", "beats",
                                                                   "text_style", "keep", "drop")}),
        photos=json.dumps({i: s.product for i, s in enumerate(shots)}), photo_brief=direction["photo"],
        max_angles=MAX_ANGLES, logo=logo, voice=", ".join(profile["voice"]["adjectives"]),
        people=("- This format shows a model wearing the product. For shot=angle, describe a "
                "premium location and an elegant pose, e.g. 'walking down sunlit limestone steps "
                "of a Mediterranean hotel, mid-stride'. The model is AI-generated and fictional: "
                "never give them a name or imply a real influencer, and end the caption with "
                "'Made with AI'.") if spec.get("people") else "",
        fixes=("An editor reviewed the last cut. Fix these: " + json.dumps(fixes)) if fixes else "",
        profile=json.dumps(facts)), schema=GROUND_SCHEMA, effort="medium", max_tokens=8000)
    g = tidy_all(json.loads(raw))
    n = max(1, len(shots))
    for b in g["beats"]:
        b["product"] %= n
        b["seconds"] = min(4.0, max(0.35, float(b["seconds"])))
    g["prices_removed"] = check_prices(g, profile)
    if spec.get("people") and "made with ai" not in g["caption"].lower():
        g["caption"] = g["caption"].rstrip() + "\n\nMade with AI"  # the platforms' rule for realistic AI people
    return g


# --- 3. shoot -----------------------------------------------------------------------

WORN = ("An elegant, stylish model wearing this exact {subject}: identical colour, pattern, "
        "fabric, cut, stitching and details, nothing added or changed on it. Setting and pose: "
        "{angle}. Fashion editorial in the style of a premium lifestyle influencer: candid, "
        "relaxed, natural light; the face turned away, in profile or cropped out of frame so "
        "the clothes lead. Light and mood: {photo}. Vertical frame, 50mm lens, shallow depth of "
        "field. Photorealistic, no text, no logos added.")

ANGLE = ("Photograph this exact {subject} again from a new camera set-up: {angle}. Keep the "
         "{subject} itself identical: same shape, colours, pattern, stitching, labels and "
         "proportions. Light and mood: {photo}. Vertical frame, full-frame camera, shallow depth "
         "of field. Photorealistic, no text, no logos added, no people.")


def shoot_angles(g: dict, shots: list[Shot], profile: dict, direction: dict, out: Path,
                 people: bool = False) -> dict:
    """(product, angle) -> image path, made by Muse Image from the reshot portrait."""
    out.mkdir(parents=True, exist_ok=True)
    subjects = {p["name"]: p["subject"] for p in profile["products"]}
    wanted = []
    for b in g["beats"]:
        key = (b["product"], b["angle"].strip())
        if b["shot"] == "angle" and key[1] and key not in wanted:
            wanted.append(key)
    wanted = wanted[:MAX_ANGLES]

    def one(k: int, key: tuple[int, str]) -> tuple[tuple[int, str], str | None]:
        s = shots[key[0]]
        try:
            p = m.edit_image(s.portrait, (WORN if people else ANGLE).format(subject=subjects.get(s.product) or "product",
                                                      angle=key[1], photo=direction["photo"]),
                             out / f"angle_{k}.png", size="1024x1536")
            return key, str(p)
        except Exception as e:
            print(f"remix: angle failed ({key[1]}): {e!r}"[:200])
            return key, None
    with ThreadPoolExecutor(max_workers=3) as pool:
        return {k: v for k, v in pool.map(lambda a: one(*a), enumerate(wanted)) if v}


# --- 4. cut -------------------------------------------------------------------------


def short_link(text: str) -> str:
    """'https://www.shop.com/collections/all' -> 'shop.com': links on screen are read, not clicked."""
    def bare(mt: re.Match) -> str:
        return re.sub(r"^www\.", "", mt.group(1))
    text = re.sub(r"https?://([^/\s]+)\S*", bare, text)
    return re.sub(r"\b((?:[a-z0-9-]+\.)+[a-z]{2,})/\S*", r"\1", text, flags=re.I).strip()


def _ease_out(t: float) -> float:
    return 1 - (1 - t) ** 3


class Cutter:
    def __init__(self, direction: dict, profile: dict, mark: dict | None):
        pal = direction["palette"]
        self.pal = {k: _hex(v) for k, v in pal.items()}
        self.fonts = direction["fonts"]
        self.name = profile["name"]
        self.native = load_font(self.fonts["body"], 56, 600)
        self.label = load_font(self.fonts["body"], 42, 600)
        self.campaign = load_font(self.fonts["display"], 60, 500)
        self.head = load_font(self.fonts["display"], 104, 400)
        self.card_big = load_font(self.fonts["display"], 200, 400)
        self.wordmark = load_font(self.fonts["display"], 88, 400)
        self.mark = Image.open(mark["mark"]).convert("RGBA") if mark else None
        self._base: dict[str, Image.Image] = {}

    def base(self, path: str) -> Image.Image:
        if path not in self._base:
            self._base[path] = cover(Path(path), (int(W * 1.3), int(H * 1.18)))
        return self._base[path]

    def photo(self, path: str, motion: str, t: float, dur: float) -> Image.Image:
        """One frame of a photo beat. t is seconds into the beat."""
        b = self.base(path)
        p = min(1.0, t / max(dur, 0.01))
        pan = 0.5
        if motion == "push":
            z = 1.0 + 0.10 * _ease_out(p)
        elif motion == "punch":  # snaps in on the beat, then breathes
            z = 1.0 + 0.12 * (1 - _ease_out(min(1.0, t / 0.16))) + 0.02 * p
        elif motion == "pan":
            z, pan = 1.04, 0.2 + 0.6 * p
        elif motion in ("drift", "dissolve"):  # slow, cinematic: a gentle push and slide
            z, pan = 1.02 + 0.07 * p, 0.42 + 0.16 * p
        elif motion == "whip":
            z = 1.02 + 0.02 * p
        else:  # cut, hold
            z = 1.0 + 0.012 * p
        cw, ch = W * 1.18 / z, H * 1.18 / z
        cw = min(cw, b.width)
        x = (b.width - cw) * pan
        y = (b.height - ch) / 2
        frame = b.crop((int(x), int(y), int(x + cw), int(y + ch))).resize((W, H), Image.BILINEAR)
        if motion == "whip" and t < 0.2:  # arrives sideways, motion-blurred
            k = 1 - _ease_out(t / 0.2)
            shifted = Image.new("RGB", (W, H))
            shifted.paste(frame, (int(W * 0.5 * k), 0))
            blur = max(1, int(60 * k))
            frame = shifted.resize((max(1, W // blur), H), Image.BILINEAR).resize((W, H), Image.BILINEAR)
        return frame

    def card(self, kind: str, text: str, t: float) -> Image.Image:
        """Full-frame type: a price, a line, or the logo landing frame."""
        on_ink = kind == "price_card"
        bg = self.pal["ink"] if on_ink else self.pal["bg"]
        fg = self.pal["bg"] if on_ink else self.pal["ink"]
        im = Image.new("RGB", (W, H), bg)
        d = ImageDraw.Draw(im)
        rise = int(30 * (1 - _ease_out(min(1.0, t / 0.35))))
        if kind == "logo":
            y = int(H * 0.30) + rise
            if self.mark:
                mk = self.mark.copy()
                mk.thumbnail((int(W * 0.42), int(H * 0.26)))
                tint = Image.new("RGBA", mk.size, (*fg, 255))
                tint.putalpha(mk.getchannel("A"))
                im.paste(tint, ((W - mk.width) // 2, y), tint)
                y += mk.height + 70
            for row in textwrap.wrap(self.name, 16):
                d.text(((W - d.textlength(row, font=self.wordmark)) / 2, y), row, font=self.wordmark, fill=fg)
                y += int(self.wordmark.size * 1.05)
            if text:
                y += 40
                self.tracked(d, short_link(text).upper(), W / 2, y, fg, center=True, fit=W - 140)
            return im
        font = self.card_big if kind == "price_card" and len(text) <= 9 else self.head
        rows = textwrap.wrap(text, 9 if font is self.card_big else 14) or [""]
        lh = int(font.size * 1.02)
        y = (H - lh * len(rows)) // 2 + rise
        for row in rows:
            d.text(((W - d.textlength(row, font=font)) / 2, y), row, font=font, fill=fg)
            y += lh
        return im

    def tracked(self, d: ImageDraw.ImageDraw, text: str, x: float, y: float, fill, center=False,
                font: ImageFont.FreeTypeFont | None = None, track: float = 0.16,
                fit: float | None = None) -> None:
        font = font or self.label
        gap = font.size * track
        width = sum(d.textlength(c, font=font) + gap for c in text) - gap
        while fit and width > fit and font.size > 18:  # shrink to fit rather than run off the frame
            font = font.font_variant(size=font.size - 2)
            gap = font.size * track
            width = sum(d.textlength(c, font=font) + gap for c in text) - gap
        x = x - width / 2 if center else x
        for c in text:
            d.text((x, y), c, font=font, fill=fill)
            x += d.textlength(c, font=font) + gap

    def ink_for(self, im: Image.Image, box: tuple[int, int, int, int]):
        """White type on dark ground, the brand's ink on light ground: always legible."""
        lum = float(np.asarray(im.crop(box).convert("L")).mean())
        return ((255, 255, 255), (0, 0, 0)) if lum < 150 else (self.pal["ink"], (255, 255, 255))

    def text(self, im: Image.Image, text: str, style: str, t: float) -> None:
        if not text:
            return
        a = min(1.0, t / 0.15)
        rise = int(18 * (1 - _ease_out(min(1.0, t / 0.25))))
        d = ImageDraw.Draw(im, "RGBA")
        if style == "native":  # the platform's own caption look: white boxes, black type
            rows = textwrap.wrap(text, 22)
            lh = int(self.native.size * 1.32)
            y = int(H * 0.27) - (lh * len(rows)) // 2 + rise
            cx = (W - SAFE_RIGHT + 60) / 2
            for row in rows:
                w = d.textlength(row, font=self.native)
                d.rounded_rectangle((cx - w / 2 - 22, y - 8, cx + w / 2 + 22, y + lh - 6), 14,
                                    fill=(255, 255, 255, int(255 * a)))
                d.text((cx - w / 2, y + 4), row, font=self.native, fill=(16, 16, 16, int(255 * a)))
                y += lh
        elif style == "label":
            y = int(H * 0.66) + rise
            fg, shadow = self.ink_for(im, (60, y - 50, W - SAFE_RIGHT, y + 140))
            d.rectangle((80, y - 34, 140, y - 31), fill=(*fg, int(230 * a)))
            for row in textwrap.wrap(short_link(text).upper(), 26)[:2]:
                self.tracked(d, row, 82, y + 2, (*shadow, int(70 * a)), fit=W - SAFE_RIGHT - 100)
                self.tracked(d, row, 80, y, (*fg, int(255 * a)), fit=W - SAFE_RIGHT - 100)
                y += int(self.label.size * 1.5)
        elif style == "campaign":  # a luxury commercial: the words sit in the letterbox bar
            a = min(1.0, t / 0.6)
            row = short_link(text).upper()
            bar = int(H * Film.BARS)
            y = H - bar + (bar - self.campaign.size) // 2 - 6
            self.tracked(d, row, W / 2, y, (255, 255, 255, int(255 * a)), center=True,
                         font=self.campaign, track=0.2, fit=W - 140)
        else:  # headline: display type over a soft floor of shade
            shade = Image.new("L", (1, 256))
            shade.putdata([int(150 * a * max(0.0, (i - 96) / 160)) for i in range(256)])
            im.paste((0, 0, 0), (0, 0, W, H), shade.resize((W, H)))
            d = ImageDraw.Draw(im, "RGBA")
            rows = textwrap.wrap(text, 16)[:3]
            lh = int(self.head.size * 1.0)
            y = int(H * 0.70) - lh * len(rows) + rise
            for row in rows:
                d.text((80, y), row, font=self.head, fill=(255, 255, 255, int(255 * a)))
                y += lh


class Film:
    """The commercial look: a warm-and-deep grade, vignette, moving grain, letterbox bars."""
    BARS = 0.11

    def __init__(self, bars: float = BARS):
        yy, xx = np.mgrid[0:H, 0:W]
        r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
        self.vignette = np.clip(1.08 - 0.32 * r ** 2, 0.55, 1.0)[..., None]
        rng = np.random.default_rng(7)
        self.grain = [rng.normal(0, 5, (H, W, 1)) for _ in range(4)]
        self.bar = int(H * bars)

    def grade(self, im: Image.Image, f: int) -> Image.Image:
        a = np.asarray(im).astype(np.float32)
        lum = a.mean(axis=2, keepdims=True) / 255
        # Shadows lean cool, highlights warm; a touch of contrast; then light falloff and grain.
        a = a + (lum - 0.5) * np.array([14, 2, -14], dtype=np.float32)
        a = (a - 128) * 1.06 + 128
        a = a * self.vignette + self.grain[f % 4]
        a[:self.bar] = 0
        a[-self.bar:] = 0
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def render(g: dict, spec: dict, shots: list[Shot], angles: dict, direction: dict, profile: dict,
           mark: dict | None, out: Path) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    c = Cutter(direction, profile, mark)
    style = spec.get("text_style", "native")

    def source(b: dict) -> str | None:
        s = shots[b["product"]]
        if b["shot"] == "hero":
            return s.portrait
        if b["shot"] == "detail":
            return s.detail or s.portrait
        if b["shot"] == "angle":
            return angles.get((b["product"], b["angle"].strip())) or s.detail or s.portrait
        return None
    beats = [{**b, "src": source(b)} for b in g["beats"]]
    film = Film() if spec.get("look") == "film" else None
    total = sum(b["seconds"] for b in beats)
    mp4 = out / "remix.mp4"
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "25" if film else "20", "-pix_fmt", "yuv420p",
         "-maxrate", "8M", "-bufsize", "16M",  # grain is expensive to encode; keep files postable
         "-c:a", "aac", "-t", f"{total:.3f}", "-movflags", "+faststart", str(mp4)],
        stdin=subprocess.PIPE)
    timeline, t0 = [], 0.0
    poster, last = None, None
    for k, b in enumerate(beats):
        n = max(1, round(b["seconds"] * FPS))
        timeline.append({"start_s": round(t0, 2), "seconds": b["seconds"], "shot": b["shot"],
                         "motion": b["motion"], "text": b["text"]})
        for f in range(n):
            t = f / FPS
            if b["src"]:
                frame = c.photo(b["src"], b["motion"], t, b["seconds"])
                if film:
                    frame = film.grade(frame, f)
                c.text(frame, b["text"], style, t)  # after the grade, so bar text survives it
            else:
                frame = c.card(b["shot"], b["text"], t)
                if film:
                    frame = film.grade(frame, f)
            if b["motion"] == "dissolve" and last is not None and t < DISSOLVE_S:
                frame = Image.blend(last, frame, _ease_out(t / DISSOLVE_S))
            if poster is None and k == 0 and t >= min(0.6, b["seconds"] / 2):
                poster = frame.copy()
            ff.stdin.write(frame.tobytes())
        last = frame
        t0 += n / FPS
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg failed to encode the remix")
    poster_path = out / "poster.jpg"
    (poster or frame).save(poster_path, quality=86)
    return {"mp4": str(mp4), "poster": str(poster_path), "duration_s": round(total, 1),
            "timeline": timeline}


# --- 5. review ----------------------------------------------------------------------

REVIEW_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["essence", "hook", "pacing", "legibility", "grounded", "overall", "verdict", "fixes"],
    "properties": {
        **{k: {"type": "integer", "description": "1-10"} for k in
           ("essence", "hook", "pacing", "legibility", "grounded", "overall")},
        "verdict": {"type": "string", "description": "two sentences to the owner"},
        "fixes": {"type": "array", "items": {"type": "string"}, "description": "up to 3 concrete changes"},
    },
}

REVIEW_PROMPT = """You are a short-form editor. This 9:16 video for {name} ({category}) is a \
remix of a popular format. Watch it against the format spec and score 1-10: essence (does it \
keep what makes the format work?), hook (does the first second stop the scroll?), pacing, \
legibility on a phone, grounded (is everything on screen true to these facts: {facts}?), and \
overall. The file is silent on purpose: sound is picked in the app from the platform's licensed \
library ({sound}), so don't mark it down for silence. Be honest; a 10 is rare.

Format spec: {spec}"""


def review(mp4: str, spec: dict, g: dict, profile: dict) -> dict:
    facts = {k: profile[k] for k in ("products", "location", "contact")}
    raw = m.ask_video(REVIEW_PROMPT.format(
        name=profile["name"], category=profile["category"], facts=json.dumps(facts), sound=g["sound"],
        spec=json.dumps({k: spec[k] for k in ("name", "essence", "keep", "beats")})),
        mp4, schema=REVIEW_SCHEMA, effort="medium", max_tokens=6000)
    return json.loads(raw)


def make_one(spec: dict, profile: dict, shots: list[Shot], direction: dict, mark: dict | None,
             out: Path, rounds: int = 2) -> dict:
    cuts, fixes, angles = [], None, {}
    for r in range(rounds):
        g = ground(spec, profile, shots, direction, bool(mark), fixes)
        new = {k for k in ((b["product"], b["angle"].strip()) for b in g["beats"] if b["shot"] == "angle")
               if k not in angles}
        if new:
            angles.update(shoot_angles({"beats": [b for b in g["beats"]
                                                  if (b["product"], b["angle"].strip()) in new]},
                                       shots, profile, direction, out / f"angles{r + 1}",
                                       people=bool(spec.get("people"))))
        res = render(g, spec, shots, angles, direction, profile, mark, out / f"cut{r + 1}")
        rv = review(res["mp4"], spec, g, profile)
        cuts.append({"grounded": g, "render": res, "review": rv})
        if rv["overall"] >= GOOD_ENOUGH:
            break
        fixes = rv["fixes"]
    best = max(cuts, key=lambda x: x["review"]["overall"])
    return {"format": spec, "best": best, "cuts": cuts,
            "angles": [{"product": k[0], "angle": k[1], "image": v} for k, v in angles.items()]}


def make(profile: dict, shots: list[Shot], direction: dict, mark: dict | None, out: Path,
         prefer: list[str] | None = None, n: int = 2) -> list[dict]:
    specs = pick(profile, n, prefer)
    with ThreadPoolExecutor(max_workers=n) as pool:
        return list(pool.map(lambda kv: make_one(kv[1], profile, shots, direction, mark,
                                                 out / f"{kv[0] + 1}-{kv[1]['id']}"), enumerate(specs)))
