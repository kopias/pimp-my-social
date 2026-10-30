"""More context than the website: the owner's Instagram, TikTok, shop and so on.

A small business's website often shows a fraction of what it makes; the feed is where
the rest lives. The owner pastes a link, `recognise` says what it is (Instagram
profile, TikTok, Etsy shop...), `read` renders it as a logged-out visitor would and
keeps the posts, and `classify` has Muse Spark look at every post with its caption and
sort it: a product on its own, a product being worn, an event, behind the scenes, a
text graphic, someone else's post. Only clear product photos go on to the brand read
and the photo studio.

Same rules as the site inspection: public pages only, a dozen posts at most, one
page at a time, and an honest user agent. A platform that answers with a bot check
or a login wall gets reported as unreadable; we never try to get around it.
"""

from __future__ import annotations

import asyncio
import io
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from PIL import Image as PILImage

from muse import client as m

from .crawl import UA, BlockedURL, _guard, _settle, check_public, safe_get
from .browser import CHANNEL

MAX_SOURCES = 3
MAX_POSTS = 12  # what a logged-out profile shows, and plenty to sort

# host (without www.) -> (platform id, display name, kind)
PLATFORMS = {
    "instagram.com": ("instagram", "Instagram", "social"),
    "tiktok.com": ("tiktok", "TikTok", "social"),
    "facebook.com": ("facebook", "Facebook", "social"),
    "fb.com": ("facebook", "Facebook", "social"),
    "pinterest.com": ("pinterest", "Pinterest", "social"),
    "youtube.com": ("youtube", "YouTube", "social"),
    "youtu.be": ("youtube", "YouTube", "social"),
    "x.com": ("x", "X", "social"),
    "twitter.com": ("x", "X", "social"),
    "linkedin.com": ("linkedin", "LinkedIn", "social"),
    "threads.net": ("threads", "Threads", "social"),
    "threads.com": ("threads", "Threads", "social"),
    "etsy.com": ("etsy", "Etsy", "shop"),
    "depop.com": ("depop", "Depop", "shop"),
    "poshmark.com": ("poshmark", "Poshmark", "shop"),
    "amazon.com": ("amazon", "Amazon", "shop"),
    "linktr.ee": ("linktree", "Linktree", "links"),
}
NOT_HANDLES = {"p", "reel", "reels", "explore", "stories", "tv", "shop", "listing", "watch",
               "channel", "c", "user", "pin", "in", "company", "share", "hashtag"}
BLOCKED_WORDS = ("captcha", "access denied", "temporarily restricted", "verify you are human",
                 "unusual traffic", "are you a robot", "page unavailable")

KINDS = ["product", "worn", "lifestyle", "event", "behind_the_scenes", "text_graphic", "repost", "other"]
USABLE = {"product", "worn"}  # what the brand read may treat as a product photo


@dataclass
class Post:
    url: str
    image: str  # local jpg
    remote: str
    alt: str
    video: bool
    owner: bool  # posted by this account, not a collab or repost
    source: str = ""  # the platform's name
    caption: str = ""
    likes: int | None = None
    comments: int | None = None
    date: str = ""
    kind: str = ""  # from classify
    product: str = ""
    subject: str = ""
    why: str = ""


@dataclass
class Source:
    url: str
    platform: str
    name: str
    handle: str
    status: str = "read"  # read | blocked | empty | failed
    note: str = ""
    title: str = ""
    bio: str = ""
    followers: str = ""
    links: list[str] = field(default_factory=list)
    posts: list[Post] = field(default_factory=list)
    linked_from_site: bool = False

    def to_dict(self) -> dict:
        return asdict(self)


def recognise(url: str) -> dict:
    """What a pasted link is: {"url", "platform", "name", "kind", "handle"}. Unknown hosts are
    a "website" (another shop or a link page). Raises BlockedURL for non-public addresses."""
    url = check_public(url)
    u = urlparse(url)
    host = (u.hostname or "").lower().removeprefix("www.").removeprefix("m.")
    platform, name, kind = next((v for h, v in PLATFORMS.items() if host == h or host.endswith("." + h)),
                                ("website", host, "website"))
    parts = [p for p in u.path.split("/") if p]
    handle = ""
    if platform == "etsy" and len(parts) >= 2 and parts[0] == "shop":
        handle = parts[1]
    elif parts and parts[0].lower() not in NOT_HANDLES:
        handle = parts[0].lstrip("@")
    if platform == "instagram" and handle:  # one canonical profile address, whatever was pasted
        url = f"https://www.instagram.com/{handle}/"
    return {"url": url, "platform": platform, "name": name, "kind": kind, "handle": handle}


