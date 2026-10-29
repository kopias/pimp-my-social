"""Refresh the inspiration screenshots in inspo/shots/ (kept out of git: they're the brands' images).

    uv run scripts/capture_inspo.py            # every reference
    uv run scripts/capture_inspo.py toteme bode

Two frames per site: the first screen, and one scroll down. Cookie banners are
dismissed where a button says Accept or Close; sites behind a bot check are skipped.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pms.inspo import REFS, ROOT  # noqa: E402

OUT = ROOT / "shots"


async def one(browser, prefix: str, url: str) -> None:
    ctx = await browser.new_context(viewport={"width": 1440, "height": 900})
    page = await ctx.new_page()
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        await page.wait_for_timeout(5000)
        for sel in ["button:has-text('Accept')", "[aria-label='Close']", "button:has-text('Close')"]:
            try:
                await page.locator(sel).first.click(timeout=800)
            except Exception:
                pass
        await page.wait_for_timeout(1000)
        await page.screenshot(path=OUT / f"{prefix}_1.jpg", quality=70)
        await page.mouse.wheel(0, 1400)
        await page.wait_for_timeout(1800)
        await page.screenshot(path=OUT / f"{prefix}_2.jpg", quality=70)
        print("captured", prefix)
    except Exception as e:
        print("skipped", prefix, repr(e)[:120])
    await ctx.close()


async def main(ids: list[str]) -> None:
    OUT.mkdir(exist_ok=True)
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(channel="chrome")
        await asyncio.gather(*[one(browser, REFS[i][1], REFS[i][2]) for i in ids])
        await browser.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or list(REFS)))
