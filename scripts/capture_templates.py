"""Capture and measure the 25 template sites (inspo/templates/<id>/).

    uv run scripts/capture_templates.py            # all of them
    uv run scripts/capture_templates.py cos dior

Per site: the first desktop screen, two scrolls down, the first mobile screen
(shots, kept out of git: they're the brands' images), and measured.json: the fonts
sizes, colours and header geometry the browser actually computed. Measurements are
what the template skills are written from, so the type and spacing are numbers
not impressions. Sites behind a bot check are marked blocked.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pms.templates import ROOT, SOURCES  # noqa: E402

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/141.0.0.0 Safari/537.36")
DISMISS = ["#onetrust-accept-btn-handler", "button:has-text('Accept all')", "button:has-text('Accept All')",
           "button:has-text('Accept')", "button:has-text('Agree')", "button:has-text('I agree')",
           "button:has-text('Continue')", "button:has-text('No thanks')", "button:has-text('No, thanks')",
           "[aria-label='Close']", "[aria-label='close']", "button:has-text('Close')", "button:has-text('×')"]
BLOCKED = ["access denied", "just a moment", "attention required", "are you a robot", "pardon our",
           "request unsuccessful", "verify you are human", "403 forbidden", "blocked", "temporarily restricted", "page unavailable"]

# Newsletter modals, cookie bars and chat bubbles that survive the clicks: hide any
# fixed overlay that isn't the header, so the shot shows the design underneath.
UNCLUTTER = r"""() => {
  for (const e of document.querySelectorAll('body *')) {
    const s = getComputedStyle(e);
    if (s.position !== 'fixed' && s.position !== 'sticky') continue;
    const r = e.getBoundingClientRect();
    const isHeader = e.matches('header, header *, nav, [class*=header], [class*=Header]') && r.top < 140 && r.height < 200;
    if (isHeader) continue;
    const dialog = e.matches('[role=dialog], [aria-modal=true], iframe, [class*=modal], [class*=popup], [class*=klaviyo], [class*=cookie], [id*=cookie], [class*=consent], [id*=onetrust], [class*=chat]');
    if (dialog || r.width * r.height > innerWidth * innerHeight * 0.12 || r.top > innerHeight * 0.6) e.style.setProperty('display', 'none', 'important');
  }
  document.documentElement.style.overflow = 'auto'; document.body.style.overflow = 'auto';
}"""

MEASURE = r"""() => {
  const cs = (e) => getComputedStyle(e);
  const vis = (e) => { const r = e.getBoundingClientRect(); const s = cs(e);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && +s.opacity > 0.05; };
  const font = (e) => { if (!e) return null; const s = cs(e); return {
    family: s.fontFamily.split(',')[0].replace(/["']/g, '').trim(), stack: s.fontFamily, size: s.fontSize,
    weight: s.fontWeight, tracking: s.letterSpacing, transform: s.textTransform, line: s.lineHeight,
    style: s.fontStyle, color: s.color, text: (e.innerText || '').trim().slice(0, 80) }; };
  const first = (sels) => { for (const q of sels) for (const e of document.querySelectorAll(q)) if (vis(e) && (e.innerText||'').trim()) return e; return null; };
  // the biggest visible text on the first two screens = the display face
  const texts = [...document.querySelectorAll('h1,h2,h3,p,a,span,div,button')].filter(e =>
    vis(e) && e.children.length === 0 && (e.innerText||'').trim().length > 1 && e.getBoundingClientRect().top < 1800);
  const bySize = texts.map(e => [parseFloat(cs(e).fontSize), e]).sort((a,b) => b[0]-a[0]);
  const families = {};
  for (const e of texts) { const f = cs(e).fontFamily.split(',')[0].replace(/["']/g,'').trim(); families[f] = (families[f]||0) + 1; }
  const header = document.querySelector('header') || first(['[class*=header]','nav']);
  const hr = header ? header.getBoundingClientRect() : null;
  const logo = header && [...header.querySelectorAll('img,svg,a')].find(e => vis(e) &&
    /logo|brand|home/i.test((e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className) + ' ' + (e.getAttribute('aria-label')||'') + ' ' + (e.getAttribute('href')||'') + (e.alt||'')));
  const lr = logo ? logo.getBoundingClientRect() : null;
  const navLinks = header ? [...header.querySelectorAll('a,button')].filter(e => vis(e) && (e.innerText||'').trim()) : [];
  const imgs = [...document.querySelectorAll('img,video,picture')].filter(vis).map(e => e.getBoundingClientRect())
    .filter(r => r.top < 900).map(r => ({x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height)}))
    .sort((a,b) => b.w*b.h - a.w*a.h).slice(0, 6);
  const buttons = [...document.querySelectorAll('a,button')].filter(e => vis(e) && /shop|discover|explore|new|buy|view/i.test(e.innerText||'') && e.getBoundingClientRect().top < 1600).slice(0, 3)
    .map(e => { const s = cs(e); return {...font(e), bg: s.backgroundColor, border: s.border, radius: s.borderRadius, padding: s.padding}; });
  return {
    title: document.title, bg: cs(document.body).backgroundColor, htmlbg: cs(document.documentElement).backgroundColor,
    body: font(first(['p'])), nav: font(navLinks[0] || null), nav_count: navLinks.length,
    nav_labels: navLinks.slice(0, 14).map(e => e.innerText.trim().slice(0, 24)),
    largest: bySize.slice(0, 4).map(([, e]) => font(e)),
    families: Object.entries(families).sort((a,b) => b[1]-a[1]).slice(0, 6),
    header: hr ? {h: Math.round(hr.height), y: Math.round(hr.top), bg: cs(header).backgroundColor, position: cs(header).position} : null,
    logo: lr ? {x: Math.round(lr.left), w: Math.round(lr.width), h: Math.round(lr.height),
                centred: Math.abs(lr.left + lr.width/2 - innerWidth/2) < 60} : null,
    images: imgs, buttons, page_h: document.documentElement.scrollHeight };
}"""


async def dismiss(page) -> None:
    for sel in DISMISS:
        try:
            await page.locator(sel).first.click(timeout=600)
            await page.wait_for_timeout(300)
        except Exception:
            pass
    await page.keyboard.press("Escape")
    await page.evaluate(UNCLUTTER)


async def one(browser, tid: str, url: str, sem: asyncio.Semaphore) -> None:
    out = ROOT / tid
    out.mkdir(parents=True, exist_ok=True)
    async with sem:
        result: dict = {"id": tid, "url": url}
        try:
            ctx = await browser.new_context(viewport={"width": 1440, "height": 900}, user_agent=UA, locale="en-US")
            page = await ctx.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
            await page.wait_for_timeout(6000)
            await dismiss(page)
            await page.wait_for_timeout(1200)
            text = (await page.title() + " " + (await page.inner_text("body"))[:400]).lower()
            if any(b in text for b in BLOCKED) and len(text) < 600:
                result["blocked"] = text[:200]
            await page.screenshot(path=out / "desktop_1.jpg", quality=72)
            result["desktop"] = await page.evaluate(MEASURE)
            for k in (2, 3):
                await page.mouse.wheel(0, 900)
                await page.wait_for_timeout(1500)
                await page.screenshot(path=out / f"desktop_{k}.jpg", quality=72)
            await ctx.close()
            ctx = await browser.new_context(viewport={"width": 390, "height": 844}, user_agent=UA.replace(
                "Macintosh; Intel Mac OS X 10_15_7", "iPhone; CPU iPhone OS 18_0 like Mac OS X") + " Mobile",
                is_mobile=True, has_touch=True, device_scale_factor=2, locale="en-US")
            page = await ctx.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=45_000)
            await page.wait_for_timeout(5000)
            await dismiss(page)
            await page.wait_for_timeout(800)
            await page.screenshot(path=out / "mobile_1.jpg", quality=60)
            result["mobile"] = await page.evaluate(MEASURE)
            await ctx.close()
            print("captured", tid, "BLOCKED" if result.get("blocked") else "")
        except Exception as e:
            result["error"] = repr(e)[:200]
            print("failed", tid, repr(e)[:120])
        (out / "measured.json").write_text(json.dumps(result, indent=1))


async def main(ids: list[str], headed: bool) -> None:
    sem = asyncio.Semaphore(5)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(channel="chrome", headless=not headed)
        await asyncio.gather(*[one(browser, i, SOURCES[i], sem) for i in ids])
        await browser.close()


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    asyncio.run(main(args or list(SOURCES), "--headed" in sys.argv))