def same(a: dict, b: dict) -> bool:
    return a["platform"] == b["platform"] and (a["handle"] or a["url"]).lower() == (b["handle"] or b["url"]).lower()


# The profile grid: each post's link, cover image and the alt text Instagram writes for it
# ("Photo by 8 AM Fashion on July 20, 2026. May be an image of ...").
GRID_JS = r"""
() => {
  const meta = (k) => (document.querySelector(`meta[property="${k}"],meta[name="${k}"]`) || {}).content || '';
  const posts = [], seen = new Set();
  for (const a of document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]')) {
    const img = a.querySelector('img');
    if (!img || seen.has(a.href) || img.naturalWidth < 200) continue;
    seen.add(a.href);
    posts.push({ url: a.href, img: img.currentSrc || img.src, alt: img.alt || '' });
  }
  // Links out of the profile (the bio link, Threads), not Instagram's own footer.
  const links = [...document.querySelectorAll('header a[href], section a[href]')].map((a) => a.href)
    .filter((h) => !/^https?:\/\/([a-z0-9-]+\.)*(instagram|facebook|meta|muse)\.(com|ai)\//.test(h) || /threads\./.test(h));
  return { title: document.title, desc: meta('description') || meta('og:description'), posts,
           links, text: document.body.innerText.slice(0, 1500) };
}
"""

POST_JS = r"""
() => (document.querySelector('meta[property="og:description"]') || {}).content || ''
"""

# Any other page (a shop, a link page): its title, description and biggest pictures.
PAGE_JS = r"""
() => {
  const meta = (k) => (document.querySelector(`meta[property="${k}"],meta[name="${k}"]`) || {}).content || '';
  const imgs = [...document.images].filter((i) => i.naturalWidth >= 300 && i.naturalHeight >= 300)
    .sort((a, b) => b.naturalWidth * b.naturalHeight - a.naturalWidth * a.naturalHeight)
    .map((i) => ({ url: i.closest('a') ? i.closest('a').href : location.href, img: i.currentSrc || i.src, alt: i.alt || '' }));
  return { title: document.title, desc: meta('og:description') || meta('description'), posts: imgs, links: [], text: (document.querySelector('main') || document.body).innerText.slice(0, 1500) };
}
"""


def _count(s: str) -> int | None:
    m_ = re.match(r"([\d.,]+)\s*([KkMm]?)", s or "")
    if not m_:
        return None
    n = float(m_.group(1).replace(",", ""))
    return int(n * {"k": 1e3, "m": 1e6}.get(m_.group(2).lower(), 1))


def _blocked(status: int, text: str) -> bool:
    return status in (401, 403, 429) or any(w in text.lower() for w in BLOCKED_WORDS)


def _save(url: str, out: Path) -> bool:
    try:
        r = safe_get(url)
        r.raise_for_status()
        im = PILImage.open(io.BytesIO(r.content)).convert("RGB")
    except Exception:
        return False
    im.thumbnail((1600, 1600))
    im.save(out, "JPEG", quality=90)
    return True


