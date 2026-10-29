"""Pimp My Social: the splash page and a small JSON API around pms.pipeline.

    uv run scripts/serve.py            # http://localhost:8000

    POST /api/jobs                     {"url", "channels": [...], "tags": [...], "consent": true}
    GET  /api/jobs/{id}                progress and results; poll it
    POST /api/jobs/{id}/direction      {"id": "<direction id>"} starts the build
    GET  /api/options                  channels, style tags and the remix format library
    POST /api/formats                  multipart "post": a video or image of a post that's working;
                                       reverse engineered into a format and added to the library
    GET  /jobs/{id}/...                the files a makeover made
"""

from __future__ import annotations

import asyncio
import hashlib
import re
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from pms.crawl import BlockedURL, check_public
from pms.directions import STYLE_TAGS
from pms import remix
from pms.pipeline import JOBS, Job
from pms.social import CHANNELS

STATIC = Path(__file__).resolve().parent / "static"
MAX_RUNNING = 2  # makeovers cost real API money; don't let a crowd run up the bill
MAX_UPLOAD = 60 * 1024 * 1024
POST_TYPES = {"video/mp4": ".mp4", "video/quicktime": ".mov", "video/webm": ".webm",
              "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
UPLOADS = JOBS.parent / "uploads"

app = FastAPI(title="Pimp My Social")
running = asyncio.Semaphore(MAX_RUNNING)
tasks: set[asyncio.Task] = set()


class NewJob(BaseModel):
    url: str = Field(max_length=300)
    channels: list[str] = []
    tags: list[str] = []
    formats: list[str] = []
    consent: bool = False


class Pick(BaseModel):
    id: str


def _spawn(coro) -> None:
    async def guarded():
        async with running:
            await coro
    t = asyncio.create_task(guarded())
    tasks.add(t)
    t.add_done_callback(tasks.discard)


def _job(jid: str) -> Job:
    if not re.fullmatch(r"[a-f0-9]{10}", jid) or not (JOBS / jid / "job.json").exists():
        raise HTTPException(404, "No such makeover.")
    return Job.load(jid)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-store"})


@app.get("/api/options")
def options() -> dict:
    return {"channels": [{"id": k, "name": v["name"]} for k, v in CHANNELS.items()],
            "tags": STYLE_TAGS, "formats": _formats()}


def _formats() -> list[dict]:
    return [{k: f.get(k) for k in ("id", "name", "essence", "look", "people", "source")}
            for f in remix.library()]


@app.post("/api/formats")
async def add_format(post: UploadFile = File(...)) -> dict:
    """Reverse engineer an uploaded post into a format (Spark watches, Transcribe listens)."""
    ext = POST_TYPES.get(post.content_type or "")
    if not ext:
        raise HTTPException(400, "Upload a video (mp4, mov, webm) or an image (jpg, png, webp).")
    data = await post.read(MAX_UPLOAD + 1)
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "That file is over 60 MB.")
    digest = hashlib.sha1(data).hexdigest()[:12]
    UPLOADS.mkdir(parents=True, exist_ok=True)
    path = UPLOADS / f"{digest}{ext}"
    path.write_bytes(data)
    async with running:
        try:
            spec = await asyncio.to_thread(remix.extract, path, UPLOADS / digest)
        except Exception as e:
            raise HTTPException(502, f"Couldn't read that post: {type(e).__name__}") from None
    return {k: spec.get(k) for k in ("id", "name", "essence", "why_it_works", "keep", "drop", "look", "people")}


@app.post("/api/jobs")
async def new_job(body: NewJob) -> dict:
    if not body.consent:
        raise HTTPException(400, "Please confirm you own this business or have its permission.")
    try:
        url = await asyncio.to_thread(check_public, body.url)
    except BlockedURL as e:
        raise HTTPException(400, str(e)) from None
    channels = [c for c in body.channels if c in CHANNELS] or ["instagram"]
    tags = [t for t in body.tags if t in STYLE_TAGS][:3]
    known = {f["id"] for f in remix.library()}
    formats = [f for f in body.formats if f in known][:2]
    job = Job(url, channels, tags, formats=formats)
    _spawn(job.act_one())
    return {"id": job.id}


@app.get("/api/jobs/{jid}")
def get_job(jid: str) -> dict:
    return _job(jid).state


@app.post("/api/jobs/{jid}/direction")
async def choose(jid: str, body: Pick, request: Request) -> dict:
    job = _job(jid)
    if job.state["status"] != "choose":
        raise HTTPException(409, "This makeover isn't waiting for a choice.")
    if body.id not in {c["id"] for c in job.state["data"].get("cards", [])}:
        raise HTTPException(400, "Pick one of the offered directions.")
    job.state["status"] = "building"
    job.save()
    base = str(request.base_url).rstrip("/")
    _spawn(job.act_two(body.id, base))
    return {"ok": True}


JOBS.mkdir(parents=True, exist_ok=True)
app.mount("/jobs", StaticFiles(directory=JOBS), name="jobs")
app.mount("/static", StaticFiles(directory=STATIC), name="static")
