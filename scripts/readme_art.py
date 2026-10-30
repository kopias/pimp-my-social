"""The README's pictures: a banner, the five models, and framed shots of a real makeover.

    uv run scripts/serve.py --demo          # in another terminal
    uv run scripts/readme_art.py 993e81e2fd --picker f1e60f387c

Every picture is set in the landing page's own type and paper, rendered by Chrome, and
cut out on a transparent ground with rounded corners, so the README reads the same in
GitHub's light and dark themes. Use the fictional Marigold Lane jobs: the repo is
public, and a real business isn't shown without asking.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import shutil
from pathlib import Path

from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs" / "readme"
APP = "http://localhost:8000"
FONTS = ("https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400"
         "&family=Hanken+Grotesk:wght@200;300;400;500;600&family=JetBrains+Mono:wght@400&display=swap")

MODELS = [
    ("Muse Spark 1.3", "Reads the site and the feed, writes the copy, sorts every post, judges every build"),
    ("Muse Wonder 1.0", "Designs and codes the new homepage on the chosen template"),
    ("Muse Image", "Reshoots the products, casts the campaign, redraws the logo"),
    ("SAM 3.1", "Cuts each product out, then checks the reshoot still shows it"),
    ("Muse Voice Transcribe", "Hears a popular post so its format can be remixed"),
]

# (file, number, kicker, title, italic, line, screenshot, crop top in CSS px)
SHOTS = [
    ("01-picker", "01", "The paint job", "Pick the one that", "feels like you.",
     "Your homepage, sketched three to six ways from 25 measured fashion-site templates, with your own words and photos.", "picker.png", 200),
    ("02-reveal", "02", "The reveal", "Before, and", "after.",
     "Drag across the new site. Every score comes from the same 17 checks run on the old site and the new one.", "reveal.png", 60),
    ("03-campaign", "03", "The campaign", "One idea,", "every post.",
     "A got-milk style campaign: posters, a still and a film, cast in the real products, every hand counted.", "tab-campaign.png", 120),
    ("04-photos", "04", "The photo studio", "Your products,", "reshot.",
     "SAM 3.1 cuts each product out, Muse Image reshoots it, and SAM checks it is still the same thing.", "tab-photos.png", 100),
    ("05-report", "05", "The report", "What changed,", "measured.",
     "What was missing, what was added, and a calculator for what it could be worth, on cited figures.", "report.png", 0),
    ("06-skill", "06", "The brand skill", "Your brand,", "in a file.",
     "Download it into Claude and everything it writes or designs next stays in your voice, colours and facts.", "tab-brand-skill.png", 100),
]

BASE_CSS = """
:root { --paper:#f7f5f0; --paper2:#eeebe4; --ink:#121212; --muted:#7a766e; --line:rgba(18,18,18,.12); --hot:#c8361b;
  --serif:"Cormorant Garamond",serif; --sans:"Hanken Grotesk",sans-serif; --mono:"JetBrains Mono",monospace; }
