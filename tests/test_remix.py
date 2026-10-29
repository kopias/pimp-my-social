"""Offline checks for the remix and logo guardrails (no API calls)."""

import json

import numpy as np
from PIL import Image, ImageDraw

from pms import logo, remix


def test_invented_prices_are_removed():
    profile = {"products": [{"price": "$89.00"}, {"price": "Regular $159, sale $129"}]}
    g = {"beats": [{"text": "Linen shirt, $89.00"}, {"text": "now only $49"}, {"text": "$129"}]}
    removed = remix.check_prices(g, profile)
    assert removed == ["$49"]
    assert g["beats"][0]["text"] == "Linen shirt, $89.00"
    assert "$" not in g["beats"][1]["text"]
    assert g["beats"][2]["text"] == "$129"


def test_library_formats_are_complete():
    keys = set(remix.FORMAT_SCHEMA["required"])
    for f in remix.library():
        assert keys <= set(f), f["id"]
        for b in f["beats"]:
            assert b["shot"] in remix.SHOTS and b["motion"] in remix.MOTIONS, f["id"]


def test_logo_background_keyed_out(tmp_path):
    im = Image.new("RGB", (400, 400), "#F8F6F1")
    ImageDraw.Draw(im).ellipse((120, 80, 280, 320), outline="#141414", width=18)
    src = tmp_path / "redraw.png"
    im.save(src)
    w, h = logo.key_out(src, "#141414", tmp_path / "mark.png", tmp_path / "light.png", "#F8F6F1")
    mark = np.asarray(Image.open(tmp_path / "mark.png"))
    assert mark.shape[2] == 4 and (w, h) == (mark.shape[1], mark.shape[0])
    assert mark[0, 0, 3] == 0  # the corner is transparent
    assert mark[..., 3].max() == 255  # the ring is solid
    assert w < 220 and h < 280  # trimmed to the mark


def _brief():
    poster = {"persona": "the boxer", "headline": "I blamed my shoulders|for three summers",
              "body": " ".join(["word"] * 40)}
    beats = [{"role": r, "caption": "Short and plain."} for r in ("failure", "face", "fix", "payoff")]
    return {"question": "got fit?", "posters": [dict(poster) for _ in range(3)],
            "deprivation": {"line": "Everyone dressed for someone else."}, "film": {"beats": beats}}


def test_campaign_gate_passes_a_clean_brief():
    from pms import campaign
    assert campaign.gate(_brief(), {}) == []


def test_campaign_gate_catches_claims_prices_and_shape():
    from pms import campaign
    b = _brief()
    b["question"] = "Got Fit"
    b["posters"][0]["headline"] = "Our AI-cut shirts|are now just $49"
    b["film"]["beats"] = b["film"]["beats"][:3]
    bad = " ".join(campaign.gate(b, {}))
    for expect in ("question", "banned", "prices", "four"):
        assert expect in bad, expect


def test_patch_only_softens_the_marked_region(tmp_path):
    from pms import campaign
    im = Image.new("RGB", (200, 200), "white")
    ImageDraw.Draw(im).rectangle((0, 0, 40, 200), fill="black")
    ImageDraw.Draw(im).rectangle((150, 150, 160, 160), fill="black")
    src = tmp_path / "a.png"
    im.save(src)
    out = campaign.patch(src, [{"x": 70, "y": 70, "w": 20, "h": 20, "kind": "garbled"}], tmp_path / "b.png")
    a = np.asarray(Image.open(out).convert("L")).astype(int)
    assert a[100, 10] == 0 and a[100, 60] == 255  # far from the patch: untouched
    assert 0 < a[155, 155] < 255  # inside it: softened
