from muse import judge as j
from muse.browning import Reading, positions


def spec(protein="poultry", turn="flip"):
    return j.WatchSpec(step="sear", food="chicken thigh", reference="gas stove",
                       target_shade="deep_golden", minutes_min=6, minutes_max=8,
                       turn_action=turn, protein=protein, watch_for="deep golden skin")


def v(state, action, say="Take it off the heat."):
    return j.Verdict(state=state, action=action, pieces=[], say=say, reason="", confidence=0.9)


def r(oid, frame, bi, cx=0.5, cy=0.5, conf=0.95):
    return Reading(object_id=oid, frame=frame, bi=bi, lightness=60, browned=0.5, area=100,
                   area_ratio=1.0, confidence=conf, cx=cx, cy=cy)


def test_thermometer_when_poultry_leaves_the_pan():
    assert "74°C" in j._guard(spec(), v("ready", "remove")).say


def test_no_thermometer_on_a_mid_cook_flip():
    assert "°C" not in j._guard(spec(), v("ready", "flip", "Flip them now.")).say


def test_no_thermometer_for_onions():
    assert "°C" not in j._guard(spec(protein="none", turn="remove"), v("ready", "remove")).say


def test_never_claims_food_is_safe():
    out = j._guard(spec(protein="beef"), v("ready", "remove", "Perfect, it's safe to eat."))
    assert "safe" not in out.say.lower() and "thermometer" in out.say.lower()


def test_no_food_means_fix_camera_without_calling_spark():
    out = j.verdict(spec(), [], "unused.jpg", fps=4, elapsed_min=1)
    assert out.action == "fix_camera" and out.by_code


def test_low_sam_confidence_means_fix_camera():
    out = j.verdict(spec(), [r("0", 0, 100, conf=0.2)], "unused.jpg", fps=4, elapsed_min=1)
    assert out.action == "fix_camera" and out.by_code


def test_positions_side_by_side_even_when_both_left_of_centre():
    assert positions([r("0", 0, 50, cx=0.35), r("1", 0, 50, cx=0.15)]) == {"1": "left", "0": "right"}


def test_positions_front_and_back():
    assert positions([r("0", 0, 50, cy=0.8), r("1", 0, 50, cy=0.2)]) == {"1": "back", "0": "front"}


def test_judge_on_band_crossing_not_on_every_frame():
    s = spec()  # target BI 180
    quiet = [r("0", 0, 100), r("0", 1, 102)]
    assert not j.should_judge(quiet, s, {"0": 100 / 180}, seconds_since_last=3)
    crossing = [r("0", 0, 100), r("0", 1, 181)]  # passes 0.85 and 1.0
    assert j.should_judge(crossing, s, {"0": 100 / 180}, seconds_since_last=3)
    assert j.should_judge(quiet, s, {"0": 100 / 180}, seconds_since_last=20)
