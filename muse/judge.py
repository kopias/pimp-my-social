"""Muse Spark as the judge: recipe step -> watch spec, readings + frame -> verdict.

Division of labour, on purpose:
- Spark reads language and pictures. It turns a recipe step into what to watch
  (`watch_spec`) and, given the measurements and the latest frame, decides what
  the cook should do and how to say it (`verdict`).
- The code owns the numbers. Spark picks a target *shade* in words; the BI that
  shade means comes from SHADE_BI below, which is calibrated on footage, not
  guessed by the model. Progress toward the target is computed here and handed
  to Spark as a fact.
- Safety is not the model's call. For poultry and pork, any "done" verdict gets
  a thermometer instruction appended, and Sous never says food is safe to eat.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from . import client as m
from .browning import Reading, by_object, positions

# Target shade -> mean Browning Index for "there". From the AI cook-through clip
# (scripts/make_test_clip.py); recalibrate on real pan footage.
SHADE_BI = {
    "light_golden": 100.0,
    "golden": 150.0,
    "deep_golden": 180.0,
    "mahogany": 260.0,
}
OVERDONE_MARGIN = 70.0  # BI past target that counts as over
MIN_CONFIDENCE = 0.5  # below this SAM confidence, don't trust the reading

THERMOMETER = {"poultry": 74, "pork": 63, "ground_meat": 71}  # °C, USDA minimums

SHADES = list(SHADE_BI)
ACTIONS = ["wait", "flip", "stir", "lower_heat", "raise_heat", "remove", "check_temp",
           "fix_camera"]
STATES = ["not_started", "cooking", "almost", "ready", "overdone", "unclear"]


# --- step -> watch spec ------------------------------------------------------

SPEC_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["food", "reference", "target_shade", "minutes_min", "minutes_max",
                 "turn_action", "protein", "watch_for"],
    "properties": {
        "food": {"type": "string",
                 "description": "ONE short noun phrase naming a single piece of the food, "
                                "for an object segmenter, e.g. 'chicken thigh', 'onion'."},
        "reference": {"type": "string",
                      "description": "a nearby surface that will not change colour, e.g. "
                                     "'gas stove', 'cutting board'"},
        "target_shade": {"type": "string", "enum": SHADES},
        "minutes_min": {"type": "number"},
        "minutes_max": {"type": "number"},
        "turn_action": {"type": "string", "enum": ["flip", "stir", "remove", "none"],
                        "description": "what the cook does when the target is reached"},
        "protein": {"type": "string",
                    "enum": ["poultry", "pork", "ground_meat", "beef", "fish", "none"]},
        "watch_for": {"type": "string", "description": "one sentence: the visual cue of done"},
    },
}

SPEC_PROMPT = """You are the sous chef standing beside a home cook. Turn this recipe step into a \
watch spec for a camera above the pan.

Step: {step}

Pick the target shade the step implies: light_golden (barely coloured), golden, deep_golden \
(rich brown, crisp skin, a proper sear) or mahogany (very dark, caramelised onions, a hard \
crust). Use the step's own timing if it gives one, else a sensible range."""


@dataclass
class WatchSpec:
    step: str
    food: str
    reference: str
    target_shade: str
    minutes_min: float
    minutes_max: float
    turn_action: str
    protein: str
    watch_for: str

    @property
    def target_bi(self) -> float:
        return SHADE_BI[self.target_shade]


def watch_spec(step: str) -> WatchSpec:
    raw = m.ask(SPEC_PROMPT.format(step=step), schema=SPEC_SCHEMA, effort="low")
    return WatchSpec(step=step, **json.loads(raw))


# --- readings -> verdict -----------------------------------------------------

VERDICT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["state", "action", "pieces", "say", "reason", "confidence"],
    "properties": {
        "state": {"type": "string", "enum": STATES},
        "action": {"type": "string", "enum": ACTIONS},
        "pieces": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["piece", "state", "position"],
                "properties": {
                    "piece": {"type": "string"},
                    "state": {"type": "string", "enum": STATES},
                    "position": {"type": "string",
                                 "description": "where it sits in the photo, as a cook would "
                                                "say it: 'left', 'back right', 'front'"},
                },
            },
        },
        "say": {"type": "string",
                "description": "what to say aloud to the cook, 15 words max, plain and calm"},
        "reason": {"type": "string", "description": "one sentence, citing the numbers"},
        "confidence": {"type": "number"},
    },
}

