"""The short video: 9:16, 15-20 seconds, voiced, captioned, reviewed.

1. Voiceover, one line at a time. Meta has no text-to-speech model, so this uses
   ElevenLabs when ELEVENLABS_API_KEY is set, else the Mac's own voice (local
   demos only). Lines are joined with short pauses.
2. Muse Voice Transcribe listens to every line and we check what it heard
   against the script. A line it can't follow (a mumbled name, a misread
   price) is voiced again, then flagged if it still fails, so a garbled read
   never reaches the owner. Timing comes from the lines themselves: each is
   synthesised separately, so where it starts and ends is known exactly. The
   checked text becomes the .srt captions file too.
3. Frames are drawn in Python and piped to ffmpeg with the voice. Each shot
   gets depth: SAM 3.1 lifts the product off its background, and in the push-in
   the product travels toward the camera faster than the set behind it
   (parallax), which reads as motion rather than a slideshow. Then a hook
   title, captions that light up word by word, and an end card.
4. Muse Spark watches the finished video and reviews it like a social editor:
   hook, pacing, legibility, brand fit, and what to change.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import subprocess
import tempfile
import textwrap
from pathlib import Path

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFilter

from muse import client as m

from .photos import Shot, find
from .social import _hex, cover, load_font

W, H, FPS = 1080, 1920, 30
GAP_S = 0.35  # silence between voiceover lines
MIN_MATCH = 0.8  # share of script words Transcribe must hear in a line
CAPTION_WORDS = 6  # most words on screen at once
GOOD_ENOUGH = 7  # Spark's overall score that ends the revision loop
LEAD_S = 0.6  # before the first word
END_S = 2.6  # end card
FADE_S = 0.3


# --- 1. voice ---------------------------------------------------------------------


def tts_line(text: str, out: Path) -> Path:
    """One line to a mono 24 kHz WAV."""
    key = os.getenv("ELEVENLABS_API_KEY", "").strip()
    raw = out.with_suffix(".src")
    if key:
        voice = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM")
        r = requests.post(f"https://api.elevenlabs.io/v1/text-to-speech/{voice}",
                          headers={"xi-api-key": key, "accept": "audio/mpeg"},
                          json={"text": text, "model_id": "eleven_multilingual_v2"}, timeout=60)
        r.raise_for_status()
        raw.write_bytes(r.content)
    else:
        subprocess.run(["say", "-v", os.getenv("PMS_SAY_VOICE", "Samantha"), "-o",
                        str(raw.with_suffix(".aiff")), text], check=True)
        raw = raw.with_suffix(".aiff")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(raw), "-ac", "1", "-ar", "24000",
                    "-c:a", "pcm_s16le", str(out)], check=True)
    raw.unlink(missing_ok=True)
    return out


def wav_seconds(path: Path) -> float:
    import wave
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def checked_line(text: str, out: Path) -> tuple[Path, float, str]:
    """Voice a line, have Transcribe listen, retry once if it doesn't match."""
    for _ in range(2):
        tts_line(text, out)
        heard = m.transcribe(out).get("transcript", "")
        score = word_accuracy([text], heard)
        if score >= MIN_MATCH:
            break
    return out, score, heard


def voiceover(lines: list[str], out: Path) -> tuple[Path, list[dict]]:
    """The joined voiceover, plus per line: start/end seconds, what Transcribe heard."""
    from concurrent.futures import ThreadPoolExecutor
    tmp = Path(tempfile.mkdtemp(prefix="vo_", dir=out.parent))
    with ThreadPoolExecutor(4) as pool:
        checked = list(pool.map(lambda it: checked_line(it[1], tmp / f"{it[0]:02d}.wav"),
                                enumerate(lines)))
    parts = [c[0] for c in checked]
    info, t = [], 0.0
    for (path, score, heard), text in zip(checked, lines):
        d = wav_seconds(path)
        info.append({"say": text, "start": t, "end": t + d, "heard": heard, "match": score})
        t += d + GAP_S
    silence = tmp / "gap.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i",
                    f"anullsrc=r=24000:cl=mono", "-t", str(GAP_S), "-c:a", "pcm_s16le", str(silence)],
                   check=True)
    lst = tmp / "list.txt"
    seq = []
    for p in parts:
        seq += [p, silence]
    lst.write_text("".join(f"file '{p.resolve()}'\n" for p in seq))
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c:a", "pcm_s16le", str(out)], check=True)
    for p in tmp.iterdir():
        p.unlink()
    tmp.rmdir()
    return out, info


