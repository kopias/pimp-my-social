"""Record a demo of Pimp My Social making over a site, end to end, with Playwright.

    uv run scripts/serve.py --demo &            # the app, allowed to reach localhost
    (cd demo/marigold-lane && python3 -m http.server 8765 --bind 127.0.0.1) &
    uv run scripts/record_demo.py http://127.0.0.1:8765/ --pick 0

Everything on screen is real: the app runs the full pipeline against the URL.
Playwright records the browser; the long waits (Wonder coding the site, the
studio) are sped up afterwards with --fast, so the cut shows the whole run
without the dead air. Writes out/demo/<name>.mp4 (and the raw .webm).
"""

from __future__ import annotations

import argparse
import json
import subprocess
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "out" / "demo"

# A visible cursor: Playwright's recording doesn't draw the real one.
CURSOR_JS = """
(() => {
  const c = document.createElement('div');
  c.style.cssText = 'position:fixed;z-index:99999;width:22px;height:22px;border-radius:50%;' +
    'background:rgba(255,75,31,.85);border:2px solid white;box-shadow:0 2px 8px rgba(0,0,0,.3);' +
    'pointer-events:none;transform:translate(-50%,-50%);transition:transform .08s;left:-50px;top:-50px';
  const add = () => document.body && document.body.append(c);
  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', add) : add();
  addEventListener('mousemove', (e) => { c.style.left = e.clientX + 'px'; c.style.top = e.clientY + 'px'; }, true);
  addEventListener('mousedown', () => (c.style.transform = 'translate(-50%,-50%) scale(.7)'), true);
  addEventListener('mouseup', () => (c.style.transform = 'translate(-50%,-50%)'), true);
})();
"""

marks: list[tuple[str, float]] = []  # (label, seconds since recording began)
t0 = 0.0


def mark(label: str) -> None:
    marks.append((label, round(time.monotonic() - t0, 2)))
    print(f"{marks[-1][1]:7.1f}s  {label}")


def glide(page: Page, selector: str, click: bool = True) -> None:
    loc = page.locator(selector).first
    loc.wait_for(state="visible", timeout=30_000)
    loc.evaluate("e => e.scrollIntoView({block: 'center', behavior: 'smooth'})")
    page.wait_for_timeout(450)
    box, last = loc.bounding_box(), None
    for _ in range(20):  # a long smooth scroll can still be moving: wait until it settles
        if box == last:
            break
        page.wait_for_timeout(150)
        last, box = box, loc.bounding_box()
    if not box:
        return
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=18)
    page.wait_for_timeout(250)
    if click:  # a real click at the cursor, so the recording shows what happened
        page.mouse.down()
        page.mouse.up()


