"""Video helpers that don't need a model: the transcript check, captions, house style."""

from pms import video as V


def test_word_accuracy_forgives_small_slips_but_not_missing_words():
    script = ["Mum Jean started us back in 1987."]
    assert V.word_accuracy(script, "Mom Jean started us back in in 1987") >= 0.8
    assert V.word_accuracy(script, "started") < 0.3


def test_srt_is_well_formed_and_offset():
    out = V.srt([{"say": "Hello there.", "start": 0.0, "end": 1.25},
                 {"say": "Second.", "start": 1.6, "end": 2.0}], offset=0.6)
    assert out.splitlines()[:3] == ["1", "00:00:00,600 --> 00:00:01,850", "Hello there."]
    assert "00:00:02,200 --> 00:00:02,600" in out
