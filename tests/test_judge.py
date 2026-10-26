from muse import judge as j
from muse.browning import Reading, positions


def spec(protein="poultry", turn="flip"):
    return j.WatchSpec(step="sear", food="chicken thigh", reference="gas stove",
                       target_shade="deep_golden", minutes_min=6, minutes_max=8,
                       turn_action=turn, protein=protein, watch_for="deep golden skin")


def v(state, action, say="Take it off the heat."):
    return j.Verdict(state=state, action=action, pieces=[], say=say, reason="", confidence=0.9)


def r(oid, frame, bi, cx=0.5, cy=0.5, conf=0.95, L=60, region=None):
    return Reading(object_id=oid, frame=frame, bi=bi, lightness=L, browned=0.5, area=100,
                   area_ratio=1.0, confidence=conf, cx=cx, cy=cy, region=region)


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


def test_charring_reads_as_overdone_even_though_bi_fell():
    # The onion clip's shape: BI peaks then drops as it blackens, L* keeps falling.
    s = spec(protein="none", turn="remove")
    rows = [r("0", 0, 60, L=72), r("0", 4, 290, L=33), r("0", 8, 239, L=28)]
    assert j.charring(rows)
    table, progress, _ = j.progress_table(rows, s, fps=4)
    assert progress["0"] > 1 + j.OVERDONE_MARGIN / s.target_bi
    assert "| yes |" in table


def test_still_browning_is_not_charring():
    assert not j.charring([r("0", 0, 60, L=72), r("0", 4, 150, L=57), r("0", 8, 240, L=47)])


def test_spread_calls_for_a_stir_when_one_region_runs_ahead():
    s = spec(protein="none", turn="stir")
    rows = [r("0", 0, 150, region="whole pan"), r("0/back", 0, 260, region="back"),
            r("0/front", 0, 110, region="front")]
    table, _, _ = j.progress_table(rows, s, fps=4)
    assert "back leads" in table and "front lags" in table and "uneven, stir" in table
