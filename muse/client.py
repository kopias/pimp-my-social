"""Thin helpers over Meta Model API (https://api.meta.ai/v1).

Every model sits behind one base URL and one bearer key. Text, vision, video,
image generation and SAM all go through the OpenAI SDK; speech-to-text is a
plain multipart POST.
"""

from __future__ import annotations

import base64
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv
from meta_sam_parser import (
    SegmentationMaskRecord,
    decode_mask_to_raster,
    image_segmentation_format,
    parse_responses_stream,
    video_segmentation_format,
)
from openai import AsyncOpenAI, OpenAI

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

BASE_URL = os.getenv("MODEL_API_BASE_URL", "https://api.meta.ai/v1")
TEXT_MODEL = os.getenv("MUSE_TEXT_MODEL", "muse-spark-1.3")
AGENT_MODEL = os.getenv("MUSE_AGENT_MODEL", "muse-wonder-1.0")
IMAGE_MODEL = os.getenv("MUSE_IMAGE_MODEL", "muse-image-1.0")
SAM_MODEL = os.getenv("MUSE_SAM_MODEL", "sam-3.1")
ASR_MODEL = os.getenv("MUSE_ASR_MODEL", "muse-voice-transcribe-1.0")


def api_key() -> str:
    key = os.getenv("MODEL_API_KEY", "").strip()
    if not key or key.startswith("<"):
        raise SystemExit("MODEL_API_KEY is not set. Put it in muse-hackathon/.env")
    return key


# The SDK default is 10 minutes a try, 3 tries: one hung request could stall a makeover for half
# an hour. Our longest healthy call (a Wonder build) takes about 3 minutes, so 5 minutes a try
# and the retry gets its turn.
TIMEOUT = 300


def client() -> OpenAI:
    return OpenAI(base_url=BASE_URL, api_key=api_key(), timeout=TIMEOUT, max_retries=2)


def aclient() -> AsyncOpenAI:
    return AsyncOpenAI(base_url=BASE_URL, api_key=api_key(), timeout=TIMEOUT, max_retries=2)


def data_url(path: str | Path) -> str:
    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(Path(path).read_bytes()).decode()}"


def output_text(response: Any) -> str:
    return getattr(response, "output_text", "") or ""


# --- text + vision -----------------------------------------------------------


def ask(prompt: str, *, images: list[str | Path] = (), model: str = TEXT_MODEL,
        effort: str = "low", schema: dict | None = None, max_tokens: int = 4000) -> str:
    """One Responses call. `images` are local paths or URLs."""
    content: list[dict] = [{"type": "input_text", "text": prompt}]
    for img in images:
        url = str(img) if str(img).startswith(("http", "data:")) else data_url(img)
        content.append({"type": "input_image", "image_url": url})
    kwargs: dict[str, Any] = {
        "model": model,
        "reasoning": {"effort": effort},
        "max_output_tokens": max_tokens,
        "input": [{"type": "message", "role": "user", "content": content}],
    }
    if schema:
        kwargs["text"] = {"format": {"type": "json_schema", "name": "out", "schema": schema,
                                     "strict": True}}
    return output_text(client().responses.create(**kwargs))


def ask_video(prompt: str, video: str | Path, *, model: str = TEXT_MODEL,
              effort: str = "low", schema: dict | None = None, max_tokens: int = 4000) -> str:
    """Upload an mp4 through the Files API, then ask about it."""
    c = client()
    with open(video, "rb") as f:
        uploaded = c.files.create(file=f, purpose="user_data")
    kwargs: dict[str, Any] = {}
    if schema:
        kwargs["text"] = {"format": {"type": "json_schema", "name": "out", "schema": schema,
                                     "strict": True}}
    response = c.responses.create(
        model=model,
        reasoning={"effort": effort},
        max_output_tokens=max_tokens,
        input=[{"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": prompt},
            {"type": "input_file", "file_id": uploaded.id},
        ]}],
        **kwargs,
    )
    return output_text(response)


