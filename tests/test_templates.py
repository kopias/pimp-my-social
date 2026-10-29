"""Offline checks for the 25 template skills and the tag mapping (no API calls)."""

import re

from pms import directions, templates

HEX = re.compile(r"^#[0-9A-F]{6}$")
ROLES = {"bg", "surface", "ink", "muted", "accent", "accent2"}


def test_every_template_skill_is_complete():
    ts = templates.all_templates()
    assert len(ts) == 25
    for tid, t in ts.items():
        assert t["id"] == tid
        for key in ("name", "style", "tags", "pitch", "palette", "fonts", "measured", "layout", "photo", "signature"):
            assert t.get(key), (tid, key)
        assert set(t["palette"]) == ROLES and all(HEX.match(v) for v in t["palette"].values()), tid
        assert set(t["tags"]) <= set(directions.STYLE_TAGS), tid
        assert len(t["signature"]) >= 5, tid
        assert "## Anatomy" in t["skill"] and "## Never" in t["skill"], tid


def test_font_urls_ask_only_for_declared_families():
    for tid, t in templates.all_templates().items():
        url = directions.font_css(t)
        for fam in [t["fonts"]["display"], t["fonts"]["body"], t["fonts"].get("label")]:
            if fam:
                assert "family=" + fam.replace(" ", "+") in url, tid


def test_every_style_tag_maps_somewhere():
    for tag in directions.STYLE_TAGS:
        n, tid = templates.rank([tag])[0]
        assert n == 1, tag
        assert tag in templates.load(tid)["tags"]


def test_tag_combinations_map_to_the_obvious_template():
    assert templates.match(["dark", "street", "editorial"]) == "khy"
    assert templates.match(["playful", "retro", "romantic", "warm"]) == "lisa_says_gah"
    assert templates.match(["natural", "romantic", "dark"]) == "madina_visconti"
    assert templates.match(["luxury", "heritage", "calm"]) == "tiffany"


def test_blocked_captures_never_reach_the_builder():
    for tid in ("sezane", "net_a_porter"):
        assert templates.shots(tid) == []
    for tid in ("cos", "dior"):
        assert [p.name for p in templates.shots(tid)] in ([], ["mobile_1.jpg"])


def test_template_menu_words_are_caught_unless_the_business_has_them():
    from pms import site
    page = "<header><nav><a>WOMEN</a><a>MEN</a><a>TEEN</a><a>KIDS</a></nav></header><main>kids</main>"
    profile = {"products": [{"name": "Linen shirt", "description": "for women and men"}]}
    assert site.borrowed_labels(page, "mango", profile) == ["TEEN", "KIDS"]
    assert site.borrowed_labels(page.replace("TEEN", "SHIRTS"), "mango", {"note": "teen women men"}) == ["KIDS"]


def test_a_product_shown_with_another_products_photo_is_caught():
    from pms import site
    imgs = [{"path": "img/shirt.jpg", "product": "Lime Shirt"}, {"path": "img/dress.jpg", "product": "Ink Dress"},
            {"path": "img/shirt-tall.jpg", "product": "Lime Shirt"}]
    page = ('<img src="img/shirt.jpg" alt="Lime Shirt in linen"><img src="img/shirt-tall.jpg" alt="Oak Jacket">'
            '<img src="img/dress.jpg" alt="Lime Shirt">')
    assert site.swapped_photos(page, imgs + [{"path": "x", "product": "Oak Jacket"}]) == [
        "Lime Shirt shown with the photo of Ink Dress", "Oak Jacket shown with the photo of Lime Shirt"]


def test_a_product_with_no_photo_borrowing_one_is_caught():
    from pms import site
    imgs = [{"path": "img/shirt.jpg", "product": "Lime Shirt"}]
    page = '<img src="img/shirt.jpg" alt="Oak Jacket">'
    assert site.swapped_photos(page, imgs) == []  # the jacket isn't known without the product list
    assert site.swapped_photos(page, imgs, ["Lime Shirt", "Oak Jacket"]) == ["Oak Jacket shown with the photo of Lime Shirt"]


def test_invented_years_and_counts_are_caught():
    from pms import site
    page = "<style>.a{width:2019px}</style><h1>Made in Oakland since 2019</h1><p>100+ reviews, 500+ fans</p>"
    assert site.invented_numbers(page, {"proof": ["100+ Five-Star Reviews"]}) == ["2019", "500+"]


def test_option_count_follows_how_precise_the_ask_is():
    from pms import directions
    assert directions.how_many(1) == 3 and directions.how_many(25) == 6 and directions.how_many(3) == 5


def test_headline_contrast_measures_the_ground_not_the_letters(tmp_path):
    from PIL import Image, ImageDraw
    from pms import site
    for ground, expect_weak in (("#111111", False), ("#F2EFE6", True)):
        im = Image.new("RGB", (400, 100), ground)
        ImageDraw.Draw(im).rectangle((20, 30, 380, 70), fill="#FFFFFF")  # stand-in for white letters
        im.save(tmp_path / "s.png")
        weak = site.headline_contrast(tmp_path / "s.png", {"x": 0, "y": 0, "w": 400, "h": 100, "rgb": [255, 255, 255]})
        assert (weak > 0.5) == expect_weak, ground


def test_neighbouring_sketches_get_different_headlines_and_twists():
    import random
    from pms import mockups
    copy = {"h1": "A", "h1_options": ["B", "C", "D"]}
    firsts = [{"name": f"P{k}", "photo": k} for k in range(4)]
    vs = mockups.variants([{}] * 4, firsts, copy, random.Random(1))
    assert len({v["headline"] for v in vs}) == 4 and len({v["twist"] for v in vs}) == 4
