"""The landing page's hero: a looping reel of one real makeover, step by step.

    uv run scripts/hero_reel.py <job id> [--name marigold-lane.example]

Every picture in it comes from the job: the before site, the sketches the owner picked
from, a raw photo and its reshoot, the old and new logo, the built site scrolling, the
posts. The type is set by a browser in the landing page's own fonts; each frame is a
screenshot. Writes server/static/hero-reel.mp4 (what the page plays), hero-reel.gif
(the same loop as a GIF, also the fallback) and hero-reel.jpg (the still, for reduced
motion and before the video loads).

Use a business that has agreed to be shown, or the fictional demo bakery.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
STATIC = ROOT / "server" / "static"
W, H, FPS = 1080, 1350, 20

FONTS = ("https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400"
         "&family=Hanken+Grotesk:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap")

# Seconds per scene, in order. A scene the job has nothing for (no logo to redraw, no
# posts) is left out and the rest close up.
SCENE_LEN = {"link": 3.4, "look": 4.0, "photo": 3.4, "logo": 2.6, "site": 4.0, "posts": 3.4, "end": 2.8}

PAGE = r"""<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="__FONTS__">
<style>
:root { --paper:#f7f5f0; --paper2:#eeebe4; --ink:#121212; --muted:#7a766e; --hot:#c8361b; --line:rgba(18,18,18,.12); }
* { box-sizing:border-box; margin:0; }
html, body { background:var(--paper); }
#p { position:relative; width:1080px; height:1350px; overflow:hidden; background:var(--paper); color:var(--ink);
  font:400 26px/1.5 "Hanken Grotesk", sans-serif; -webkit-font-smoothing:antialiased; }
