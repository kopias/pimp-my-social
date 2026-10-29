"""Pimp My Social: the splash page and a small JSON API around pms.pipeline.

    uv run scripts/serve.py            # http://localhost:8000

    POST /api/jobs                     {"url", "channels": [...], "tags": [...], "consent": true}
    GET  /api/jobs/{id}                progress and results; poll it
    POST /api/jobs/{id}/direction      {"id": "<direction id>"} starts the build
    GET  /api/options                  channels and style tags for the form
    GET  /jobs/{id}/...                the files a makeover made
"""

from __future__ import annotations

import asyncio
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from pms.crawl import BlockedURL, check_public
from pms.directions import STYLE_TAGS
from pms.pipeline import JOBS, Job
from pms.social import CHANNELS

STATIC = Path(__file__).resolve().parent / "static"
MAX_RUNNING = 2  # makeovers cost real API money; don't let a crowd run up the bill

app = FastAPI(title="Pimp My Social")
running = asyncio.Semaphore(MAX_RUNNING)
tasks: set[asyncio.Task] = set()


class NewJob(BaseModel):
    url: str = Field(max_length=300)
    channels: list[str] = []
    tags: list[str] = []
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
            "tags": STYLE_TAGS}


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
    job = Job(url, channels, tags)
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
