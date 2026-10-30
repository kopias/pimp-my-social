"""Pimp My Social: the splash page and a small JSON API around pms.pipeline.

    uv run scripts/serve.py            # http://localhost:8000

    POST /api/jobs                     {"url", "sources": [...], "channels": [...], "tags": [...], "consent": true}
    POST /api/sources                  {"url"}: what a pasted link is (Instagram, TikTok, a shop...)
    GET  /api/jobs/{id}                progress and results; poll it
    POST /api/jobs/{id}/direction      {"id": "<direction id>"} starts the build
    GET  /api/options                  channels, style tags and the remix format library
    POST /api/formats                  multipart "post": a video or image of a post that's working;
                                       reverse engineered into a format and added to the library
    GET  /api/config                   whether live makeovers are open, and the showroom
    GET  /jobs/{id}/...                the files a makeover made

Hosted, it runs as a showroom (PMS_LIVE=code): finished makeovers listed in
out/showroom.json open for anyone, and a new makeover, which spends real API money,
needs PMS_LIVE_CODE. PMS_LIVE=off turns live makeovers off entirely; open (the
default, for local use) asks for nothing.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import os
import re
import time
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from pms.crawl import BlockedURL, check_public
from pms.directions import STYLE_TAGS
from pms import remix, sources
from pms.pipeline import JOBS, Job
from pms.social import CHANNELS

STATIC = Path(__file__).resolve().parent / "static"
MAX_RUNNING = int(os.environ.get("PMS_MAX_RUNNING", "2"))  # makeovers cost real API money
LIVE = os.environ.get("PMS_LIVE", "open")  # open | code | off
LIVE_CODE = os.environ.get("PMS_LIVE_CODE", "")
PER_DAY = int(os.environ.get("PMS_LIVE_PER_DAY", "12"))  # a second cap, on the bill not the crowd
MAX_UPLOAD = 60 * 1024 * 1024
POST_TYPES = {"video/mp4": ".mp4", "video/quicktime": ".mov", "video/webm": ".webm",
              "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}
UPLOADS = JOBS.parent / "uploads"
SHOWROOM = JOBS.parent / "showroom.json"
LEDGER = JOBS.parent / "live-runs.json"

app = FastAPI(title="Pimp My Social")
running = asyncio.Semaphore(MAX_RUNNING)
tasks: set[asyncio.Task] = set()


class NewJob(BaseModel):
    code: str = Field(default="", max_length=100)
    url: str = Field(max_length=300)
    sources: list[str] = Field(default=[], max_length=sources.MAX_SOURCES)
    channels: list[str] = []
    tags: list[str] = []
    formats: list[str] = []
    consent: bool = False


class Pick(BaseModel):
    id: str
    code: str = Field(default="", max_length=100)


class Link(BaseModel):
    url: str = Field(max_length=300)


def _spawn(coro) -> None:
    async def guarded():
        async with running:
            await coro
    t = asyncio.create_task(guarded())
    tasks.add(t)
    t.add_done_callback(tasks.discard)


def _job(jid: str) -> Job:
    if not re.fullmatch(r"[a-f0-9]{10}", jid) or not (JOBS / jid / "job.json").exists() or jid in hidden():
        raise HTTPException(404, "No such makeover.")
    return Job.load(jid)


def _allow_live(code: str) -> None:
    """Spending money needs the code (when there is one) and room in today's allowance."""
    if LIVE == "off":
        raise HTTPException(403, "Live makeovers are off here. Open a finished one below.")
    if LIVE == "code" and not (LIVE_CODE and hmac.compare_digest(code.strip(), LIVE_CODE)):
        raise HTTPException(403, "A live makeover needs the access code.")
    if LIVE != "open":
        today = time.strftime("%Y-%m-%d")
        runs = json.loads(LEDGER.read_text()) if LEDGER.exists() else {}
        if runs.get(today, 0) >= PER_DAY:
            raise HTTPException(429, "Today's live makeovers are used up. Open a finished one below.")
        LEDGER.write_text(json.dumps({today: runs.get(today, 0) + 1}))


