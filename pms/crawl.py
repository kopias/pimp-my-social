"""The inspection: render a business's site the way a visitor sees it and take notes.

Chrome (via Playwright) renders the homepage and a few key inner pages, so
JavaScript-built sites work too. We keep what the makeover needs: the words, the
product photos, the colours and fonts actually on screen, any structured data,
the social links, and the agent-facing files (robots.txt, sitemap.xml, llms.txt).
Plus before screenshots, desktop and phone, for the reveal.

Only public pages, a handful of them, one at a time, and never anything on a
private network: the URL comes from a stranger on the internet.
"""

from __future__ import annotations

import asyncio
import ipaddress
import json
import os
import re
import socket
from dataclasses import asdict, dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from playwright.async_api import Route, async_playwright

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/141.0 Safari/537.36 PimpMySocial/0.1")
MAX_PAGES = 5  # homepage + 4 inner pages
INNER_HINTS = ("shop", "product", "menu", "service", "about", "collection", "store", "work",
               "portfolio", "pricing", "offer", "class", "lesson", "contact")
SOCIAL_HOSTS = {"instagram.com": "instagram", "tiktok.com": "tiktok", "facebook.com": "facebook",
                "linkedin.com": "linkedin", "x.com": "x", "twitter.com": "x",
                "youtube.com": "youtube", "pinterest.com": "pinterest"}


class BlockedURL(ValueError):
    pass


def check_public(url: str) -> str:
    """Normalise a user-typed URL and refuse anything that isn't a public web host."""
    url = url.strip()
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    u = urlparse(url)
    if u.scheme not in ("http", "https") or not u.hostname:
        raise BlockedURL("That doesn't look like a website address.")
    _public_host(u.hostname)
    return url


def _public_host(host: str) -> None:
    if os.getenv("PMS_ALLOW_PRIVATE") == "1":  # local development only: the demo site on localhost
        return
    try:
        infos = socket.getaddrinfo(host, None)
    except socket.gaierror:
        raise BlockedURL(f"Couldn't find {host}. Check the address.") from None
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise BlockedURL("That address points at a private network.")


_host_ok: dict[str, bool] = {}


def _allowed(url: str) -> bool:
    host = urlparse(url).hostname
    if not host or urlparse(url).scheme not in ("http", "https"):
        return urlparse(url).scheme in ("data", "blob")
    if host not in _host_ok:
        try:
            _public_host(host)
            _host_ok[host] = True
        except BlockedURL:
            _host_ok[host] = False
    return _host_ok[host]


@dataclass
class Image:
    url: str
    alt: str
    width: int
    height: int
    page: str

    @property
    def area(self) -> int:
        return self.width * self.height


@dataclass
class Page:
    url: str
    title: str
    description: str
    headings: list[str]
    text: str


@dataclass
class Site:
    url: str
    final_url: str
    name_guess: str
    pages: list[Page] = field(default_factory=list)
    images: list[Image] = field(default_factory=list)
    logo: str | None = None
    colors: list[str] = field(default_factory=list)  # most used first
    fonts: list[str] = field(default_factory=list)
    jsonld: list[dict] = field(default_factory=list)
    socials: dict[str, str] = field(default_factory=dict)
    meta: dict[str, str] = field(default_factory=dict)  # og:*, twitter:*, theme-color...
    signals: dict = field(default_factory=dict)  # homepage: lang, canonical, h1, alt text...
    perf: dict = field(default_factory=dict)  # homepage: load_ms, lcp_ms, bytes, requests
    robots_txt: str | None = None
    sitemap: bool = False
    llms_txt: bool = False
    shots: dict[str, str] = field(default_factory=dict)  # name -> png path

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=1)

    @classmethod
    def from_json(cls, s: str) -> "Site":
        d = json.loads(s)
        d["pages"] = [Page(**p) for p in d["pages"]]
        d["images"] = [Image(**i) for i in d["images"]]
        return cls(**d)