VERDICT_PROMPT = """You are Sous, a sous chef watching a home cook's pan through a camera. \
Decide what the cook should do right now.

The step: {step}
Done looks like: {watch_for}. When it is done, the cook should: {turn_action}.
Expected time: {minutes_min:g}-{minutes_max:g} min. Elapsed: {elapsed:.1f} min.

Measured surface browning per piece. These numbers come from pixel measurement inside a \
segmentation mask and are more reliable than your eye for colour. "progress" is mean \
browning divided by the target: 1.0 means the target shade is reached, above {over:.2f} \
means overdone. "browned" is the share of the surface past golden. "rate" is progress \
gained per minute over the last readings.
{table}

"position" is measured from where each piece sits in the frame; use exactly those words. \
The photo is the latest frame. Use it for what numbers can't tell you: smoke, a piece out of \
frame, the camera blocked, something unexpected.

Rules:
- Trust the numbers for colour. Only override them if the photo clearly shows they are wrong \
(say so in reason).
- Call each piece by its measured position, never by its id number.
- If pieces differ, say so: "flip the left one, give the right one a minute".
- "say" is spoken aloud: 15 words max, no numbers unless it's a time, no jargon.
- Never say food is safe to eat or fully cooked inside. You only see the surface."""


@dataclass
class Verdict:
    state: str
    action: str
    pieces: list[dict]
    say: str
    reason: str
    confidence: float
    progress: dict[str, float] = field(default_factory=dict)
    by_code: bool = False  # True when decided without calling Spark

    def as_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def progress_table(readings: list[Reading], spec: WatchSpec, fps: float,
                   window_s: float = 20.0) -> tuple[str, dict[str, float], float]:
    """Latest reading per piece, as a small text table, plus the progress dict
    and the worst SAM confidence seen."""
    lines = ["piece | position | progress | browned | rate/min | shrink | sam_conf"]
    where = positions(readings)
    progress: dict[str, float] = {}
    worst = 1.0
    for oid, rows in sorted(by_object(readings).items()):
        last = rows[-1]
        p = last.bi / spec.target_bi if not math.isnan(last.bi) else float("nan")
        earlier = [r for r in rows if (last.frame - r.frame) / fps <= window_s]
        span_min = (last.frame - earlier[0].frame) / fps / 60
        rate = ((last.bi - earlier[0].bi) / spec.target_bi / span_min) if span_min > 0 else 0.0
        progress[oid] = round(p, 3)
        conf = last.confidence if last.confidence is not None else 1.0
        worst = min(worst, conf)
        lines.append(f"{oid} | {where.get(oid, '?')} | {p:.2f} | {100 * last.browned:.0f}% | {rate:+.2f} | "
                     f"{100 * (1 - last.area_ratio):.0f}% | {conf:.2f}")
    return "\n".join(lines), progress, worst


def verdict(spec: WatchSpec, readings: list[Reading], frame_path: str | Path, *,
            fps: float, elapsed_min: float) -> Verdict:
    if not readings:
        return _guard(spec, Verdict("unclear", "fix_camera", [], "I can't see the food. "
                                    "Can you point the camera at the pan?",
                                    "SAM found no food in frame.", 1.0, by_code=True))
    table, progress, worst = progress_table(readings, spec, fps)
    if worst < MIN_CONFIDENCE:
        return _guard(spec, Verdict("unclear", "fix_camera", [], "I've lost sight of the food. "
                                    "Is something in the way?",
                                    f"SAM confidence {worst:.2f} is below {MIN_CONFIDENCE}.",
                                    1.0, progress=progress, by_code=True))
    prompt = VERDICT_PROMPT.format(
        step=spec.step, watch_for=spec.watch_for, turn_action=spec.turn_action,
        minutes_min=spec.minutes_min, minutes_max=spec.minutes_max, elapsed=elapsed_min,
        over=1 + OVERDONE_MARGIN / spec.target_bi, table=table,
    )
    raw = m.ask(prompt, images=[frame_path], schema=VERDICT_SCHEMA, effort="low")
    return _guard(spec, Verdict(**json.loads(raw), progress=progress))


def _guard(spec: WatchSpec, v: Verdict) -> Verdict:
    """Hard rules the model doesn't get a vote on."""
    # Leaving the pan is when inside-doneness matters. A flip is mid-cook, so
    # no thermometer there.
    temp = THERMOMETER.get(spec.protein)
    leaving = v.action in ("remove", "check_temp") or spec.turn_action == "remove"
    if temp and v.state in ("ready", "overdone") and leaving:
        v.say = f"{v.say.rstrip('.')}. Check it hits {temp}°C inside before serving."
    for word in ("safe to eat", "fully cooked", "cooked through"):
        if word in v.say.lower():
            v.say = "It looks done on the outside. Check the inside with a thermometer."
    return v


# --- when to call the judge --------------------------------------------------


def should_judge(readings: list[Reading], spec: WatchSpec, last_progress: dict[str, float],
                 seconds_since_last: float, every_s: float = 15.0) -> bool:
    """Call Spark when a piece crosses a progress band, or every `every_s` seconds."""
    if seconds_since_last >= every_s or not last_progress:
        return True
    bands = (0.6, 0.85, 1.0, 1 + OVERDONE_MARGIN / spec.target_bi)
    for oid, rows in by_object(readings).items():
        now = rows[-1].bi / spec.target_bi
        before = last_progress.get(oid, 0.0)
        if any(before < b <= now for b in bands):
            return True
    return False