# --- image generation --------------------------------------------------------


def generate_image(prompt: str, out: str | Path, *, size: str = "auto",
                   fast: bool = True) -> Path:
    """Muse Image, one shot. `fast` = single pass with search tools off. A refused explicit
    size is retried at "auto" and cropped (see edit_image)."""
    extra: dict[str, Any] = {"output_format": "png"}
    if fast:
        extra["reasoning_strength"] = "low"
        extra["tool_enablement"] = {"enable_web_search": False, "enable_shell": False}

    def call(sz: str) -> Path:
        kwargs: dict[str, Any] = {"model": IMAGE_MODEL, "prompt": prompt, "n": 1, "extra_body": extra}
        if sz != "auto":
            kwargs["size"] = sz
        response = client().images.generate(**kwargs)
        Path(out).write_bytes(base64.b64decode(response.data[0].b64_json))
        return Path(out)
    return _sized(call, size, Path(out))


def _sized(call, size: str, out: Path, tries: int = 3) -> Path:
    """Run `call(size)`; when the API refuses the size with its bare 400, make it at "auto"
    and crop to the size. Retry the same 400 when it comes from a burst of requests."""
    import time
    for k in range(tries):
        try:
            if size == "auto":
                return call("auto")
            try:
                return call(size)
            except Exception as e:
                if "invalid" not in str(e).lower():
                    raise
                call("auto")
                _crop_to(out, size)
                return out
        except Exception as e:
            if k == tries - 1 or "invalid" not in str(e).lower():
                raise
            time.sleep(2 + 3 * k)
    raise AssertionError("unreachable")


def _crop_to(path: Path, size: str) -> None:
    """Centre-crop and scale a picture to an exact WxH."""
    from PIL import Image
    w, h = (int(v) for v in size.split("x"))
    im = Image.open(path)
    r = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * r), round(im.height * r)), Image.LANCZOS)
    left, top = (im.width - w) // 2, (im.height - h) // 2
    im.crop((left, top, left + w, top + h)).save(path)


def edit_image(src: str | Path, prompt: str, out: str | Path, *, size: str = "auto",
               tries: int = 3) -> Path:
    """Muse Image edit of one photo. Fast mode: one pass, no web or image search.
    The content filter is strict about words like "burnt"; it raises on refusal.

    Since late October 2026 the edit endpoint answers an explicit size with a bare 400
    ("The image generation request was invalid"), so a sized request that's refused is
    made at "auto" and cropped to the size here. Bursts of requests also draw the same
    400 now and then, so each call gets a couple of retries."""

    def call(sz: str) -> Path:
        kwargs: dict[str, Any] = {"model": IMAGE_MODEL, "prompt": prompt, "n": 1,
                                  "extra_body": {"output_format": "png", "reasoning_strength": "low",
                                                 "tool_enablement": {"enable_web_search": False,
                                                                     "enable_shell": False,
                                                                     "enable_image_search": False}}}
        if sz != "auto":
            kwargs["size"] = sz
        with open(src, "rb") as f:
            r = client().images.edit(image=f, **kwargs)
        Path(out).write_bytes(base64.b64decode(r.data[0].b64_json))
        return Path(out)

    return _sized(call, size, Path(out), tries)


