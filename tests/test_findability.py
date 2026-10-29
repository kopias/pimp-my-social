"""The parts of the makeover that code guarantees: no network, no models."""

import json
import re

from pms import audit
from pms import site as S

PROFILE = {
    "name": "Marigold Lane Bakery", "one_liner": "Family bakery in Riverside.",
    "category": "bakery", "audience": "Riverside locals", "location": "Riverside",
    "contact": {"address": "22 Marigold Lane, Riverside", "phone": "555-0142", "email": "",
                "hours": ["Tue-Fri 7am-3pm"], "order_url": ""},
    "products": [{"name": "Country Sourdough", "description": "36 hour ferment.", "price": "$9",
                  "photo": 0, "subject": "bread loaf"},
                 {"name": "Wedding Cakes", "description": "Call for a quote.", "price": "",
                  "photo": -1, "subject": "cake"}],
    "faqs": [{"q": "Do you do gluten free bread?", "a": "Fridays, if you order by Wednesday."}],
    "socials": {"facebook": "https://facebook.com/marigold"},
}
COPY = {"seo_title": "Marigold Lane Bakery | Sourdough in Riverside",
        "meta_description": "Hand-made sourdough and croissants.", "share_title": "Marigold Lane"}
IMAGES = [{"path": "img/country-sourdough.jpg", "w": 1600, "h": 1067, "product": "Country Sourdough",
           "alt": "A sourdough loaf", "role": "hero"},
          {"path": "img/share.jpg", "w": 1200, "h": 630, "role": "share", "alt": ""}]
BASE = "https://marigold.example/"


def test_robots_blocking_ai_bots_is_caught():
    robots = "User-agent: GPTBot\nDisallow: /\n\nUser-agent: ClaudeBot\nDisallow: /\n\nUser-agent: *\nDisallow:\n"
    assert audit.blocked_ai_bots(robots) == ["GPTBot", "ClaudeBot"]


def test_a_blanket_disallow_blocks_every_ai_bot():
    assert set(audit.blocked_ai_bots("User-agent: *\nDisallow: /\n")) == set(audit.AI_BOTS)


def test_grouped_user_agents_share_their_rules():
    robots = "User-agent: GPTBot\nUser-agent: CCBot\nDisallow: /\n"
    assert audit.blocked_ai_bots(robots) == ["GPTBot", "CCBot"]


def test_our_robots_txt_passes_our_own_check():
    assert audit.blocked_ai_bots(S.robots_txt(BASE)) == []
    assert "Sitemap: https://marigold.example/sitemap.xml" in S.robots_txt(BASE)


def test_jsonld_has_business_products_with_real_prices_and_faq():
    blocks = S.jsonld(PROFILE, COPY, BASE, IMAGES, None)
    types = [b["@type"] for b in blocks]
    assert types == ["LocalBusiness", "Product", "Product", "FAQPage"]
    assert blocks[1]["offers"]["price"] == "9"
    assert "offers" not in blocks[2]  # no price on the site, so none invented
    assert blocks[0]["sameAs"] == ["https://facebook.com/marigold"]


def test_head_tags_cover_what_the_audit_checks():
    head = S.head_tags(PROFILE, COPY, BASE, IMAGES, None)
    for needle in ("<title>", 'name="description"', 'rel="canonical"', 'property="og:title"',
                   'property="og:description"', 'property="og:image"', "application/ld+json"):
        assert needle in head


def test_llms_txt_lists_products_and_answers():
    txt = S.llms_txt(PROFILE, COPY, BASE)
    assert txt.startswith("# Marigold Lane Bakery") and "Country Sourdough ($9)" in txt
    assert "Fridays, if you order by Wednesday." in txt


def test_enforce_leaves_one_h1_and_alt_on_every_image():
    page = ('<html><body><h1>A</h1><h1 class="x">B</h1><img src="img/country-sourdough.jpg">'
            '<img src="other.jpg" alt=""></body></html>')
    out = S.enforce(page, IMAGES)
    assert out.count("<h1") == 1 and "<h2 class=\"x\">B</h2>" in out
    assert 'alt="A sourdough loaf"' in out and 'lang="en"' in out


def test_inline_data_cannot_close_its_script_tag():
    evil = {**PROFILE, "faqs": [{"q": "</script><script>alert(1)</script>", "a": "x"}]}
    end = S.body_end(evil, COPY)
    blob = re.search(r'id="pms-data">(.*?)</script>', end, re.S).group(1)
    assert json.loads(blob.replace("<\\/", "</"))["faqs"][0]["q"].startswith("</script>")


def test_tidy_calms_the_shouting_but_keeps_the_facts():
    from pms.text import tidy, tidy_all
    assert tidy("Saturdays only, they go fast!! Come early!") == "Saturdays only, they go fast! Come early."
    assert tidy("Sun 8am - 12pm (NEW!)") == "Sun 8am - 12pm"
    assert tidy("NOW OPEN SUNDAYS") == "Now Open Sundays"
    out = tidy_all({"caption": "Wow!! So good!", "price": "$9!!", "contact": {"phone": "555-0142"}})
    assert out == {"caption": "Wow! So good.", "price": "$9!!", "contact": {"phone": "555-0142"}}