* { box-sizing:border-box; margin:0; }
html, body { background:transparent; -webkit-font-smoothing:antialiased; }
.card { position:relative; overflow:hidden; border-radius:28px; background:var(--paper); color:var(--ink); font-family:var(--sans); isolation:isolate; }
.card::before { content:""; position:absolute; z-index:-1; right:-160px; top:-260px; width:820px; aspect-ratio:1; border-radius:50%;
  background:conic-gradient(from 40deg, #c8361b, #e7a541, #f2dcc6 35%, #d9b8a0 60%, #b2675a 80%, #c8361b);
  filter:blur(90px) saturate(1.1); opacity:.3; }
.card::after { content:""; position:absolute; z-index:-1; inset:0;
  background-image:linear-gradient(to right, rgba(18,18,18,.05) 1px, transparent 1px); background-size:calc(100% / 12) 100%;
  -webkit-mask-image:radial-gradient(ellipse 70% 70% at 40% 30%, #000 20%, transparent 80%); }
.dots { position:absolute; z-index:-1; left:-30px; bottom:-30px; width:420px; height:300px;
  background-image:radial-gradient(rgba(200,54,27,.3) 1.1px, transparent 1.6px); background-size:13px 13px;
  -webkit-mask-image:radial-gradient(circle at 0% 100%, #000 0%, transparent 70%); }
.label { font:500 13px/1.4 var(--sans); letter-spacing:.2em; text-transform:uppercase; color:var(--muted); }
.brand { font:500 15px var(--sans); letter-spacing:.36em; text-transform:uppercase; }
.brand i, .hot { font-style:normal; color:var(--hot); }
"""


def page(body: str, css: str) -> str:
    return (f'<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="{FONTS}">'
            f"<style>{BASE_CSS}{css}</style></head><body>{body}</body></html>")


BANNER_CSS = """
.card { width:1600px; height:800px; display:grid; grid-template-columns:1fr 1.02fr; }
.top { position:absolute; left:72px; right:72px; top:44px; display:flex; justify-content:space-between; align-items:center;
  border-bottom:1px solid var(--line); padding-bottom:22px; }
.copy { padding:150px 0 0 72px; }
h1 { font:300 164px/.84 var(--serif); letter-spacing:-.04em; margin:18px 0 28px; }
h1 i { color:var(--hot); }
.lede { font:400 21px/1.5 var(--sans); color:#3a3833; max-width:540px; }
.meta { position:absolute; left:72px; bottom:44px; display:flex; gap:10px; flex-wrap:nowrap; }
.meta span { white-space:nowrap; font:500 11px var(--sans); letter-spacing:.14em; text-transform:uppercase; padding:9px 14px; border-radius:999px;
  background:rgba(255,255,255,.55); border:1px solid rgba(255,255,255,.85); box-shadow:0 10px 24px -16px rgba(70,35,10,.4); }
.art { position:relative; }
.shot { position:absolute; border-radius:16px; overflow:hidden; background:#fff; border:1px solid rgba(18,18,18,.1); }
.shot img { display:block; width:100%; height:100%; object-fit:cover; object-position:top; }
.shot .tag { position:absolute; top:12px; left:12px; font:500 11px var(--sans); letter-spacing:.18em; text-transform:uppercase;
  background:var(--paper); padding:6px 10px; border-radius:6px; }
.before { width:500px; height:330px; left:30px; top:150px; transform:rotate(-5deg); filter:saturate(.7);
  box-shadow:0 30px 60px -30px rgba(70,35,10,.45); }
.after { width:600px; height:400px; left:130px; top:280px; transform:rotate(2deg);
  box-shadow:16px 16px 0 -1px #efe2d2, 32px 32px 0 -1px #ead6c2, 0 60px 100px -40px rgba(70,35,10,.6); }
.after .tag { background:var(--ink); color:var(--paper); }
.phone { position:absolute; width:150px; height:318px; left:620px; top:420px; border-radius:26px; overflow:hidden;
  border:5px solid var(--ink); background:#fff; transform:rotate(6deg); box-shadow:0 40px 60px -30px rgba(0,0,0,.5); }
.phone img { width:100%; height:100%; object-fit:cover; object-position:top; display:block; }
.score { position:absolute; left:470px; top:120px; padding:16px 22px 18px; border-radius:20px; background:rgba(255,255,255,.62);
  border:1px solid rgba(255,255,255,.9); backdrop-filter:blur(14px); box-shadow:0 30px 50px -30px rgba(70,35,10,.5); transform:rotate(3deg); }
.score b { display:block; font:200 72px/.9 var(--sans); letter-spacing:-.05em; }
.score b s { color:var(--muted); text-decoration-thickness:2px; text-decoration-color:var(--hot); }
.score b em { font-style:normal; font-family:var(--serif); font-weight:300; color:var(--hot); margin:0 6px; }
"""


def banner(a: dict) -> str:
    chips = "".join(f"<span>{m}</span>" for m, _ in MODELS)
    return page(f"""<div class="card" id="c"><div class="dots"></div>
<div class="top"><span class="label">Episode 01 · Meta AI Developer Hackathon</span><span class="brand">Pimp My <i>Social</i></span>
<span class="label">Makeovers for small businesses</span></div>
<div class="copy"><div class="label">Your website in · a whole brand out</div>
<h1>Pimp my<br><i>social.</i></h1>
<p class="lede">Give it your website. Get back a new site built for search and AI agents, studio photos, a campaign, and a brand skill for Claude.</p></div>
<div class="art">
  <div class="shot before"><img src="{a['before']}"><span class="tag">Before</span></div>
  <div class="shot after"><img src="{a['after']}"><span class="tag">After</span></div>
  <div class="phone"><img src="{a['phone']}"></div>
  <div class="score"><span class="label">Score</span><b><s>{a['from']}</s><em>→</em>{a['to']}</b></div>
</div>
<div class="meta">{chips}</div></div>""", BANNER_CSS)


MODELS_CSS = """
.card { width:1600px; padding:56px 64px 60px; }
h2 { font:300 64px/1 var(--serif); letter-spacing:-.03em; margin:14px 0 36px; }
h2 i { color:var(--hot); }
.row { display:grid; grid-template-columns:repeat(5,1fr); gap:16px; }
.t { padding:24px 24px 28px; border-radius:20px; background:rgba(255,255,255,.5); border:1px solid rgba(255,255,255,.85);
  box-shadow:0 26px 50px -36px rgba(70,35,10,.45); }
.t .n { font:400 13px var(--mono); color:var(--hot); }
.t b { display:block; font:400 34px/1.05 var(--serif); letter-spacing:-.01em; margin:14px 0 10px; }
.t span { font:400 16px/1.5 var(--sans); color:#4a4741; }
"""


def models() -> str:
    tiles = "".join(f'<div class="t"><div class="n">0{i}</div><b>{m}</b><span>{why}</span></div>'
                    for i, (m, why) in enumerate(MODELS, 1))
    return page(f"""<div class="card" id="c"><div class="dots"></div><div class="label">Built on Meta's models</div>
<h2>Five models, <i>each with a job.</i></h2><div class="row">{tiles}</div></div>""", MODELS_CSS)


SHOT_CSS = """
.card { width:1600px; padding:52px 60px 60px; }
.head { display:grid; grid-template-columns:70px 1.35fr 1fr; gap:24px; align-items:end; margin-bottom:34px; }
.head .n { font:400 15px var(--mono); color:var(--hot); padding-bottom:12px; }
h2 { font:300 66px/.95 var(--serif); letter-spacing:-.03em; margin-top:10px; }
h2 i { color:var(--hot); }
.head p { font:400 20px/1.5 var(--sans); color:#4a4741; padding-bottom:8px; }
.frame { border-radius:18px; overflow:hidden; background:var(--paper); border:1px solid rgba(18,18,18,.1);
  box-shadow:14px 14px 0 -1px #efe2d2, 28px 28px 0 -1px #ead6c2, 0 50px 90px -40px rgba(70,35,10,.5); margin-right:28px; }
.bar { height:40px; display:flex; align-items:center; gap:8px; padding:0 16px; background:var(--paper); border-bottom:1px solid var(--line); }
.bar i { width:11px; height:11px; border-radius:50%; background:rgba(18,18,18,.14); }
.bar span { margin-left:16px; font:400 12px var(--mono); color:var(--muted); }
.view { height:820px; overflow:hidden; position:relative; }
.view img { position:absolute; left:0; width:100%; display:block; }
"""


def shot(n: str, kicker: str, title: str, italic: str, line: str, img: str, top: int) -> str:
    # the screenshots are 1440 CSS px wide; the frame shows them at 1480 - a hair over 1:1
    return page(f"""<div class="card" id="c"><div class="dots"></div>
<div class="head"><span class="n">{n}</span><div><div class="label">{kicker}</div><h2>{title} <i>{italic}</i></h2></div><p>{line}</p></div>
<div class="frame"><div class="bar"><i></i><i></i><i></i><span>pimp-my-social · {kicker.lower()}</span></div>
<div class="view" style="height:{min(820, (900 - top) * 1480 / 1440):.0f}px"><img src="{img}" style="top:-{top * 1480 / 1440:.0f}px"></div></div></div>""", SHOT_CSS)


async def capture(job: str, picker: str, raw: Path) -> None:
    """The app's own screens, at 2x, from the running server."""
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome")
        ctx = await b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=2)
        pg = await ctx.new_page()
        await pg.goto("about:blank"); await pg.goto(f"{APP}/#{picker}"); await pg.wait_for_timeout(5000)
        # the page glides down to the sketches; settle there with their heading in view
        await pg.evaluate("window.scrollTo(0, document.getElementById('choose').getBoundingClientRect().top + scrollY - 230)")
        await pg.wait_for_timeout(1200)
        await pg.screenshot(path=str(raw / "picker.png"))
        await pg.goto("about:blank"); await pg.goto(f"{APP}/#{job}"); await pg.wait_for_timeout(5000)
        await pg.screenshot(path=str(raw / "reveal.png"))
        for t in ("PHOTOS", "CAMPAIGN", "BRAND SKILL"):
            await pg.locator(".tab", has_text=t).first.click(); await pg.wait_for_timeout(2500)
            await pg.evaluate("window.scrollTo(0, document.querySelector('.tabs').getBoundingClientRect().top + scrollY - 70)")
            await pg.wait_for_timeout(800)
            await pg.screenshot(path=str(raw / f"tab-{t.lower().replace(' ', '-')}.png"))
        await pg.goto(f"{APP}/jobs/{job}/report.html"); await pg.wait_for_timeout(2500)
        await pg.screenshot(path=str(raw / "report.png"))
        await b.close()


async def render(pages: dict[str, str], work: Path) -> None:
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome")
        pg = await b.new_page(viewport={"width": 1700, "height": 1000}, device_scale_factor=1)
        for name, html in pages.items():
            f = work / f"{name}.html"
            f.write_text(html)
            await pg.goto(f.as_uri()); await pg.wait_for_timeout(1500)
            await pg.evaluate("document.fonts.ready")
            await pg.locator("#c").screenshot(path=str(OUT / f"{name}.png"), omit_background=True)
        await b.close()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("job", help="a finished Marigold Lane job")
    ap.add_argument("--picker", required=True, help="a job waiting at the sketch picker")
    args = ap.parse_args()
    job = ROOT / "out" / "jobs" / args.job
    work = ROOT / "out" / "readme-art"
    raw = work / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    asyncio.run(capture(args.job, args.picker, raw))
    for f in ("before_desktop.png", "after/before_desktop.png", "after/before_phone.png"):
        shutil.copy(job / f, work / f.replace("/", "_"))
    d = json.loads((job / "job.json").read_text())["data"]
    pages = {
        "banner": banner({"before": "before_desktop.png", "after": "after_before_desktop.png",
                          "phone": "after_before_phone.png",
                          "from": d["audit_before"]["score"]["overall"], "to": d["audit_after"]["score"]["overall"]}),
        "models": models(),
    }
    for name, n, kicker, title, italic, line, img, top in SHOTS:
        pages[name] = shot(n, kicker, title, italic, line, f"raw/{img}", top)
    asyncio.run(render(pages, work))
    for f in sorted(OUT.glob("*.png")):
        print(f.relative_to(ROOT), f"{f.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
