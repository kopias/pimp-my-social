"""Offline checks for the extra sources: link recognition, caption parsing, post choice (no API calls)."""

import pytest

from pms import sources
from pms.sources import Post, Source


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """recognise() resolves the host; these tests shouldn't depend on the network."""
    monkeypatch.setenv("PMS_ALLOW_PRIVATE", "1")


@pytest.mark.parametrize("raw, platform, handle", [
    ("instagram.com/shop8amfashion", "instagram", "shop8amfashion"),
    ("https://www.instagram.com/shop8amfashion/?hl=en", "instagram", "shop8amfashion"),
    ("https://www.instagram.com/shop8amfashion/p/DdrjxXNPLSO/", "instagram", "shop8amfashion"),
    ("https://www.tiktok.com/@shop8am", "tiktok", "shop8am"),
    ("https://www.etsy.com/shop/8amStyle", "etsy", "8amStyle"),
    ("linktr.ee/marigold", "linktree", "marigold"),
    ("m.facebook.com/shop8amfashion", "facebook", "shop8amfashion"),
    ("someshop.example", "website", ""),
])
def test_recognise(raw, platform, handle):
    r = sources.recognise(raw)
    assert (r["platform"], r["handle"]) == (platform, handle)
    if platform == "instagram":
        assert r["url"] == f"https://www.instagram.com/{handle}/"


def test_links_add_the_sites_own_instagram_once():
    site = {"instagram": "https://www.instagram.com/shop8amfashion", "facebook": "https://facebook.com/x"}
    links = sources.links_for(site, ["https://www.etsy.com/shop/8amStyle"])
    assert [x["platform"] for x in links] == ["etsy", "instagram"] and links[1]["linked_from_site"]
    # Added by the owner already (in another spelling): no duplicate, and it's theirs, not "linked".
    links = sources.links_for(site, ["@x", "instagram.com/SHOP8AMFASHION/"])
    assert [x["platform"] for x in links].count("instagram") == 1
    assert len(sources.links_for({}, ["a.example", "b.example", "c.example", "d.example"])) == sources.MAX_SOURCES


def test_caption_and_counts_from_the_post_page():
    p = Post("u", "i", "r", "", False, True)
    sources._caption(p, '1,204 likes, 4 comments - shop8amfashion on September 17, 2026: "New kimono, cut in Oakland". ')
    assert (p.likes, p.comments, p.caption, p.date) == (1204, 4, "New kimono, cut in Oakland", "September 17, 2026")
    assert sources._count("3.4K") == 3400


def test_profile_bio_and_followers():
    src = Source("u", "instagram", "Instagram", "shop8amfashion")
    sources._instagram_profile(src, {"desc": '957 Followers, 1,627 Following, 83 Posts - 8 AM Fashion '
                                             '(@shop8amfashion) on Instagram: "Cut & sewn in Oakland."'})
    assert (src.followers, src.bio) == ("957", "Cut & sewn in Oakland.")


def test_usable_keeps_products_first_and_one_per_name():
    def post(kind, product, likes, owner=True):
        return Post(product or kind, "i", "r", "", False, owner, kind=kind, product=product, likes=likes)
    src = Source("u", "instagram", "Instagram", "h", posts=[
        post("worn", "Kimono", 50), post("product", "Denim jacket", 2), post("event", "", 90),
        post("worn", "kimono", 10), post("product", "Tee", 9)])
    assert [p.product for p in sources.usable([src])] == ["Tee", "Denim jacket", "Kimono"]


def test_safe_get_refuses_private_addresses_and_redirects_into_them(monkeypatch):
    """A picture URL off someone's page must not reach the server's own network."""
    from pms import crawl
    monkeypatch.delenv("PMS_ALLOW_PRIVATE")
    crawl._host_ok.clear()
    for url in ("http://169.254.169.254/computeMetadata/v1/", "http://127.0.0.1:27150/", "file:///etc/passwd"):
        with pytest.raises(crawl.BlockedURL):
            crawl.safe_get(url)

    class Hop:  # a public page that redirects to the metadata service
        status_code, headers = 302, {"location": "http://169.254.169.254/latest/"}
    monkeypatch.setattr(crawl, "_public_host", lambda host: None if host == "public.example" else (_ for _ in ()).throw(crawl.BlockedURL("private")))
    monkeypatch.setattr(crawl.requests, "get", lambda *a, **k: Hop())
    crawl._host_ok.clear()
    with pytest.raises(crawl.BlockedURL):
        crawl.safe_get("http://public.example/photo.jpg")