async def read(link: dict, out: Path) -> Source:
    """Render one source as a logged-out visitor and keep its posts (images saved under `out`)."""
    from playwright.async_api import async_playwright  # only when a source is read

    src = Source(url=link["url"], platform=link["platform"], name=link["name"], handle=link["handle"],
                 linked_from_site=link.get("linked_from_site", False))
    out.mkdir(parents=True, exist_ok=True)
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(channel=CHANNEL)
            ctx = await browser.new_context(user_agent=UA, viewport={"width": 1280, "height": 900})
            await ctx.route("**/*", _guard)
            page = await ctx.new_page()
            resp = await page.goto(link["url"], wait_until="domcontentloaded", timeout=30000)
            await _settle(page)
            d = await page.evaluate(GRID_JS if link["platform"] == "instagram" else PAGE_JS)
            if _blocked(resp.status if resp else 0, d["title"] + " " + d["text"][:600]):
                src.status, src.note = "blocked", f"{link['name']} showed a bot check to a logged-out visitor, so we left it."
                await browser.close()
                return src
            src.title, src.links = d["title"], list(dict.fromkeys(d["links"]))[:5]
            if link["platform"] == "instagram":
                _instagram_profile(src, d)
            else:
                src.bio = d["desc"] or d["text"][:300]
            for raw in d["posts"][:MAX_POSTS]:
                k = len(src.posts)
                path = out / f"{k:02d}.jpg"
                if not await asyncio.to_thread(_save, raw["img"], path):
                    continue
                # A grid link reads /<author>/p/<id>/; a collab or tagged post has someone else as author.
                seg = [x for x in urlparse(raw["url"]).path.lower().split("/") if x]
                owner = not (link["platform"] == "instagram" and src.handle and seg
                             and seg[0] not in ("p", "reel") and seg[0] != src.handle.lower())
                src.posts.append(Post(url=raw["url"], image=str(path), remote=raw["img"], alt=raw["alt"],
                                      video="/reel/" in raw["url"] or raw["alt"].startswith("Video by"),
                                      owner=owner, source=link["name"], date=_date(raw["alt"])))
            # The caption and the likes are on each post's own page. Only the account's own posts.
            if link["platform"] == "instagram":
                for post in src.posts:
                    if not post.owner:
                        continue
                    try:
                        await page.goto(post.url, wait_until="domcontentloaded", timeout=20000)
                        try:
                            await page.wait_for_load_state("networkidle", timeout=6000)
                        except Exception:
                            pass
                        _caption(post, await page.evaluate(POST_JS))
                    except Exception as e:  # one slow post shouldn't sink the read
                        print(f"source: skipped {post.url}: {e!r}"[:200])
            await browser.close()
    except BlockedURL:
        raise
    except Exception as e:
        src.status, src.note = "failed", f"Couldn't open {link['name']}: {type(e).__name__}."
        return src
    if not src.posts:
        src.status = "empty"
        src.note = src.note or f"{link['name']} didn't show any posts to a logged-out visitor."
    return src


def _date(alt: str) -> str:
    m_ = re.search(r"\bon ([A-Z][a-z]+ \d{1,2}, \d{4})", alt)
    return m_.group(1) if m_ else ""


def _instagram_profile(src: Source, d: dict) -> None:
    # "957 Followers, 1,627 Following, 83 Posts - 8 AM Fashion (@shop8amfashion) on Instagram: "bio...""
    desc = d["desc"] or ""
    f = re.match(r"([\d.,]+[KkMm]?) Followers", desc)
    src.followers = f.group(1) if f else ""
    b = re.search(r'on Instagram:\s*"(.*)', desc, re.S)
    src.bio = b.group(1).rstrip('"').strip() if b else ""


def _caption(post: Post, desc: str) -> None:
    # '18 likes, 4 comments - shop8amfashion on September 17, 2026: "caption". '
    lk = re.match(r"([\d.,]+[KkMm]?) likes?", desc)
    cm = re.search(r"([\d.,]+[KkMm]?) comments?", desc)
    post.likes = _count(lk.group(1)) if lk else None
    post.comments = _count(cm.group(1)) if cm else None
    c = re.search(r':\s*"(.*)"\.?\s*$', desc, re.S)
    post.caption = (c.group(1) if c else "").strip()[:600]
    if not post.date:
        post.date = _date(" on " + desc.split(" on ", 1)[-1]) if " on " in desc else ""


CLASSIFY_SCHEMA = {
    "type": "object", "additionalProperties": False, "required": ["posts"],
    "properties": {"posts": {"type": "array", "items": {
        "type": "object", "additionalProperties": False,
        "required": ["index", "kind", "product", "subject", "why"],
        "properties": {
            "index": {"type": "integer"},
            "kind": {"type": "string", "enum": KINDS},
            "product": {"type": "string",
                        "description": "the item's name if the caption, the picture or the shop's catalogue names it, "
                                       "else a plain description ('green kimono jacket'); '' if not a product"},
            "subject": {"type": "string",
                        "description": "the product as a short noun phrase for an object segmenter: 'kimono jacket', "
                                       "'linen shirt'; '' if not a product"},
            "why": {"type": "string", "description": "under 12 words: what you see that decided it"},
        },
    }}},
}

