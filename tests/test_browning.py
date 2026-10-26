import numpy as np

from muse.browning import browning_index, erode, measure, srgb_to_lab
from muse.client import Segment

SWATCHES = {  # sRGB of chicken skin as it cooks
    "raw": (236, 210, 190),
    "pale gold": (226, 180, 120),
    "golden": (200, 140, 70),
    "deep brown": (130, 75, 35),
}


def bi(rgb):
    return float(browning_index(srgb_to_lab(np.array([[rgb]], dtype=np.uint8)))[0, 0])


def test_lab_white_and_black():
    lab = srgb_to_lab(np.array([[[255, 255, 255], [0, 0, 0]]], dtype=np.uint8))[0]
    assert abs(lab[0, 0] - 100) < 0.1 and abs(lab[0, 1]) < 0.1 and abs(lab[0, 2]) < 0.1
    assert abs(lab[1, 0]) < 0.1


def test_bi_rises_as_skin_browns():
    values = [bi(c) for c in SWATCHES.values()]
    assert values == sorted(values), dict(zip(SWATCHES, values))
    assert values[0] < 40 and values[-1] > 120


def test_erode_shrinks_square():
    m = np.zeros((20, 20), bool)
    m[5:15, 5:15] = True
    assert erode(m, 2).sum() == 36


def _seg(oid, frame, w=40, h=40):
    return Segment(object_id=oid, box=(0, 0, w, h), mask=b"\x01" * (w * h), width=w, height=h,
                   confidence=0.9, frame=frame)


def test_measure_tracks_browning_and_lighting():
    raw, brown = SWATCHES["raw"], SWATCHES["golden"]
    frames = {0: np.full((40, 40, 3), raw, np.uint8), 1: np.full((40, 40, 3), brown, np.uint8)}
    r = measure(frames, [_seg("0", 0), _seg("0", 1)])
    assert r[0].bi < r[1].bi and r[0].browned == 0 and r[1].browned == 1
    assert r[1].area_ratio == 1.0


def test_reference_cancels_a_lighting_change():
    # Same food, but the second frame is shot under dimmer light: the reference
    # dims identically, so the corrected lightness should barely move.
    food = np.full((40, 40, 3), SWATCHES["pale gold"], np.uint8)
    dim = (food.astype(float) * 0.8).astype(np.uint8)
    ref, ref_dim = np.full((40, 40, 3), 128, np.uint8), np.full((40, 40, 3), 102, np.uint8)
    frames = {0: np.concatenate([food, ref], 1), 1: np.concatenate([dim, ref_dim], 1)}
    f = [_seg("0", 0), _seg("0", 1)]
    refs = [Segment("9", (40, 0, 80, 40), b"\x01" * 1600, 40, 40, None, i) for i in (0, 1)]
    naive = measure(frames, f)
    fixed = measure(frames, f, reference=refs)
    assert abs(fixed[1].lightness - fixed[0].lightness) < abs(naive[1].lightness - naive[0].lightness) / 3