def edit_images(srcs: list[str | Path], prompt: str, out: str | Path, *,
                size: str = "1024x1536") -> Path:
    """Muse Image edit from several photos at once ("the person in image 1 wearing the
    dress in image 2"). The API wants the files as image[0], image[1], ..., which the
    OpenAI SDK doesn't send, so this is a plain multipart POST. A refused size is made at
    "auto" and cropped (see edit_image)."""
    def call(sz: str) -> Path:
        files = {f"image[{i}]": (Path(s).name, open(s, "rb"), mimetypes.guess_type(str(s))[0] or "image/png")
                 for i, s in enumerate(srcs)}
        data = {"model": IMAGE_MODEL, "prompt": prompt, "n": "1", "output_format": "png",
                "reasoning_strength": "low"}
        if sz != "auto":
            data["size"] = sz
        try:
            r = requests.post(f"{BASE_URL}/images/edits", headers={"Authorization": f"Bearer {api_key()}"},
                              files=files, timeout=300, data=data)
        finally:
            for _, f, _ in files.values():
                f.close()
        if not r.ok:
            raise RuntimeError(f"Muse Image edit {r.status_code}: {r.text[:300]}")
        Path(out).write_bytes(base64.b64decode(r.json()["data"][0]["b64_json"]))
        return Path(out)
    return _sized(call, size, Path(out))


# --- SAM 3.1 -----------------------------------------------------------------


@dataclass
class Segment:
    object_id: str
    # Where the mask sits in the frame: left, top, right, bottom (right/bottom
    # half-open). The mask is cropped to this box, not the whole frame.
    box: tuple[int, int, int, int]
    mask: bytes | None  # row-major 0/1, width * height of the box
    width: int
    height: int
    confidence: float | None
    frame: int | None

    @property
    def area(self) -> int:
        return sum(self.mask) if self.mask else 0


async def segment(concept: str, media: str | Path, *, video: bool = False,
                  confidence: bool = True) -> list[Segment]:
    """Boxes + masks for every `concept` in an image (or each frame of an mp4)."""
    c = aclient()
    if video:
        with open(media, "rb") as f:
            uploaded = await c.files.create(file=f, purpose="user_data")
        part = {"type": "input_video", "file_id": uploaded.id}
    else:
        url = str(media) if str(media).startswith(("http", "data:")) else data_url(media)
        part = {"type": "input_image", "image_url": url}
    metadata = {"mask_encoding": "one_bit"}
    if confidence:
        metadata["include_confidence"] = "true"
    events = await c.responses.create(
        model=SAM_MODEL,
        input=[{"type": "message", "role": "user",
                "content": [{"type": "input_text", "text": concept}, part]}],
        stream=True,
        metadata=metadata,
    )
    fmt = video_segmentation_format() if video else image_segmentation_format()
    result = await parse_responses_stream(events, fmt).final_result()

    def frame_of(rec: Any) -> int | None:
        return getattr(rec.frame, "frame_index", None) if rec.frame else None

    out: list[Segment] = []
    for r in result.records:
        if not isinstance(r, SegmentationMaskRecord):
            continue
        b = r.bounds
        out.append(Segment(
            object_id=r.object_id,
            box=(b.left, b.top, b.right, b.bottom),
            mask=decode_mask_to_raster(r.mask),
            width=r.mask.width,
            height=r.mask.height,
            confidence=r.confidence,
            frame=frame_of(r),
        ))
    return out


# --- speech to text ----------------------------------------------------------


def transcribe(wav: str | Path, *, keywords: list[str] | None = None,
               mode: str = "PUSH_TO_TALK") -> dict:
    """Muse Voice Transcribe on a mono 16-bit WAV (16 or 24 kHz).

    Convert anything else first:
      ffmpeg -i in.m4a -ac 1 -ar 24000 -c:a pcm_s16le -map_metadata -1 out.wav
    """
    import json

    req: dict[str, Any] = {"mode": mode, "model": ASR_MODEL, "audioEncoding": "WAV"}
    if keywords:
        req["keywords"] = keywords
    with open(wav, "rb") as f:
        r = requests.post(
            f"{BASE_URL}/asr/transcribe",
            headers={"Authorization": f"Bearer {api_key()}"},
            files={"request": (None, json.dumps(req), "application/json"),
                   "audio": (Path(wav).name, f, "audio/wav")},
            timeout=120,
        )
    r.raise_for_status()
    return r.json()