CLASSIFY_PROMPT = """These are recent posts from {who}, a small business ({about}). Images are \
numbered 0 to {last} in the order given; each post's caption and details are below. Sort every \
post so a makeover crew knows which ones show something the business sells:

- product: one item the business sells, clearly seen on its own (flat lay, hanger, shelf, table, \
packshot). The photo crew could reshoot it.
- worn: an item the business sells, being worn or used by a person, and the item is clearly visible.
- lifestyle: mood, place or people where no single product is the point.
- event: a market, pop-up, opening, a flyer or invitation to come somewhere.
- behind_the_scenes: making, sewing, packing, the studio, the team.
- text_graphic: mostly words (an announcement, a quote, a sale banner), even with a product behind.
- repost: another account's content (a customer, a collab, a feature).
- other: anything else.

Judge the picture and the caption together: a caption that invites people to a market makes it \
an event even if clothes are in the shot. Name the product from the caption or the shop's own \
catalogue when they name it; never invent a price or a name.

The shop's catalogue, for names: {catalogue}

{posts}"""


def classify(sources: list[Source], profile_hint: str, catalogue: list[str]) -> None:
    """Spark sorts every read post, in place."""
    posts = [p for s in sources for p in s.posts]
    if not posts:
        return
    who = ", ".join(f"{s.name} @{s.handle}" if s.handle else s.name for s in sources if s.posts)
    lines = []
    for k, p in enumerate(posts):
        bits = [f"[{k}] {'video cover' if p.video else 'photo'}", p.date and f"posted {p.date}",
                not p.owner and "posted by ANOTHER account", p.likes is not None and f"{p.likes} likes",
                p.caption and f'caption: "{p.caption[:300]}"', p.alt and f"alt: {p.alt[:200]}"]
        lines.append(" · ".join(b for b in bits if b))
    raw = m.ask(CLASSIFY_PROMPT.format(who=who, about=profile_hint or "unknown", last=len(posts) - 1,
                                       catalogue=", ".join(catalogue[:40]) or "none found",
                                       posts="\n".join(lines)),
                images=[p.image for p in posts], schema=CLASSIFY_SCHEMA, effort="low", max_tokens=16000)
    for row in json.loads(raw)["posts"]:
        if 0 <= row["index"] < len(posts):
            p = posts[row["index"]]
            p.kind, p.product, p.subject, p.why = row["kind"], row["product"], row["subject"], row["why"]
            if not p.owner and p.kind in USABLE:  # someone else's photo: context only
                p.kind = "repost"


def usable(sources: list[Source], limit: int = 8) -> list[Post]:
    """Product photos from the feeds, best first: products on their own, then worn, most liked first,
    one per named product."""
    rank = {"product": 0, "worn": 1}
    pool = sorted((p for s in sources for p in s.posts if p.kind in USABLE),
                  key=lambda p: (rank[p.kind], -(p.likes or 0)))
    out, names = [], set()
    for p in pool:
        key = p.product.lower().strip()
        if key and key in names:
            continue
        names.add(key)
        out.append(p)
    return out[:limit]


def links_for(site_socials: dict[str, str], added: list[str]) -> list[dict]:
    """The owner's links, plus the Instagram their own site links to when they didn't add one.
    Deduplicated, at most MAX_SOURCES."""
    links: list[dict] = []
    for url in added:
        try:
            r = recognise(url)
        except BlockedURL:
            continue
        if not any(same(r, x) for x in links):
            links.append(r)
    ig = site_socials.get("instagram")
    if ig and not any(x["platform"] == "instagram" for x in links):
        try:
            r = recognise(ig)
            if r["handle"]:
                links.append({**r, "linked_from_site": True})
        except BlockedURL:
            pass
    return links[:MAX_SOURCES]


async def read_all(links: list[dict], out: Path) -> list[Source]:
    """One at a time: polite to the platforms, and each is quick."""
    found = []
    for k, link in enumerate(links):
        try:
            found.append(await read(link, out / f"{k}_{link['platform']}"))
        except BlockedURL as e:
            found.append(Source(url=link["url"], platform=link["platform"], name=link["name"],
                                handle=link["handle"], status="failed", note=str(e)))
    return found