# Runs in the page: everything we want from the rendered DOM in one go.
EXTRACT_JS = r"""
() => {
  const abs = (u) => { try { return new URL(u, location.href).href } catch { return null } };
  const text = (document.querySelector('main') || document.body).innerText || '';
  const headings = [...document.querySelectorAll('h1,h2,h3')].map(h => h.innerText.trim())
    .filter(Boolean).slice(0, 40);
  const meta = {};
  for (const m of document.querySelectorAll('meta[property],meta[name]')) {
    const k = m.getAttribute('property') || m.getAttribute('name');
    if (/^(og:|twitter:|description$|theme-color$|keywords$)/.test(k)) meta[k] = m.content || '';
  }
  const imgs = [...document.images].map(i => ({ url: abs(i.currentSrc || i.src), alt: i.alt || '',
    width: i.naturalWidth, height: i.naturalHeight,
    logo: /logo/i.test((i.className || '') + ' ' + i.alt + ' ' + (i.id || '') + ' ' + i.src) }));
  const links = [...document.querySelectorAll('a[href]')].map(a => ({ href: abs(a.getAttribute('href')),
    text: (a.innerText || '').trim().slice(0, 60) }));
  const jsonld = [...document.querySelectorAll('script[type="application/ld+json"]')]
    .map(s => s.textContent);
  // Colours and fonts as rendered, weighted by how much of the page uses them.
  const colors = {}, fonts = {};
  const add = (o, k, w) => { if (k) o[k] = (o[k] || 0) + w };
  for (const el of [...document.querySelectorAll('body, body *')].slice(0, 2500)) {
    const r = el.getBoundingClientRect();
    if (!r.width || !r.height) continue;
    const cs = getComputedStyle(el), area = Math.min(r.width * r.height, 400000);
    if (cs.backgroundColor && !/rgba\(.*, 0\)$/.test(cs.backgroundColor) && cs.backgroundColor !== 'transparent')
      add(colors, cs.backgroundColor, area);
    if (el.childNodes.length && [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim())) {
      add(colors, cs.color, 2000);
      add(fonts, cs.fontFamily.split(',')[0].replace(/["']/g, '').trim(), 1);
    }
  }
  const icon = document.querySelector('link[rel~="icon"], link[rel="apple-touch-icon"]');
  const canon = document.querySelector('link[rel="canonical"]');
  const all = [...document.images].filter(i => i.naturalWidth > 40);
  const html = document.documentElement.outerHTML;
  const signals = {
    lang: document.documentElement.lang || '',
    canonical: canon ? canon.href : '',
    viewport: !!document.querySelector('meta[name="viewport"]'),
    h1: document.querySelectorAll('h1').length,
    images: all.length, images_no_alt: all.filter(i => !(i.alt || '').trim()).length,
    faq: !!document.querySelector('details > summary') || /\b(faq|frequently asked)/i.test(headings.join(' ')),
    webmcp: /modelContext/.test(html),
  };
  return { title: document.title, text: text.slice(0, 6000), headings, meta, imgs, links, jsonld,
           colors, fonts, icon: icon ? abs(icon.href) : null, signals };
}
"""


# Homepage speed as this browser saw it (desktop, no throttling): a before/after
# comparison on the same machine, not a lab score.
PERF_JS = r"""
async () => {
  const nav = performance.getEntriesByType('navigation')[0] || {};
  const res = performance.getEntriesByType('resource');
  const lcp = await new Promise((ok) => {
    let v = 0;
    try {
      new PerformanceObserver((l) => { for (const e of l.getEntries()) v = e.startTime; })
        .observe({ type: 'largest-contentful-paint', buffered: true });
    } catch {}
    setTimeout(() => ok(v), 300);
  });
  const bytes = res.reduce((a, r) => a + (r.transferSize || r.encodedBodySize || 0), 0)
    + (nav.transferSize || 0);
  return { load_ms: Math.round(nav.loadEventEnd || nav.duration || 0), lcp_ms: Math.round(lcp),
           bytes, requests: res.length + 1 };
}
"""


def _hex(rgb: str) -> str | None:
    m = re.findall(r"[\d.]+", rgb)
    if len(m) < 3:
        return None
    return "#" + "".join(f"{int(float(x)):02x}" for x in m[:3])


def _pick_inner(links: list[dict], base: str) -> list[str]:
    host = urlparse(base).hostname
    seen, scored = set(), []
    for link in links:
        href = (link["href"] or "").split("#")[0]
        u = urlparse(href)
        if u.hostname != host or href in seen or href.rstrip("/") == base.rstrip("/"):
            continue
        if re.search(r"\.(pdf|jpe?g|png|zip|mp4)$|/(cart|login|account|checkout|wp-admin)", href, re.I):
            continue
        seen.add(href)
        hay = (u.path + " " + link["text"]).lower()
        score = sum(h in hay for h in INNER_HINTS)
        if score:
            scored.append((-score, len(u.path), href))
    return [h for *_, h in sorted(scored)][: MAX_PAGES - 1]


async def _guard(route: Route) -> None:
    if _allowed(route.request.url):
        await route.continue_()
    else:
        await route.abort()