def srt(info: list[dict], offset: float) -> str:
    def ts(x: float) -> str:
        ms = int(round(x * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    return "\n".join(f"{i + 1}\n{ts(x['start'] + offset)} --> {ts(x['end'] + offset)}\n{x['say']}\n"
                     for i, x in enumerate(info))


# --- 2. timing from Muse Voice Transcribe ------------------------------------------


def _words(s: str) -> list[str]:
    return re.findall(r"[a-z0-9']+", s.lower())


def word_accuracy(script: list[str], transcript: str) -> float:
    """Share of script words heard, in order (a light check, not WER)."""
    want, heard = _words(" ".join(script)), _words(transcript)
    j = hits = 0
    for w in want:
        k = j
        while k < len(heard) and heard[k] != w and k < j + 4:
            k += 1
        if k < len(heard) and heard[k] == w:
            hits, j = hits + 1, k + 1
    return round(hits / max(1, len(want)), 2)


# --- 3. frames ---------------------------------------------------------------------


def _ease(t: float) -> float:
    return t * t * (3 - 2 * t)


class Renderer:
    def __init__(self, direction: dict, name: str):
        self.d, self.name = direction, name
        pal = direction["palette"]
        self.bg, self.ink, self.accent = _hex(pal["bg"]), _hex(pal["ink"]), _hex(pal["accent"])
        self.cap = load_font(direction["fonts"]["body"], 62, 700)
        self.hook = load_font(direction["fonts"]["display"], 104, 700)
        self.big = load_font(direction["fonts"]["display"], 96, 700)
        self.small = load_font(direction["fonts"]["body"], 40, 500)
        self._base: dict[str, Image.Image] = {}
        self._fg: dict[str, tuple[Image.Image, tuple[float, float]] | None] = {}

    def base(self, path: str) -> Image.Image:
        if path not in self._base:
            self._base[path] = cover(Path(path), (int(W * 1.16), int(H * 1.16)))
        return self._base[path]

    def lift(self, path: str, subject: str) -> None:
        """SAM 3.1 finds the product in the shot; keep it as its own feathered layer."""
        if path in self._fg:
            return
        b = self.base(path)
        tmp = Path(path).with_suffix(".sam.jpg")
        b.save(tmp, quality=90)
        try:
            seg, mask = asyncio.run(find(subject, tmp))
        except Exception as e:
            print(f"parallax: SAM failed on {Path(path).name}: {e!r}"[:200])
            seg, mask = None, None
        tmp.unlink(missing_ok=True)
        if seg is None or (seg.confidence or 0) < 0.5 or not 0.03 < mask.mean() < 0.7:
            self._fg[path] = None  # nothing clean to lift: plain push-in
            return
        alpha = Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(3))
        layer = b.convert("RGBA")
        layer.putalpha(alpha)
        ys, xs = np.nonzero(mask)
        self._fg[path] = (layer, (xs.mean() / b.width, ys.mean() / b.height))

    def shot(self, path: str, t: float, k: int) -> Image.Image:
        """Push-in, alternating drift per shot. With a lifted product, the set moves
        slowly and the product comes forward faster: parallax."""
        b = self.base(path)
        e = _ease(min(1.0, max(0.0, t)))
        fg = self._fg.get(path)
        if not fg:
            z = 1.16 - 0.12 * e
            cw, ch = int(W * z), int(H * z)
            dx = (b.width - cw) * (0.5 + (0.25 if k % 2 else -0.25) * e)
            dy = (b.height - ch) * 0.5
            return b.crop((int(dx), int(dy), int(dx) + cw, int(dy) + ch)).resize((W, H), Image.BILINEAR)
        layer, (cx, cy) = fg

        def window(z: float, drift: float) -> tuple[int, int, int, int]:
            cw, ch = W * z, H * z
            x = min(max(cx * b.width - cw / 2 + drift, 0), b.width - cw)
            y = min(max(cy * b.height - ch / 2, 0), b.height - ch)
            return int(x), int(y), int(x + cw), int(y + ch)
        side = 1 if k % 2 else -1
        back = b.crop(window(1.16 - 0.06 * e, side * 40 * e)).resize((W, H), Image.BILINEAR)
        front = layer.crop(window(1.16 - 0.20 * e, side * 70 * e)).resize((W, H), Image.BILINEAR)
        back.paste(front, (0, 0), front)
        return back

    def caption(self, im: Image.Image, text: str, progress: float) -> None:
        """Up to 6 words at a time, words already spoken in the accent colour. Sits
        above the bottom third, where TikTok and Reels put their buttons."""
        all_words = text.split()
        n_chunks = max(1, -(-len(all_words) // CAPTION_WORDS))
        size = -(-len(all_words) // n_chunks)
        spoken = progress * len(all_words)
        c = min(n_chunks - 1, int(spoken // size))
        words = all_words[c * size:(c + 1) * size]
        lit = int(round(spoken - c * size))
        text = " ".join(words)
        rows = textwrap.wrap(text, 20)
        draw = ImageDraw.Draw(im, "RGBA")
        lh = int(self.cap.size * 1.25)
        y0 = int(H * 0.56) - (len(rows) * lh) // 2
        draw.rounded_rectangle((60, y0 - 34, W - 60, y0 + len(rows) * lh + 24), 36, fill=(0, 0, 0, 120))
        i = 0
        for r, row in enumerate(rows):
            x = (W - draw.textlength(row, font=self.cap)) / 2
            for word in row.split():
                colour = self.accent if i < lit else (255, 255, 255)
                draw.text((x, y0 + r * lh), word, font=self.cap, fill=colour,
                          stroke_width=3, stroke_fill=(0, 0, 0))
                x += draw.textlength(word + " ", font=self.cap)
                i += 1

    def hook_title(self, im: Image.Image, text: str, alpha: float) -> None:
        draw = ImageDraw.Draw(im, "RGBA")
        rows = textwrap.wrap(text, 14)
        lh = int(self.hook.size * 1.1)
        y = int(H * 0.16)
        pad = 50
        draw.rectangle((0, y - pad, W, y + len(rows) * lh + pad), fill=(*self.bg, int(230 * alpha)))
        for r, row in enumerate(rows):
            x = (W - draw.textlength(row, font=self.hook)) / 2
            draw.text((x, y + r * lh), row, font=self.hook, fill=(*self.ink, int(255 * alpha)))

    def end_card(self, line: str, contact: str) -> Image.Image:
        im = Image.new("RGB", (W, H), self.bg)
        draw = ImageDraw.Draw(im)
        rows = textwrap.wrap(self.name, 14)
        y = int(H * 0.36)
        for row in rows:
            draw.text(((W - draw.textlength(row, font=self.big)) / 2, y), row, font=self.big, fill=self.ink)
            y += int(self.big.size * 1.1)
        draw.rectangle((W / 2 - 60, y + 30, W / 2 + 60, y + 38), fill=self.accent)
        y += 90
        for row in textwrap.wrap(line, 28):
            draw.text(((W - draw.textlength(row, font=self.small)) / 2, y), row, font=self.small, fill=self.ink)
            y += 56
        y += 30
        for row in textwrap.wrap(contact, 34):
            draw.text(((W - draw.textlength(row, font=self.small)) / 2, y), row, font=self.small,
                      fill=_hex(self.d["palette"]["muted"]))
            y += 52
        return im


def render(plan: dict, shots: list[Shot], direction: dict, profile: dict, out: Path) -> dict:
    """The whole video. Returns timings, the transcript check and file paths."""
    out.mkdir(parents=True, exist_ok=True)
    video = plan["video"]
    lines = [ln for ln in video["lines"] if 0 <= ln["photo"] < len(shots)]
    script = [ln["say"] for ln in lines]
    wav, info = voiceover(script, out / "voiceover.wav")
    (out / "captions.srt").write_text(srt(info, LEAD_S))
    accuracy = round(sum(x["match"] for x in info) / max(1, len(info)), 2)

    voice_s = wav_seconds(wav)
    duration = LEAD_S + voice_s + END_S
    n_frames = int(duration * FPS)
    starts = [LEAD_S + x["start"] for x in info]
    ends = [LEAD_S + x["end"] for x in info]
    cuts = starts[1:] + [LEAD_S + voice_s]  # each shot holds until the next line starts
    c = profile["contact"]
    end = Renderer(direction, profile["name"]).end_card(
        video["end_card"], " · ".join(x for x in (c.get("address"), c.get("phone")) if x))
    r = Renderer(direction, profile["name"])
    subjects = {p["name"]: p["subject"] for p in profile["products"]}
    # Each line's frame: the portrait, or the close-up the second time a product appears.
    frames_for, seen = [], set()
    for ln in lines:
        s = shots[ln["photo"]]
        path = s.detail if ln["photo"] in seen and s.detail else s.portrait
        seen.add(ln["photo"])
        frames_for.append(path)
        r.lift(path, subjects.get(s.product) or "product")

    mp4 = out / "video.mp4"
    ff = subprocess.Popen(
        ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
         "-r", str(FPS), "-i", "-", "-itsoffset", str(LEAD_S), "-i", str(wav),
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-pix_fmt", "yuv420p",
         "-af", "apad", "-t", f"{n_frames / FPS:.3f}",  # silence under the end card
         "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", str(mp4)],
        stdin=subprocess.PIPE)
    voice_end = LEAD_S + voice_s
    for f in range(n_frames):
        t = f / FPS
        if t >= voice_end:
            k = len(lines) - 1
            frame = r.shot(frames_for[k], 1.0, k)
            a = min(1.0, (t - voice_end) / FADE_S)
            frame = Image.blend(frame, end, a)
        else:
            k = max(0, sum(1 for s in starts if s <= t) - 1)
            seg_start = 0.0 if k == 0 else starts[k]
            seg_len = max(0.5, cuts[k] - seg_start)
            frame = r.shot(frames_for[k], (t - seg_start) / seg_len, k)
            if k > 0 and t - starts[k] < FADE_S:  # cross-fade from the previous shot
                prev = r.shot(frames_for[k - 1], 1.0, k - 1)
                frame = Image.blend(prev, frame, (t - starts[k]) / FADE_S)
            if t < 2.4:
                r.hook_title(frame, video["hook"], 1.0 if t < 2.0 else (2.4 - t) / 0.4)
            if starts[k] <= t <= ends[k] + 0.35:
                p = (t - starts[k]) / max(0.3, ends[k] - starts[k])
                r.caption(frame, lines[k]["say"], min(1.0, p))
        ff.stdin.write(frame.tobytes())
    ff.stdin.close()
    if ff.wait() != 0:
        raise RuntimeError("ffmpeg failed to encode the video")
    poster = out / "poster.jpg"
    r.shot(frames_for[0], 0.3, 0).save(poster, quality=85)
    return {"mp4": str(mp4), "poster": str(poster), "voiceover": str(wav),
            "captions": str(out / "captions.srt"), "duration_s": round(duration, 1),
            "lines": [{"say": x["say"], "start_s": round(LEAD_S + x["start"], 2),
                       "end_s": round(LEAD_S + x["end"], 2), "heard": x["heard"], "match": x["match"]}
                      for x in info],
            "transcript_match": accuracy,
            "voice": "elevenlabs" if os.getenv("ELEVENLABS_API_KEY") else "macos-say"}


# --- 4. Muse Spark reviews the cut ------------------------------------------------------

REVIEW_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["hook", "pacing", "legibility", "on_brand", "overall", "verdict", "fixes"],
    "properties": {
        **{k: {"type": "integer", "description": "1-10"} for k in
           ("hook", "pacing", "legibility", "on_brand", "overall")},
        "verdict": {"type": "string", "description": "two sentences to the owner"},
        "fixes": {"type": "array", "items": {"type": "string"},
                  "description": "up to 3 concrete changes for the next cut"},
    },
}

REVIEW_PROMPT = """You are a short-form video editor reviewing a 9:16 video made for {name}, \
a {category}, before it is posted to TikTok and Instagram Reels. Watch and listen to it.
Score 1-10: hook (do the first 2 seconds stop the scroll?), pacing, legibility (captions and \
titles readable on a phone), on_brand (fits: {voice}), overall. Be honest and specific; a 10 \
is rare. Then give the owner a two-sentence verdict and up to 3 concrete fixes."""


def review(mp4: str, profile: dict) -> dict:
    raw = m.ask_video(REVIEW_PROMPT.format(name=profile["name"], category=profile["category"],
                                           voice=", ".join(profile["voice"]["adjectives"])),
                      mp4, schema=REVIEW_SCHEMA, effort="medium", max_tokens=6000)
    return json.loads(raw)


REVISE_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["hook", "lines", "end_card"],
    "properties": {
        "hook": {"type": "string", "description": "under 7 words; it is also the first spoken line"},
        "lines": {"type": "array", "items": {
            "type": "object", "additionalProperties": False, "required": ["photo", "say"],
            "properties": {"photo": {"type": "integer"}, "say": {"type": "string"}}}},
        "end_card": {"type": "string"},
    },
}

REVISE_PROMPT = """You wrote this short video script for {name}. An editor reviewed the cut \
and scored it {overall}/10 (hook {hook}/10). Their notes: {fixes}

Rewrite the script to fix what a script can fix. We can't film new footage: the shots are \
the same product photos (index: what it shows): {photos}. The first spoken line must be the \
hook, said out loud, and must stop the scroll in under 2 seconds. 4-5 lines, under 10 words \
each, 15 seconds in all. Same facts only, from: {facts}

Current script: {script}"""


def revise(plan: dict, review: dict, shots: list[Shot], profile: dict) -> dict:
    """Spark rewrites the script from the editor's notes."""
    facts = {k: profile[k] for k in ("name", "products", "contact", "value_props", "proof")}
    raw = m.ask(REVISE_PROMPT.format(
        name=profile["name"], overall=review["overall"], hook=review["hook"],
        fixes=json.dumps(review["fixes"]), photos=json.dumps({i: s.product for i, s in enumerate(shots)}),
        facts=json.dumps(facts), script=json.dumps(plan["video"])),
        schema=REVISE_SCHEMA, effort="medium", max_tokens=6000)
    from .text import tidy_all
    new = tidy_all(json.loads(raw))
    n = len(shots)
    for ln in new["lines"]:
        ln["photo"] %= n
    return {**plan, "video": {**plan["video"], **new}}


def make(plan: dict, shots: list[Shot], direction: dict, profile: dict, out: Path,
         rounds: int = 2) -> dict:
    """Render, have Spark review, and if it's weak, revise from the notes and go again.
    Keeps every cut and its review; the best one is the deliverable."""
    cuts = []
    for r in range(rounds):
        res = render(plan, shots, direction, profile, out / f"cut{r + 1}")
        rv = review(res["mp4"], profile)
        cuts.append({"render": res, "review": rv, "script": plan["video"]})
        if rv["overall"] >= GOOD_ENOUGH or r == rounds - 1:
            break
        plan = revise(plan, rv, shots, profile)
    best = max(cuts, key=lambda c: c["review"]["overall"])
    return {"best": best, "cuts": cuts}
