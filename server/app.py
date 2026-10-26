"""Sous live server: the phone page, plus a small JSON API around muse.live.

    uv run scripts/serve.py            # http://localhost:8000 (camera works on localhost)
    uv run scripts/serve.py --https    # self-signed, for a phone on the same wifi

    POST /api/sessions                 {"step": "..."} -> {"id", "spec"}
    POST /api/sessions/{id}/frames     multipart: image (JPEG), cook_s -> readings + verdict
    GET  /api/sessions/{id}            the newest state, without sending a frame
    GET  /api/clips                    clips in fixtures/ for replay mode, served at /clips/
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from muse.judge import OVERDONE_MARGIN
from muse.live import Session

ROOT = Path(__file__).resolve().parent.parent
STATIC = Path(__file__).resolve().parent / "static"
FIXTURES = ROOT / "fixtures"
CLIP_SUFFIXES = {".mp4", ".mov", ".m4v", ".webm"}
MAX_FRAME_BYTES = 4_000_000

app = FastAPI(title="Sous")
sessions: dict[str, Session] = {}


class NewSession(BaseModel):
    step: str


def get(sid: str) -> Session:
    s = sessions.get(sid)
    if not s:
        raise HTTPException(404, "no such session")
    return s


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-store"})


@app.post("/api/sessions")
async def new_session(body: NewSession) -> dict:
    step = body.step.strip()
    if not step:
        raise HTTPException(400, "say what you're cooking")
    s = await Session.start(step[:500])
    sessions[s.id] = s
    return {"id": s.id, "spec": asdict(s.spec), "over": 1 + OVERDONE_MARGIN / s.spec.target_bi}


@app.post("/api/sessions/{sid}/frames")
async def frame(sid: str, image: UploadFile = File(...), cook_s: float = Form(...)) -> dict:
    s = get(sid)
    jpeg = await image.read()
    if not jpeg or len(jpeg) > MAX_FRAME_BYTES:
        raise HTTPException(400, "send one JPEG frame under 4 MB")
    return await s.add_frame(jpeg, cook_s)


@app.get("/api/sessions/{sid}")
def state(sid: str) -> dict:
    s = get(sid)
    return {"id": s.id, "spec": asdict(s.spec), "pieces": s.pieces(),
            "verdict": s.verdict, "judging": s.judging}


@app.get("/api/clips")
def clips() -> list[str]:
    if not FIXTURES.exists():
        return []
    return sorted(p.name for p in FIXTURES.iterdir() if p.suffix.lower() in CLIP_SUFFIXES)


if FIXTURES.exists():
    app.mount("/clips", StaticFiles(directory=FIXTURES), name="clips")