def main() -> None:
    global t0
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("url", help="the site to make over")
    p.add_argument("--app", default="http://127.0.0.1:8000")
    p.add_argument("--channels", default="facebook,linkedin,x", help="extra channels to click on")
    p.add_argument("--vibe", default="warm", help="style tags to click, comma-separated")
    p.add_argument("--formats", default="", help="Remix-a-hit formats to click, comma-separated names")
    p.add_argument("--pick", type=int, default=0, help="which paint job card to choose")
    p.add_argument("--name", default="pimp-my-social-demo")
    p.add_argument("--fast", type=float, default=12, help="speed-up for the waiting stretches")
    args = p.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="chrome")
        ctx = browser.new_context(viewport={"width": 1440, "height": 900},
                                  record_video_dir=str(OUT / "raw"),
                                  record_video_size={"width": 1440, "height": 900})
        ctx.add_init_script(CURSOR_JS)
        page = ctx.new_page()
        t0 = time.monotonic()
        page.goto(args.app, wait_until="networkidle")
        mark("splash")
        page.wait_for_timeout(1500)

        glide(page, "#url")
        page.keyboard.type(args.url, delay=55)
        page.wait_for_timeout(400)
        for ch in [c for c in args.channels.split(",") if c]:
            label = {"facebook": "Facebook", "linkedin": "LinkedIn", "x": "X", "instagram": "Instagram",
                     "tiktok": "TikTok"}[ch]
            glide(page, f"#channels .chip:text-is('{label}')")
            page.wait_for_timeout(200)
        for v in [v for v in args.vibe.split(",") if v]:
            glide(page, f"#tags .chip:text-is('{v}')")
            page.wait_for_timeout(200)
        for f in [f for f in args.formats.split(",") if f]:
            glide(page, f"#formats .chip:text-is('{f}')")
            page.wait_for_timeout(250)
        glide(page, "#consent")
        page.wait_for_timeout(500)
        glide(page, "#goBtn")
        mark("submitted")

        page.wait_for_selector("#scorebox:not([hidden])", timeout=240_000)
        mark("scorecard")
        page.mouse.move(700, 600, steps=10)
        page.wait_for_timeout(3500)
        page.wait_for_selector("#choose:not([hidden]) .dcard", timeout=600_000)
        page.wait_for_timeout(1500)  # let the previews load and the page scroll
        mark("choose")
        page.wait_for_timeout(4000)
        cards = page.locator(".dcard")
        for i in range(cards.count()):  # hover over each option
            b = cards.nth(i).bounding_box()
            if b:
                page.mouse.move(b["x"] + b["width"] / 2, b["y"] + b["height"] / 3, steps=14)
                page.wait_for_timeout(900)
        glide(page, f".dcard >> nth={args.pick}")
        mark("building")

        page.wait_for_selector("#v-reveal.on", timeout=1_500_000)
        mark("reveal")
        page.wait_for_timeout(2500)
        slider = page.locator("#slider").bounding_box()
        y = slider["y"] + slider["height"] / 2
        page.mouse.move(slider["x"] + slider["width"] * 0.5, y, steps=8)
        page.mouse.down()
        for frac in (0.15, 0.85, 0.5):
            page.mouse.move(slider["x"] + slider["width"] * frac, y, steps=30)
            page.wait_for_timeout(700)
        page.mouse.up()
        page.wait_for_timeout(800)

        def show_tab(name: str, linger: int = 4000, scroll: int = 0) -> None:
            if page.locator(f".tab:text-is('{name}')").count() == 0:
                return
            glide(page, f".tab:text-is('{name}')")
            page.wait_for_timeout(600)
            page.locator(".tabs").scroll_into_view_if_needed()
            page.evaluate("window.scrollBy({top: 380, behavior: 'smooth'})")
            page.wait_for_timeout(linger)
            if scroll:
                page.mouse.wheel(0, scroll)
                page.wait_for_timeout(2000)

        mark("tour")
        show_tab("Website", 3000)
        frame = page.frame_locator("#p-site iframe")
        for _ in range(6):  # scroll the new site inside its frame
            page.mouse.move(720, 640)
            page.mouse.wheel(0, 650)
            page.wait_for_timeout(900)
        show_tab("Photos", 5000, 600)
        show_tab("Logo", 4500)
        show_tab("What changed", 5000)
        if page.locator(".tab:text-is('Remixes')").count():
            show_tab("Remixes", 800)
            vids = page.locator("#p-remixes video")
            for i in range(vids.count()):
                vids.nth(i).scroll_into_view_if_needed()
                page.evaluate("(i) => { const v = document.querySelectorAll('#p-remixes video')[i];"
                              " v.muted = true; v.currentTime = 0; v.play(); }", i)
                page.wait_for_timeout(1500)
                page.mouse.wheel(0, 260)
                page.wait_for_timeout(11000)
        show_tab("Instagram", 2500)
        posts = page.locator("#p-instagram .grid3 img")
        for i in range(min(3, posts.count())):
            glide(page, f"#p-instagram .grid3 img >> nth={i}")
            page.wait_for_timeout(1300)
        for name in ("Facebook", "LinkedIn", "X"):
            show_tab(name, 2500)
        show_tab("Report", 3000)
        for _ in range(4):
            page.mouse.move(720, 640)
            page.mouse.wheel(0, 700)
            page.wait_for_timeout(900)
        show_tab("Brand skill", 3500, 900)
        show_tab("Download", 2500)
        glide(page, ".dl", click=False)
        page.wait_for_timeout(2000)
        mark("end")
        raw = Path(page.video.path())
        ctx.close()
        browser.close()

    webm = OUT / f"{args.name}.webm"
    raw.replace(webm)
    (OUT / f"{args.name}.marks.json").write_text(json.dumps(marks, indent=1))
    cut(webm, OUT / f"{args.name}.mp4", args.fast)


def cut(webm: Path, mp4: Path, fast: float) -> None:
    """Speed up the two long waits (garage -> choose, build -> reveal); keep the rest 1x."""
    m = dict(marks)
    segs = [(0, m["scorecard"] + 4, 1), (m["scorecard"] + 4, m["choose"], fast),
            (m["choose"], m["building"] + 3, 1), (m["building"] + 3, m["reveal"], fast),
            (m["reveal"], m["end"] + 1, 1)]
    parts, chain = [], []
    for i, (a, b, speed) in enumerate(segs):
        if b <= a:
            continue
        parts.append(f"[0:v]trim=start={a}:end={b},setpts=(PTS-STARTPTS)/{speed}[s{i}]")
        chain.append(f"[s{i}]")
    graph = ";".join(parts) + f";{''.join(chain)}concat=n={len(chain)}:v=1:a=0,fps=30[v]"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", str(webm), "-filter_complex", graph,
                    "-map", "[v]", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(mp4)], check=True)
    print(f"wrote {mp4.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
