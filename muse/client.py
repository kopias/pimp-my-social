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
    SegmentationBoxRecord,
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


def client() -> OpenAI:
    return OpenAI(base_url=BASE_URL, api_key=api_key())


def aclient() -> AsyncOpenAI:
    return AsyncOpenAI(base_url=BASE_URL, api_key=api_key())


def data_url(path: str | Path) -> str:
    mime = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
    return f"data:{mime};base64,{base64.b64encode(Path(path).read_bytes()).decode()}"


def output_text(response: Any) -> str:
    return getattr(response, "output_text", "") or ""


# --- text + vision -----------------------------------------------------------


def ask(prompt: str, *, images: list[str | Path] = (), model: str = TEXT_MODEL,
        effort: str = "low", schema: dict | None = None) -> str:
    """One Responses call. `images` are local paths or URLs."""
    content: list[dict] = [{"type": "input_text", "text": prompt}]
    for img in images:
        url = str(img) if str(img).startswith(("http", "data:")) else data_url(img)
        content.append({"type": "input_image", "image_url": url})
    kwargs: dict[str, Any] = {
        "model": model,
        "reasoning": {"effort": effort},
        "max_output_tokens": 4000,
        "input": [{"type": "message", "role": "user", "content": content}],
    }
    if schema:
        kwargs["text"] = {"format": {"type": "json_schema", "name": "out", "schema": schema,
                                     "strict": True}}
    return output_text(client().responses.create(**kwargs))


def ask_video(prompt: str, video: str | Path, *, model: str = TEXT_MODEL,
              effort: str = "low") -> str:
    """Upload an mp4 through the Files API, then ask about it."""
    c = client()
    with open(video, "rb") as f:
        uploaded = c.files.create(file=f, purpose="user_data")
    response = c.responses.create(
        model=model,
        reasoning={"effort": effort},
        max_output_tokens=4000,
        input=[{"type": "message", "role": "user", "content": [
            {"type": "input_text", "text": prompt},
            {"type": "input_file", "file_id": uploaded.id},
        ]}],
    )
    return output_text(response)


# --- image generation --------------------------------------------------------


def generate_image(prompt: str, out: str | Path, *, size: str = "auto",
                   fast: bool = True) -> Path:
    """Muse Image, one shot. `fast` = single pass with search tools off."""
    extra: dict[str, Any] = {"output_format": "png"}
    if fast:
        extra["reasoning_strength"] = "low"
        extra["tool_enablement"] = {"enable_web_search": False, "enable_shell": False}
    kwargs: dict[str, Any] = {"model": IMAGE_MODEL, "prompt": prompt, "n": 1, "extra_body": extra}
    if size != "auto":
        kwargs["size"] = size
    response = client().images.generate(**kwargs)
    out = Path(out)
    out.write_bytes(base64.b64decode(response.data[0].b64_json))
    return out


# --- SAM 3.1 -----------------------------------------------------------------


@dataclass
class Segment:
    object_id: str
    box: tuple[int, int, int, int]  # left, top, right, bottom (right/bottom half-open)
    mask: bytes | None  # row-major 0/1, width * height
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
    fmt = video_segmentation_format if video else image_segmentation_format
    result = await parse_responses_stream(events, fmt).final_result()

    def frame_of(rec: Any) -> int | None:
        return getattr(rec.frame, "frame_index", None) if rec.frame else None

    boxes = {(r.object_id, frame_of(r)): r for r in result.records
             if isinstance(r, SegmentationBoxRecord)}
    out: list[Segment] = []
    for r in result.records:
        if not isinstance(r, SegmentationMaskRecord):
            continue
        b = boxes.get((r.object_id, frame_of(r)))
        out.append(Segment(
            object_id=r.object_id,
            box=(b.left, b.top, b.right, b.bottom) if b else (0, 0, 0, 0),
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