def showroom() -> list[dict]:
    """The finished makeovers on show: listed in out/showroom.json, and only ones that finished."""
    if not SHOWROOM.exists():
        return []
    out = []
    for item in json.loads(SHOWROOM.read_text()):
        if not item.get("public") or not re.fullmatch(r"[a-f0-9]{10}", item.get("id", "")):
            continue
        f = JOBS / item["id"] / "job.json"
        if not f.exists():
            continue
        st = json.loads(f.read_text())
        d = st.get("data", {})
        if st.get("status") != "done":
            continue
        picked = next((c for c in d.get("cards", []) if c.get("id") == d.get("direction")), {})
        out.append({"id": item["id"], "name": d.get("brand", {}).get("name", ""),
                    "note": item.get("note", ""),
                    "direction": picked.get("name", ""),
                    "before": d.get("before", {}).get("desktop"),
                    "after": d.get("audit_after", {}).get("desktop"),
                    "from": d.get("audit_before", {}).get("score", {}).get("overall"),
                    "to": d.get("audit_after", {}).get("score", {}).get("overall")})
    return out


def hidden() -> set[str]:
    """Showroom entries not yet published (a real business still saying yes): never served."""
    if not SHOWROOM.exists():
        return set()
    return {x["id"] for x in json.loads(SHOWROOM.read_text()) if not x.get("public")}


class JobFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        if path.split("/", 1)[0] in hidden():
            raise HTTPException(404, "No such makeover.")
        return await super().get_response(path, scope)


@app.get("/api/config")
def config() -> dict:
    return {"live": LIVE, "showroom": showroom()}


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
async def add_format(post: UploadFile = File(...), code: str = Form("")) -> dict:
    """Reverse engineer an uploaded post into a format (Spark watches, Transcribe listens)."""
    _allow_live(code)
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


@app.post("/api/sources")
async def recognise(body: Link) -> dict:
    """The page recognises common platforms itself; this is the word on anything else
    (and refuses addresses that aren't public)."""
    try:
        return await asyncio.to_thread(sources.recognise, body.url)
    except BlockedURL as e:
        raise HTTPException(400, str(e)) from None


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
    links = []
    for raw in body.sources:
        if not raw.strip():
            continue
        try:
            links.append((await asyncio.to_thread(sources.recognise, raw[:300]))["url"])
        except BlockedURL as e:
            raise HTTPException(400, f"{raw.strip()[:60]}: {e}") from None
    _allow_live(body.code)  # last, so a refused address doesn't use up a run
    job = Job(url, channels, tags, formats=formats, sources=links)
    _spawn(job.act_one())
    return {"id": job.id}


@app.get("/api/jobs/{jid}")
def get_job(jid: str) -> dict:
    return _job(jid).state


@app.post("/api/jobs/{jid}/direction")
async def choose(jid: str, body: Pick, request: Request) -> dict:
    job = _job(jid)
    if LIVE != "open" and not (LIVE_CODE and hmac.compare_digest(body.code.strip(), LIVE_CODE)):
        raise HTTPException(403, "Building a makeover needs the access code.")
    if job.state["status"] != "choose":
        raise HTTPException(409, "This makeover isn't waiting for a choice.")
    if body.id not in {c["id"] for c in job.state["data"].get("cards", [])}:
        raise HTTPException(400, "Pick one of the offered directions.")
    job.state["status"] = "building"
    job.save()
    # the after-audit re-crawls our own preview of the new site with the address check off,
    # so on a server that address is pinned in config, never taken from the Host header
    base = (os.environ.get("PMS_BASE_URL") or str(request.base_url)).rstrip("/")
    _spawn(job.act_two(body.id, base))
    return {"ok": True}


JOBS.mkdir(parents=True, exist_ok=True)
app.mount("/jobs", JobFiles(directory=JOBS), name="jobs")
app.mount("/static", StaticFiles(directory=STATIC), name="static")
# The fictional demo bakery, so anyone with the code can watch a whole makeover without
# making over a real business that never asked.
app.mount("/demo", StaticFiles(directory=STATIC.parent.parent / "demo", html=True), name="demo")