async def inspect(url: str, out: Path) -> Site:
    url = check_public(url)
    out.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(channel="chrome")
        ctx = await browser.new_context(user_agent=UA, viewport={"width": 1440, "height": 900})
        await ctx.route("**/*", _guard)
        page = await ctx.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=30000)
        await _settle(page)
        final = page.url
        site = Site(url=url, final_url=final, name_guess="")
        await page.screenshot(path=str(out / "before_desktop.png"))
        site.shots["desktop"] = str(out / "before_desktop.png")

        home = await page.evaluate(EXTRACT_JS)
        _absorb(site, home, final)
        site.signals = home["signals"]
        site.perf = await page.evaluate(PERF_JS)
        site.name_guess = (home["meta"].get("og:site_name") or re.split(r"\s[|\-–—:]\s", home["title"])[0]
                           or urlparse(final).hostname).strip()

        for inner in _pick_inner(home["links"], final):
            try:
                await page.goto(inner, wait_until="domcontentloaded", timeout=20000)
                await _settle(page)
                _absorb(site, await page.evaluate(EXTRACT_JS), page.url)
            except Exception as e:  # one bad page shouldn't sink the inspection
                print(f"inspect: skipped {inner}: {e!r}"[:200])

        phone = await browser.new_context(user_agent=UA, viewport={"width": 390, "height": 844},
                                          device_scale_factor=2, is_mobile=True)
        await phone.route("**/*", _guard)
        pp = await phone.new_page()
        await pp.goto(final, wait_until="domcontentloaded", timeout=30000)
        await _settle(pp)
        await pp.screenshot(path=str(out / "before_phone.png"))
        site.shots["phone"] = str(out / "before_phone.png")
        await browser.close()

    _agent_files(site)
    site.images = _rank_images(site.images)
    (out / "site.json").write_text(site.to_json())
    return site


async def _settle(page) -> None:
    """Let lazy images and late scripts land: wait for the network, nudge a scroll."""
    try:
        await page.wait_for_load_state("networkidle", timeout=8000)
    except Exception:
        pass
    await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
    await asyncio.sleep(0.8)
    await page.evaluate("window.scrollTo(0, 0)")
    await asyncio.sleep(0.4)


def _absorb(site: Site, d: dict, url: str) -> None:
    site.pages.append(Page(url=url, title=d["title"], description=d["meta"].get("description", ""),
                           headings=d["headings"], text=d["text"]))
    for k, v in d["meta"].items():
        site.meta.setdefault(k, v)
    for i in d["imgs"]:
        if i["url"] and i["logo"] and not site.logo:
            site.logo = i["url"]
        elif i["url"] and i["width"] >= 300 and i["height"] >= 200:
            site.images.append(Image(url=i["url"], alt=i["alt"], width=i["width"],
                                     height=i["height"], page=url))
    if not site.logo and d["icon"]:
        site.logo = d["icon"]
    for raw in d["jsonld"]:
        try:
            site.jsonld.append(json.loads(raw))
        except (json.JSONDecodeError, TypeError):
            pass
    for link in d["links"]:
        host = (urlparse(link["href"] or "").hostname or "").removeprefix("www.")
        if host in SOCIAL_HOSTS:
            site.socials.setdefault(SOCIAL_HOSTS[host], link["href"])
    weights: dict[str, float] = {}
    for c, w in list(d["colors"].items()) + [(c, 0) for c in site.colors]:
        h = _hex(c)
        if h:
            weights[h] = weights.get(h, 0) + w
    site.colors = sorted(weights, key=weights.get, reverse=True)[:8]
    for f in sorted(d["fonts"], key=d["fonts"].get, reverse=True):
        if f and f not in site.fonts:
            site.fonts.append(f)
    site.fonts = site.fonts[:4]


def _rank_images(images: list[Image]) -> list[Image]:
    """Biggest first, one copy of each, no tracking pixels or sprites."""
    seen, out = set(), []
    for i in sorted(images, key=lambda i: i.area, reverse=True):
        key = re.sub(r"[?#].*$", "", i.url)
        key = re.sub(r"-\d+x\d+(?=\.\w+$)", "", key)  # WordPress size variants
        if key in seen or i.url.startswith("data:") or i.width / max(i.height, 1) > 4:
            continue
        seen.add(key)
        out.append(i)
    return out[:24]


def _agent_files(site: Site) -> None:
    root = f"{urlparse(site.final_url).scheme}://{urlparse(site.final_url).netloc}"
    def get(path: str) -> requests.Response | None:
        try:
            r = requests.get(root + path, headers={"User-Agent": UA}, timeout=10, allow_redirects=False)
            return r if r.status_code == 200 else None
        except requests.RequestException:
            return None
    r = get("/robots.txt")
    site.robots_txt = r.text[:5000] if r is not None and "<html" not in r.text[:500].lower() else None
    r = get("/sitemap.xml")
    site.sitemap = bool(r is not None and "<urlset" in r.text[:2000] or r is not None and "<sitemapindex" in r.text[:2000])
    r = get("/llms.txt")
    site.llms_txt = bool(r is not None and "<html" not in r.text[:500].lower() and r.text.strip())
