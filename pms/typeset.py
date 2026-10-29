"""Type, set by a browser: posters, captions and end cards as HTML, screenshotted.

Image models garble lettering, and Pillow sets type like a spreadsheet. A real
browser gets kerning, ligatures, the direction's own web fonts and text-wrap
balance for free, and restyling is a CSS edit. Same discipline as the Loreto
"got skills?" posters: the model makes the photograph, the browser sets the words.
"""

from __future__ import annotations

import shutil
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

MONO = "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500&display=swap"


def render(pages: list[dict]) -> list[Path]:
    """Each page: {html, css, out, w, h, transparent?, fonts?, assets?}. One browser for the lot.

    `assets` are local files the page refers to by bare name; they're copied next to it."""
    done = []
    work = Path(tempfile.mkdtemp(prefix="typeset-"))
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome")
            for k, pg in enumerate(pages):
                for a in pg.get("assets", []):
                    shutil.copy(a, work / Path(a).name)
                links = "".join(f'<link rel="stylesheet" href="{u}">' for u in [*pg.get("fonts", []), MONO])
                bg = "transparent" if pg.get("transparent") else "#000"
                f = work / f"page{k}.html"
                f.write_text(f"""<!doctype html><meta charset="utf-8">{links}
<style>html,body{{margin:0;background:{bg}}}
#p{{position:relative;width:{pg['w']}px;height:{pg['h']}px;overflow:hidden;
  -webkit-font-smoothing:antialiased;font-feature-settings:"kern","liga"}}
{pg['css']}</style><div id="p">{pg['html']}</div>""")
                page = browser.new_page(viewport={"width": pg["w"], "height": pg["h"]})
                page.goto(f.as_uri())
                page.evaluate("document.fonts.ready")
                page.wait_for_timeout(150)
                out = Path(pg["out"])
                out.parent.mkdir(parents=True, exist_ok=True)
                page.locator("#p").screenshot(path=str(out), omit_background=bool(pg.get("transparent")))
                page.close()
                done.append(out)
            browser.close()
    finally:
        shutil.rmtree(work, ignore_errors=True)
    return done