.scene { position:absolute; inset:0; padding:84px 80px; opacity:0; }
.step { font:500 20px/1 "Hanken Grotesk"; letter-spacing:.2em; text-transform:uppercase; color:var(--muted); display:flex; gap:18px; }
.step b { color:var(--hot); font:400 20px "JetBrains Mono"; letter-spacing:0; }
h2 { font:300 108px/.92 "Cormorant Garamond", serif; letter-spacing:-.03em; margin:26px 0 0; }
h2 i { color:var(--hot); font-weight:300; }
.label { font:500 17px/1.3 "Hanken Grotesk"; letter-spacing:.18em; text-transform:uppercase; }
.frame { position:absolute; background:#fff; border:1px solid var(--line); box-shadow:0 30px 60px -30px rgba(0,0,0,.35); overflow:hidden; }
.frame .bar { height:34px; background:var(--paper2); border-bottom:1px solid var(--line); display:flex; align-items:center; gap:8px; padding:0 14px; }
.frame .bar i { width:10px; height:10px; border-radius:50%; background:#d6d2c8; display:block; }
.frame img { display:block; width:100%; }
.url { position:absolute; left:80px; right:80px; top:430px; height:110px; border:1px solid var(--ink); background:#fff;
  display:flex; align-items:center; padding:0 34px; font:400 40px "JetBrains Mono"; }
.url .caret { display:inline-block; width:3px; height:46px; background:var(--hot); margin-left:4px; }
.chips { position:absolute; left:80px; top:580px; display:flex; gap:14px; }
.chip { border:1px solid var(--ink); padding:12px 26px; font:500 20px "Hanken Grotesk"; letter-spacing:.14em; text-transform:uppercase; }
.chip.on { background:var(--ink); color:var(--paper); }
.stamp { position:absolute; background:var(--paper); padding:10px 16px; }
.grid { position:absolute; left:80px; right:80px; top:430px; display:grid; grid-template-columns:1fr 1fr; gap:22px; }
.grid .t { position:relative; aspect-ratio:16/10; overflow:hidden; border:1px solid var(--line); background:#fff; }
.grid .t img { width:100%; height:100%; object-fit:cover; object-position:top; display:block; }
.grid.three { grid-template-columns:1fr 1fr 1fr; gap:18px; top:470px; }
.grid.three .cap { font-size:13px; letter-spacing:.14em; }
.grid .t.pick { outline:5px solid var(--hot); outline-offset:6px; }
.grid .cap { position:absolute; left:10px; bottom:10px; background:rgba(247,245,240,.94); padding:6px 10px; }
.pair { position:absolute; left:80px; right:80px; top:430px; bottom:110px; }
.pair img { position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }
.logos { position:absolute; left:80px; right:80px; top:470px; height:600px; display:grid; grid-template-columns:1fr 80px 1fr; align-items:center; }
.logos .box { height:420px; background:#fff; border:1px solid var(--line); display:flex; align-items:center; justify-content:center; padding:40px; position:relative; }
.logos .box img { max-width:100%; max-height:100%; }
.logos .arrow { text-align:center; font:300 80px "Cormorant Garamond"; color:var(--hot); }
.score { position:absolute; right:80px; top:300px; text-align:right; }
.score .n { font:300 150px/.9 "Cormorant Garamond"; letter-spacing:-.03em; }
.score .n s { color:var(--muted); text-decoration-thickness:3px; }
.fan { position:absolute; left:80px; right:80px; top:440px; height:760px; }
.fan img { position:absolute; width:440px; top:40px; left:50%; box-shadow:0 30px 60px -30px rgba(0,0,0,.45); border:10px solid #fff; }
#s-end { display:flex; flex-direction:column; justify-content:center; text-align:left; }
#s-end .word { font:500 26px "Hanken Grotesk"; letter-spacing:.34em; text-transform:uppercase; }
#s-end .word i { font-style:normal; color:var(--hot); }
#s-end h2 { font-size:150px; margin:40px 0; }
#s-end p { font-size:32px; color:#3a3833; max-width:16em; }
.dots { position:absolute; left:80px; right:80px; bottom:54px; display:flex; gap:10px; }
.dots span { flex:1; height:3px; background:rgba(18,18,18,.12); position:relative; overflow:hidden; }
.dots span b { position:absolute; inset:0; background:var(--hot); transform-origin:left; transform:scaleX(0); }
</style>
<div id="p">
<section class="scene" id="s-link">
  <div class="step"><b>01</b>Paste your link</div>
  <h2>Bring us your<br><i>site.</i></h2>
  <div class="url"><span id="typed"></span><span class="caret" id="caret"></span></div>
  <div class="chips" id="chips">__CHIPS__</div>
  <div class="frame" id="before" style="left:80px;right:80px;top:690px;height:540px">
    <div class="bar"><i></i><i></i><i></i></div><img src="before.jpg" alt=""></div>
  <div class="stamp label" id="before-stamp" style="left:104px;top:1150px">Before · findable __BEFORE__/100</div>
</section>
<section class="scene" id="s-look">
  <div class="step"><b>02</b>Pick a look</div>
  <h2>See your home page<br>in <i>__COUNT__ looks.</i></h2>
  <div class="grid__GRIDCLASS__" id="grid">__SKETCHES__</div>
</section>
<section class="scene" id="s-photo">
  <div class="step"><b>03</b>The photo studio</div>
  <h2>Your products,<br><i>reshot.</i></h2>
  <div class="pair"><img src="raw.jpg" alt=""><img id="shot" src="shot.jpg" alt="">
    <div class="stamp label" id="raw-tag" style="left:22px;bottom:22px">Before · the owner's photo</div>
    <div class="stamp label" id="shot-tag" style="right:22px;bottom:22px">After · Muse Image, checked by SAM 3.1</div></div>
</section>
<section class="scene" id="s-logo">
  <div class="step"><b>04</b>The logo</div>
  <h2>Your mark,<br><i>redrawn.</i></h2>
  <div class="logos"><div class="box" id="old"><img src="old.png" alt=""><span class="stamp label" style="left:16px;top:16px;background:none;padding:0;color:var(--muted)">Before</span></div>
    <div class="arrow" id="arrow">→</div>
    <div class="box" id="new"><img src="new.png" alt=""><span class="stamp label" style="left:16px;top:16px;background:none;padding:0;color:var(--hot)">After</span></div></div>
</section>
<section class="scene" id="s-site">
  <div class="step"><b>05</b>The new site</div>
  <h2>Built, and<br><i>findable.</i></h2>
  <div class="score"><div class="label" style="color:var(--muted)">Findable by search and AI</div>
    <div class="n"><s>__BEFORE__</s> <span id="after-n">__AFTER__</span></div></div>
  <div class="frame" style="left:80px;right:80px;top:470px;height:800px">
    <div class="bar"><i></i><i></i><i></i></div>
    <div style="height:766px;overflow:hidden"><img id="site" src="site.jpg" alt=""></div></div>
</section>
<section class="scene" id="s-posts">
  <div class="step"><b>06</b>The launch</div>
  <h2>And the posts<br>to <i>launch it.</i></h2>
  <div class="fan" id="fan">__POSTS__</div>
</section>
<section class="scene" id="s-end">
  <div class="word">Pimp <i>My</i> Social</div>
  <h2>Paste a link.<br><i>Get the glow-up.</i></h2>
  <p>A new site, studio photos, a redrawn logo and launch posts. Made with Meta's Muse models.</p>
</section>
<div class="dots" id="dots">__DOTS__</div>
</div>
<script>
const SC = __SCENES__, LEN = __LEN__, URL = __URL__;
// number the steps in the order they play
SC.filter(([n]) => n !== 'end').forEach(([n], i) => { const b = document.querySelector('#s-' + n + ' .step b');
  if (b) b.textContent = String(i + 1).padStart(2, '0'); });
const clamp = (x) => Math.max(0, Math.min(1, x));
const ease = (x) => { x = clamp(x); return x < .5 ? 4*x*x*x : 1 - Math.pow(-2*x + 2, 3) / 2; };
const $ = (id) => document.getElementById(id);
function render(t) {
  SC.forEach(([name, start], i) => {
    const end = i + 1 < SC.length ? SC[i + 1][1] : LEN, el = $('s-' + name);
    const fin = ease((t - start) / .45), fout = i + 1 < SC.length ? 1 - ease((t - end + .35) / .35) : 1 - ease((t - LEN + .5) / .5);
    el.style.opacity = t >= start - .01 && t < end + .01 ? Math.min(fin, fout) : 0;
    el.style.transform = `translateY(${(1 - fin) * 24}px)`;
    const k = (t - start) / (end - start);
    const dot = $('dots').children[i]; if (dot) dot.firstChild.style.transform = `scaleX(${clamp(k)})`;
    const local = t - start;
    if (name === 'link') {
      $('typed').textContent = URL.slice(0, Math.round(clamp((local - .5) / 1.1) * URL.length));
      $('caret').style.opacity = Math.floor(t * 2.5) % 2 ? .15 : 1;
      [...$('chips').children].forEach((c, j) => { const on = local > 1.8 + j * .3; c.classList.toggle('on', on);
        c.style.opacity = local > 1.5 + j * .3 ? 1 : 0; });
      const b = ease((local - 2.0) / .6); $('before').style.transform = `translateY(${(1 - b) * 120}px)`; $('before').style.opacity = b;
      $('before-stamp').style.opacity = ease((local - 2.5) / .3);
    }
    if (name === 'look') {
      [...$('grid').children].forEach((c, j) => { const a = ease((local - .5 - j * .14) / .4);
        c.style.opacity = a; c.style.transform = `translateY(${(1 - a) * 30}px)`;
        const picked = c.classList.contains('chosen'), sel = local > 2.5;
        c.classList.toggle('pick', picked && sel);
        if (sel && !picked) c.style.opacity = .35 + .65 * (1 - ease((local - 2.5) / .4));
        if (picked) c.style.transform += ` scale(${1 + .05 * ease((local - 2.5) / .5)})`; });
    }
    if (name === 'photo') {
      const w = ease((local - 1.1) / 1.3); $('shot').style.clipPath = `inset(0 0 0 ${(1 - w) * 100}%)`;
      $('raw-tag').style.opacity = 1 - w; $('shot-tag').style.opacity = w;
    }
    if (name === 'logo') {
      $('old').style.opacity = ease((local - .3) / .4); $('arrow').style.opacity = ease((local - .9) / .3);
      const n = ease((local - 1.2) / .5); $('new').style.opacity = n; $('new').style.transform = `scale(${.94 + .06 * n})`;
    }
    if (name === 'site') {
      const img = $('site'), travel = Math.max(0, img.offsetHeight - 766);
      img.style.transform = `translateY(${-travel * ease((local - .6) / (end - start - 1.2))}px)`;
      $('after-n').style.opacity = ease((local - 1.2) / .5);
    }
    if (name === 'posts') {
      [...$('fan').children].forEach((c, j) => { const a = ease((local - .3 - j * .25) / .55), r = (j - 1) * 7;
        c.style.opacity = a; c.style.transform = `translateX(-50%) translateX(${(j - 1) * 230 * a}px) rotate(${r * a}deg) translateY(${(1 - a) * 80}px)`; });
    }
  });
}
</script>"""


def _jpg(src: Path, dst: Path, width: int) -> None:
    im = Image.open(src).convert("RGB")
    if im.width > width:
        im = im.resize((width, round(im.height * width / im.width)))
    im.save(dst, quality=88)


def assemble(job: Path, name: str, work: Path) -> tuple[str, list, float]:
    state = json.loads((job / "job.json").read_text())
    d = state["data"]
    cards = json.loads((job / "cards.json").read_text())
    chosen = d["direction"]
    _jpg(job / "before_desktop.png", work / "before.jpg", 1000)
    shown = [c for c in cards if c.get("sketch")][:6]
    sketches = []
    for k, c in enumerate(shown):
        _jpg(Path(c["sketch"]["desktop"]), work / f"sk{k}.jpg", 520)
        sketches.append(f'<div class="t{" chosen" if c["id"] == chosen else ""}"><img src="sk{k}.jpg" alt="">'
                        f'<span class="cap label">{c.get("style") or c["name"]}</span></div>')
    shot = d["shots"][0]
    _jpg(Path(shot["source"]), work / "raw.jpg", 1000)
    _jpg(Path(shot["portrait"] or shot["landscape"]), work / "shot.jpg", 1000)
    logo = job / "logo"
    old = logo / "original_on_white.png" if (logo / "original_on_white.png").exists() else logo / "original.png"
    has_logo = old.exists() and (logo / "mark.png").exists()
    if has_logo:
        Image.open(old).save(work / "old.png")
        Image.open(logo / "mark.png").save(work / "new.png")
    full = sorted((job / "site" / "_fidelity").glob("r*_desktop_full.jpg"))
    _jpg(full[-1] if full else Path(d["audit_after"]["desktop"].replace("/jobs/", str(ROOT / "out" / "jobs") + "/")),
         work / "site.jpg", 920)
    posts = []
    for k, p in enumerate([x for x in d.get("campaign", {}).get("pieces", []) if x.get("kind") == "poster"][:3]):
        _jpg(ROOT / "out" / p["image"].lstrip("/"), work / f"post{k}.jpg", 600)
        posts.append(f'<img src="post{k}.jpg" alt="">')
    chips = "".join(f'<span class="chip">{t}</span>' for t in state["tags"][:3])
    names = [n for n in SCENE_LEN if (n != "logo" or has_logo) and (n != "posts" or posts)]
    scenes, t = [], 0.0
    for n in names:
        scenes.append((n, round(t, 2)))
        t += SCENE_LEN[n]
    page = PAGE
    for n in SCENE_LEN:
        if n not in names:  # drop that scene's markup
            a = page.index(f'<section class="scene" id="s-{n}">')
            page = page[:a] + page[page.index("</section>", a) + len("</section>"):]
    page = (page.replace("__FONTS__", FONTS).replace("__CHIPS__", chips).replace("__SKETCHES__", "".join(sketches))
            .replace("__COUNT__", str(len(shown))).replace("__GRIDCLASS__", " three" if len(shown) > 4 else "").replace("__POSTS__", "".join(posts))
            .replace("__BEFORE__", str(d["audit_before"]["score"]["overall"]))
            .replace("__AFTER__", str(d["audit_after"]["score"]["overall"]))
            .replace("__DOTS__", "<span><b></b></span>" * (len(scenes) - 1))
            .replace("__SCENES__", json.dumps(scenes)).replace("__LEN__", str(round(t, 2)))
            .replace("__URL__", json.dumps(name)))
    return page, scenes, t


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("job")
    ap.add_argument("--name", default="marigold-lane.example", help="the address typed in the first scene")
    args = ap.parse_args()
    job = ROOT / "out" / "jobs" / args.job
    work = Path(tempfile.mkdtemp(prefix="reel-"))
    frames = work / "frames"
    frames.mkdir()
    try:
        page, scenes, length = assemble(job, args.name, work)
        (work / "index.html").write_text(page)
        with sync_playwright() as p:
            b = p.chromium.launch(channel="chrome")
            pg = b.new_page(viewport={"width": W, "height": H})
            pg.goto((work / "index.html").as_uri(), wait_until="load")
            pg.evaluate("document.fonts.ready")
            pg.wait_for_timeout(800)
            n = round(length * FPS)
            for i in range(n):
                pg.evaluate(f"render({i / FPS})")
                pg.locator("#p").screenshot(path=frames / f"f{i:04d}.png")
            pg.evaluate(f"render({scenes[-1][1] + 1.2})")  # the still: the end card, settled
            pg.locator("#p").screenshot(path=work / "still.png")
            b.close()
        ff = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(frames / "f%04d.png")]
        subprocess.run(ff + ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "24", "-preset", "slow",
                             "-movflags", "+faststart", str(STATIC / "hero-reel.mp4")], check=True)
        subprocess.run(ff + ["-vf", "fps=12,scale=540:-1:flags=lanczos,split[a][b];[a]palettegen=max_colors=128:"
                             "stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
                             "-loop", "0", str(STATIC / "hero-reel.gif")], check=True)
        Image.open(work / "still.png").convert("RGB").save(STATIC / "hero-reel.jpg", quality=86)
        for f in ("hero-reel.mp4", "hero-reel.gif", "hero-reel.jpg"):
            print(f, round((STATIC / f).stat().st_size / 1e6, 2), "MB")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
