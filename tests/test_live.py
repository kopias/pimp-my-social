"""Live session logic with SAM and Spark stubbed out: no network, no cost."""

import asyncio
import io

import numpy as np
from PIL import Image

from muse import judge as j
from muse import live
from muse.client import Segment


def jpeg(rgb=(200, 140, 70)):
    buf = io.BytesIO()
    Image.fromarray(np.full((60, 90, 3), rgb, np.uint8)).save(buf, "JPEG")
    return buf.getvalue()


def pile(conf=0.9):
    return [Segment("0", (10, 10, 70, 50), b"\x01" * (60 * 40), 60, 40, conf, None)]


def spec():
    return j.WatchSpec(step="onions", food="sliced onions", reference="pan handle",
                       target_shade="mahogany", minutes_min=25, minutes_max=30,
                       turn_action="remove", protein="none", watch_for="deep brown", pile=True)


def session(tmp_path, monkeypatch, sam):
    monkeypatch.setattr(live, "SESSIONS", tmp_path)
    asked = []

    async def segment(concept, media, video=False):
        asked.append(concept)
        return sam(concept)

    def verdict(spec, readings, frame_path, *, fps, elapsed_min):
        if not readings:
            return j.Verdict("unclear", "fix_camera", [], "I can't see the food.", "", 1.0,
                             by_code=True)
        return j.Verdict("cooking", "wait", [], "Keep going.", "", 0.9)

    monkeypatch.setattr(live.m, "segment", segment)
    monkeypatch.setattr(live.j, "verdict", verdict)
    return live.Session(spec()), asked


def test_a_pile_is_measured_as_regions_and_judged_in_the_background(tmp_path, monkeypatch):
    s, _ = session(tmp_path, monkeypatch, lambda c: pile() if c != "pan handle" else [])

    async def run():
        first = await s.add_frame(jpeg(), 0)
        assert first["judging"] and first["verdict"] is None  # Spark never blocks a frame
        await asyncio.gather(*s._tasks)
        return await s.add_frame(jpeg(), 3)

    out = asyncio.run(run())
    positions = {p["position"] for p in out["pieces"]}
    assert "whole pan" in positions and "middle" in positions
    assert out["verdict"]["say"] == "Keep going." and out["overlay"].startswith("data:image/png")
    assert (tmp_path / s.id / "verdicts.jsonl").exists()


def test_falls_back_to_food_when_the_recipe_phrase_fades(tmp_path, monkeypatch):
    s, asked = session(tmp_path, monkeypatch,
                       lambda c: pile(0.95) if c == "food" else pile(0.4) if c != "pan handle" else [])
    out = asyncio.run(s.add_frame(jpeg(), 0))
    assert out["concept"] == "food" and out["found"] == 1
    asked.clear()
    asyncio.run(s.add_frame(jpeg(), 3))
    assert "sliced onions" not in asked  # it stays on the phrase that works


def test_says_it_cannot_see_after_two_empty_frames(tmp_path, monkeypatch):
    s, _ = session(tmp_path, monkeypatch, lambda c: [])
    assert asyncio.run(s.add_frame(jpeg(), 0))["verdict"] is None
    out = asyncio.run(s.add_frame(jpeg(), 3))
    assert out["verdict"]["action"] == "fix_camera"
