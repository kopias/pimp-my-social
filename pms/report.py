"""The makeover report: what was missing, what we added, what it could be worth.

Every score is measured (the same 17 checks before and after, in pms.audit).
The value section is a calculator, not a promise: the owner's own traffic
numbers times published effects we can cite, with every input editable and
every assumption written next to it. Things nobody can measure yet (being
recommended by an AI assistant) are listed as capabilities, without numbers.
"""

from __future__ import annotations

import html
import json
import re
import statistics
from datetime import date
from pathlib import Path

from . import audit

SOURCES = {
    "rich_results": {
        "url": "https://developers.google.com/search/docs/appearance/structured-data/intro-structured-data",
        "text": "Google Search Central: Rotten Tomatoes measured a 25% higher click-through rate on "
                "pages with structured data; Food Network saw 35% more visits; Nestlé measured 82% "
                "higher click-through on rich results.",
    },
}


def typical_price(profile: dict) -> float:
    """Median of the first price on each product, as a default order value."""
    prices = []
    for p in profile["products"]:
        mt = re.search(r"\$\s?(\d+(?:\.\d{1,2})?)", p.get("price") or "")
        if mt:
            prices.append(float(mt.group(1)))
    return round(statistics.median(prices), 2) if prices else 25.0


def build(site_before, checks_before, checks_after, profile: dict, direction: dict,
          shots: list[dict], social: dict, remixes: list | None, files: dict,
          logo: dict | None = None, camp: dict | None = None) -> dict:
    sb, sa = audit.score(checks_before), audit.score(checks_after)
    after = {c.id: c for c in checks_after}
    fixed = [{"label": c.label, "category": audit.CATEGORIES[c.category], "found": c.found,
              "why": c.why, "added": c.fix, "now": after[c.id].found if c.id in after else "",
              "passes_now": bool(after.get(c.id) and after[c.id].passed)}
             for c in checks_before if not c.passed]
    kept = [c.label for c in checks_before if c.passed]
    still = [{"label": c.label, "found": c.found} for c in checks_after if not c.passed]
    posts = {ch["channel"]: len(ch["posts"]) for ch in social.get("channels", [])}
    agent = [
        "AI crawlers (GPTBot, ClaudeBot, PerplexityBot, Google-Extended, Meta's crawler and more) "
        "are welcomed by name in robots.txt",
        "llms.txt gives AI models a plain-language summary of the business, products, hours and FAQs",
        "WebMCP tools let a browser agent list products, look up prices and hours, answer questions "
        "and find how to order without scraping the page",
        f"{len(profile['faqs'])} questions customers ask, answered in your words and marked up as FAQPage",
    ]
    return {
        "business": profile["name"], "date": date.today().isoformat(),
        "url": site_before.final_url, "direction": direction["name"],
        "score_before": sb, "score_after": sa,
        "fixed": fixed, "kept": kept, "still_missing": still,
        "made": {
            "photos": [{"product": s["product"], "fidelity": s["fidelity"], "note": s["note"]}
                       for s in shots],
            "posts": posts,
            "remixes": [{"title": r["best"]["grounded"]["title"], "format": r["format"]["name"],
                         "essence": r["format"]["essence"],
                         "duration_s": r["best"]["render"]["duration_s"],
                         "review": r["best"]["review"], "cuts": len(r["cuts"])}
                        for r in remixes or []],
            "logo": logo,
            "campaign": ({"question": camp["question"], "thesis": camp["thesis"],
                          "pieces": [{"kind": p["kind"], "persona": p["persona"], "headline": p["headline"],
                                      "takes": p["takes"], "hands_checked": p["check"]["hands_checked"]}
                                     for p in camp["pieces"]],
                          "film": {"title": camp["film"]["title"], "duration_s": camp["film"]["duration_s"],
                                   "review": camp["film"]["review"]}} if camp else None),
            "files": files,
        },
        "agent_ready": agent,
        "speed": {"before": site_before.perf, "after": files.get("perf_after", {})},
        "gaps": profile.get("gaps", []),
        "value": {
            "monthly_visitors": 500, "search_share": 0.6, "conversion": 0.03,
            "order_value": typical_price(profile), "ctr_lift": 0.25,
            "source": SOURCES["rich_results"],
        },
    }


# --- the page ---------------------------------------------------------------------

CSS = """
:root { --paper:#f7f5f0; --paper2:#eeebe4; --ink:#121212; --muted:#7a766e; --line:rgba(18,18,18,.12);
        --hot:#c8361b; --good:#2f5d43; --card:rgba(255,255,255,.5); --edge:rgba(255,255,255,.78);
        --shadow:rgba(70,35,10,.38);
        --serif:"Cormorant Garamond","Times New Roman",serif; --sans:"Hanken Grotesk",system-ui,sans-serif;
        --mono:"JetBrains Mono",ui-monospace,monospace; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --paper:#13110f; --paper2:#1c1916; --ink:#f3ede4; --muted:#a39a8d; --line:rgba(243,237,228,.13);
  --hot:#e8613f; --good:#7cc196; --card:rgba(255,255,255,.04); --edge:rgba(255,255,255,.09); --shadow:rgba(0,0,0,.6); } }
* { box-sizing:border-box }
html { background:var(--paper); }
body { margin:0; color:var(--ink); font:400 16px/1.6 var(--sans); font-variant-numeric:lining-nums; -webkit-font-smoothing:antialiased; background:transparent; }
a { color:inherit; text-underline-offset:.22em; text-decoration-thickness:1px; }
a:hover { color:var(--hot); }
/* the landing page's atmosphere: column grid, a turning colour halo, halftone, grain */
.backdrop { position:fixed; inset:0; z-index:0; pointer-events:none; overflow:hidden; }
.backdrop .grid { position:absolute; inset:0;
  background-image:linear-gradient(to right, var(--line) 1px, transparent 1px);
  background-size:calc(100% / 12) 100%; opacity:.45;
  -webkit-mask-image:radial-gradient(ellipse 70% 60% at 50% 20%, #000 20%, transparent 80%);
  mask-image:radial-gradient(ellipse 70% 60% at 50% 20%, #000 20%, transparent 80%); }
.backdrop .halo { position:absolute; right:-14vw; top:-18vh; width:min(70vw,820px); aspect-ratio:1; border-radius:50%;
  background:conic-gradient(from 0deg, #c8361b, #e7a541, #f2dcc6 30%, #8ea38c, #2b3a55 70%, #b2675a, #c8361b);
  filter:blur(80px) saturate(1.1); opacity:.32; animation:turn 60s linear infinite; }
.backdrop .halo::after { content:""; position:absolute; inset:30%; border-radius:50%; background:var(--paper); filter:blur(40px); }
.backdrop .dots { position:absolute; left:-4vw; bottom:-6vh; width:40vw; height:46vh;
  background-image:radial-gradient(rgba(200,54,27,.28) 1.1px, transparent 1.6px); background-size:13px 13px;
  -webkit-mask-image:radial-gradient(circle at 0% 100%, #000 0%, transparent 70%);
  mask-image:radial-gradient(circle at 0% 100%, #000 0%, transparent 70%); }
@keyframes turn { to { transform:rotate(360deg); } }
.grain { position:fixed; inset:0; z-index:60; pointer-events:none; opacity:.06; mix-blend-mode:multiply;
  background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='180' height='180'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='3' stitchTiles='stitch'/%3E%3CfeColorMatrix values='0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 0'/%3E%3C/filter%3E%3Crect width='180' height='180' filter='url(%23n)'/%3E%3C/svg%3E"); }
main { position:relative; z-index:1; max-width:1040px; margin:0 auto; padding:0 32px 96px; }
.label { font:500 11px/1.4 var(--sans); letter-spacing:.16em; text-transform:uppercase; color:var(--muted); }
.num { font-family:var(--mono); font-variant-numeric:tabular-nums; }
h1,h2,h3 { text-wrap:balance; } p { text-wrap:pretty; }
header.top { display:flex; justify-content:space-between; align-items:center; gap:16px; padding:22px 0; border-bottom:1px solid var(--line); }
header.top .brand { font:500 13px var(--sans); letter-spacing:.34em; text-transform:uppercase; text-decoration:none; white-space:nowrap; }
header.top .brand i { font-style:normal; color:var(--hot); }
.hero { padding:clamp(48px,9vh,96px) 0 40px; }
.hero .label b { color:var(--hot); font-weight:500; }
h1 { font:300 clamp(54px,9vw,120px)/.9 var(--serif); letter-spacing:-.035em; margin:20px 0 28px; }
h1 i { color:var(--hot); }
.lede { font-size:18px; max-width:36em; color:var(--muted); margin:0; }
.lede b { color:var(--ink); font-weight:500; }
/* glass, as on the landing page's form and model tiles */
.glass { background:var(--card); border:1px solid var(--edge); border-radius:20px;
  backdrop-filter:blur(14px) saturate(1.2); -webkit-backdrop-filter:blur(14px) saturate(1.2);
  box-shadow:0 40px 70px -48px var(--shadow), 0 1px 0 var(--edge) inset; }
.board { display:grid; grid-template-columns:minmax(260px,1.1fr) 2fr; gap:14px; margin-top:44px; }
.overall { padding:28px 30px 30px; display:flex; flex-direction:column; justify-content:space-between; gap:24px; }
.overall .big { display:flex; align-items:baseline; gap:8px; font:200 clamp(88px,11vw,148px)/.85 var(--sans); letter-spacing:-.06em; }
.overall .big sup { font:400 14px var(--sans); letter-spacing:.1em; color:var(--muted); }
.overall .from { font:italic 300 26px/1.2 var(--serif); color:var(--muted); }
.overall .from b { color:var(--good); font-style:normal; font-weight:500; font-family:var(--sans); font-size:13px; letter-spacing:.08em;
  border:1px solid currentColor; padding:3px 8px; border-radius:999px; vertical-align:4px; margin-left:8px; }
.cats { display:grid; grid-template-columns:repeat(auto-fit,minmax(180px,1fr)); gap:14px; }
.cat { padding:18px 20px 20px; display:flex; flex-direction:column; transition:transform .3s cubic-bezier(.3,1.4,.5,1); }
.cat:hover { transform:translateY(-4px); }
.cat .row { display:flex; align-items:baseline; justify-content:space-between; gap:10px; margin-top:auto; padding-top:14px; }
.cat .after { font:200 48px/.9 var(--sans); letter-spacing:-.05em; }
.cat .delta { font:500 12px var(--sans); color:var(--muted); white-space:nowrap; }
.cat .delta.up { color:var(--good); }
.meter { position:relative; height:3px; background:var(--line); margin-top:14px; border-radius:2px; overflow:hidden; }
.meter i { position:absolute; top:0; bottom:0; left:0; background:var(--ink); }
.meter i.gain { background:var(--hot); }
section { margin-top:96px; }
.sechead { display:grid; grid-template-columns:72px 1fr; gap:8px 20px; align-items:baseline; border-top:1px solid var(--ink); padding-top:22px; margin-bottom:28px; }
.sechead .num { color:var(--hot); font-size:12px; }
h2 { font:300 clamp(36px,5vw,56px)/1 var(--serif); letter-spacing:-.025em; margin:0; }
.sechead p { grid-column:2; margin:6px 0 0; color:var(--muted); max-width:42em; }
.fix { display:grid; grid-template-columns:1.1fr 1fr 1.2fr; gap:28px; padding:22px 0; border-bottom:1px solid var(--line); }
.fix h3 { font:400 26px/1.1 var(--serif); margin:6px 0 0; letter-spacing:-.01em; }
.fix .was { color:var(--muted); font-size:14px; }
.fix .was s { text-decoration-color:var(--hot); }
.fix .why { font:italic 300 19px/1.4 var(--serif); color:var(--ink); }
.fix .now { font-size:14px; }
.pill { display:inline-block; margin-top:10px; font:500 10px var(--sans); letter-spacing:.14em; text-transform:uppercase;
  padding:5px 10px; border-radius:999px; border:1px solid currentColor; }
.pill.ok { color:var(--good); } .pill.no { color:var(--hot); }
.kept { margin-top:18px; color:var(--muted); font-size:14px; }
.kept span { display:inline-block; margin:4px 6px 0 0; padding:4px 10px; border:1px solid var(--line); border-radius:999px; font-size:12px; color:var(--ink); }
.list { list-style:none; padding:0; margin:0; counter-reset:n; }
.list > li { counter-increment:n; display:grid; grid-template-columns:72px 1fr; gap:20px; padding:18px 0; border-bottom:1px solid var(--line); }
.list > li::before { content:counter(n, decimal-leading-zero); font:400 12px var(--mono); color:var(--muted); padding-top:4px; }
.list ul { padding-left:18px; margin:10px 0 0; color:var(--muted); font-size:14px; }
.list q { font-family:var(--serif); font-style:italic; font-size:1.15em; }
.note { color:var(--muted); font-size:13px; margin-top:18px; }
.calc { padding:30px; display:grid; grid-template-columns:1fr 1fr; gap:36px; }
.calc .ins label { display:flex; justify-content:space-between; align-items:flex-end; gap:16px; padding:12px 0 8px; border-bottom:1px solid var(--line); font-size:14px; }
.calc input { width:110px; border:0; border-bottom:1px solid var(--ink); background:transparent; color:var(--ink);
  font:300 22px/1 var(--sans); text-align:right; padding:2px 0; outline:none; }
.calc input:focus { border-color:var(--hot); }
.out { display:grid; gap:14px; align-content:start; }
.out div { border-top:1px solid var(--ink); padding-top:10px; }
.out b { font:200 56px/1 var(--sans); letter-spacing:-.05em; display:block; margin-top:4px; }
.out div:last-child b { color:var(--hot); }
footer { margin-top:96px; border-top:1px solid var(--line); padding-top:22px; color:var(--muted); font-size:12px; display:flex; justify-content:space-between; gap:20px; flex-wrap:wrap; }
@media (max-width:820px) {
  main { padding:0 16px 72px; }
  header.top .label { display:none; }
  .board, .calc { grid-template-columns:1fr; }
  .cats { grid-template-columns:1fr 1fr; gap:10px; } .cat .after { font-size:40px; }
  .fix { grid-template-columns:1fr; gap:10px; }
  .sechead, .list > li { grid-template-columns:40px 1fr; gap:6px 12px; }
  .calc { padding:22px 18px; } .out b { font-size:48px; }
}
@media (prefers-reduced-motion: reduce) { .backdrop .halo { animation:none; } .cat { transition:none; } }
"""


def page(r: dict) -> str:
    e = html.escape
    sb, sa = r["score_before"], r["score_after"]

    def cat(k: str, label: str) -> str:
        b, a = sb[k], sa[k]
        d = a - b
        delta = f'<span class="delta up">+{d}</span>' if d > 0 else (
            f'<span class="delta">{d}</span>' if d < 0 else '<span class="delta">held</span>')
        return (f'<div class="cat glass"><div class="label">{e(label)}</div>'
                f'<div class="row"><span class="after">{a}</span>{delta}</div>'
                f'<div class="meter" title="{b} before, {a} after"><i style="width:{min(a, b)}%"></i>'
                f'<i class="gain" style="left:{b}%;width:{max(d, 0)}%"></i></div></div>')
    cats = "".join(cat(k, v) for k, v in audit.CATEGORIES.items())
    gain = sa["overall"] - sb["overall"]
    fixes = "".join(
        f'<div class="fix"><div><div class="label">{e(f["category"])}</div><h3>{e(f["label"])}</h3>'
        f'<div class="was">Before: <s>{e(f["found"])}</s></div></div>'
        f'<div class="why">{e(f["why"])}</div>'
        f'<div class="now">{e(f["added"])}<br><span class="pill {"ok" if f["passes_now"] else "no"}">'
        f'{"✓ passes now" if f["passes_now"] else "✗ still failing"}</span></div></div>'
        for f in r["fixed"]) or '<p class="note">Nothing failed: every check passed before the makeover too.</p>'
    kept = "".join(f"<span>{e(k)}</span>" for k in r["kept"])
    m = r["made"]
    photos = "".join(f"<li>{e(p['product'])}: fidelity {p['fidelity'] if p['fidelity'] is not None else 'n/a'}"
                     f"{' (' + e(p['note']) + ')' if p['note'] else ''}</li>" for p in m["photos"])
    posts = ", ".join(f"{n} for {e(ch.title() if ch != 'x' else 'X')}" for ch, n in m["posts"].items())
    vid_line = "".join(
        f"<li><div>“{e(x['title'])}”: a {x['duration_s']}s vertical video remixing the {e(x['format'])} format "
        f"({e(x['essence'])}) with your own products. Muse Spark's editor review: essence "
        f"{x['review']['essence']}/10, grounded {x['review']['grounded']}/10, overall {x['review']['overall']}/10. "
        f"<q>{e(x['review']['verdict'])}</q></div></li>" for x in m.get("remixes", []))
    cp = m.get("campaign")
    if cp:
        fr = cp["film"]["review"]
        vid_line = (f"<li><div>A campaign, <q>{e(cp['question'])}</q>, built on one idea: “{e(cp['thesis']['not_x'])} "
                    f"{e(cp['thesis']['is_y'])}” Three posters ("
                    + ", ".join(e(p["persona"]) for p in cp["pieces"] if p["kind"] == "poster")
                    + f"), a still, and “{e(cp['film']['title'])}”, a {cp['film']['duration_s']}s film. Every hand "
                    f"was found by SAM 3.1 and checked by Muse Spark. Spark's review of the film: thesis "
                    f"{fr['thesis']}/10, hook {fr['hook']}/10, overall {fr['overall']}/10. <q>{e(fr['verdict'])}</q></div></li>") + vid_line
    lg = m.get("logo") or {}
    if lg.get("mark"):
        vid_line += (f"<li><div>Your logo, remade from the original ({e(lg.get('motif') or '')}): "
                     f"{e(lg['note'])}</div></li>")
    agent = "".join(f"<li><div>{e(a)}</div></li>" for a in r["agent_ready"])
    gaps = "".join(f"<li><div>{e(g)}</div></li>" for g in r["gaps"])
    fixes_next = "".join(f"<li>{e(f)}</li>" for f in (cp["film"]["review"]["fixes"] if cp else
                         [f for x in m.get("remixes", [])[:1] for f in x["review"]["fixes"]]))
    v = r["value"]
    sp_b, sp_a = r["speed"]["before"], r["speed"]["after"]

    def mb(x: dict) -> str:
        return f"{x.get('bytes', 0) / 1e6:.1f} MB, {x.get('requests', 0)} requests, main content at {x.get('lcp_ms', 0) / 1000:.1f}s" if x else "n/a"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Makeover Report</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300;1,400&family=Hanken+Grotesk:wght@200;300;400;500;600&family=JetBrains+Mono:wght@400&display=swap">
<style>{CSS}</style></head><body>
<div class="backdrop" aria-hidden="true"><div class="halo"></div><div class="grid"></div><div class="dots"></div></div>
<div class="grain" aria-hidden="true"></div>
<main>
<header class="top"><span class="brand">Pimp My <i>Social</i></span><span class="label">Makeover report · <span class="num">{e(r['date'])}</span></span></header>

<div class="hero">
<div class="label">The makeover of <b>{e(r['business'])}</b> · in the “{e(r['direction'])}” direction</div>
<h1>{e(r['business'])}, <i>before</i> and after</h1>
<p class="lede">We inspected <b>{e(r['url'])}</b> the way a search engine, an AI assistant and a
customer would, then rebuilt it. Every score is measured by the same 17 checks, on the old site and the new one.</p>
<div class="board">
  <div class="overall glass"><div class="label">Overall</div>
    <div><div class="big">{sa['overall']}<sup>/ 100</sup></div>
    <div class="from">from {sb['overall']}{f'<b>+{gain}</b>' if gain > 0 else ''}</div></div>
    <div class="meter"><i style="width:{min(sa['overall'], sb['overall'])}%"></i><i class="gain" style="left:{sb['overall']}%;width:{max(gain, 0)}%"></i></div>
  </div>
  <div class="cats">{cats}</div>
</div>
</div>

<section><div class="sechead"><span class="num">01</span><h2>What was missing, and what we added</h2>
<p>Each check that failed on the old site, why it matters, and what the new one does instead.</p></div>
{fixes}
{f'<div class="kept">Already in good shape before: {kept}</div>' if kept else ''}
</section>

<section><div class="sechead"><span class="num">02</span><h2>Ready for AI assistants and agents</h2>
<p>Being recommended by an AI assistant can't be measured from outside yet, so we don't put a number on it. These are the things those systems read.</p></div>
<ol class="list">{agent}</ol>
</section>

<section><div class="sechead"><span class="num">03</span><h2>What we made</h2></div>
<ol class="list">
<li><div>A new homepage designed and coded by Muse Wonder, with search, share and agent files.</div></li>
<li><div>{len(m['photos'])} professional product photos, reshot by Muse Image from your own. SAM 3.1 isolated each product and checked the reshoot still shows the same thing.<ul>{photos}</ul></div></li>
<li><div>Social posts: {posts or 'none'}.</div></li>
{vid_line}
<li><div>A brand skill file, so any AI tool you use next writes and designs in your voice.</div></li>
</ol>
<p class="note">Speed, same machine and network: before {e(mb(sp_b))}; after {e(mb(sp_a))}.</p>
</section>

<section><div class="sechead"><span class="num">04</span><h2>What it could be worth</h2>
<p>An estimate you control: put in your own numbers. The click-through lift defaults to the most conservative
published figure we could find. It applies to visits from search.</p></div>
<div class="calc glass" id="calc">
<div class="ins">
<label>Website visitors per month <input type="number" id="v" value="{v['monthly_visitors']}" min="0"></label>
<label>Share of visitors from search (%) <input type="number" id="s" value="{round(v['search_share'] * 100)}" min="0" max="100"></label>
<label>Visitors who buy or book (%) <input type="number" id="c" value="{v['conversion'] * 100:g}" min="0" max="100" step="0.5"></label>
<label>Typical order ($) <input type="number" id="o" value="{v['order_value']:g}" min="0"></label>
<label>Click-through lift from rich results (%) <input type="number" id="l" value="{round(v['ctr_lift'] * 100)}" min="0" max="100"></label>
</div>
<div class="out"><div><span class="label">Extra visits / month</span><b id="ov">–</b></div>
<div><span class="label">Extra orders / month</span><b id="oo">–</b></div>
<div><span class="label">Extra revenue / year</span><b id="or">–</b></div></div>
</div>
<p class="note">{e(v['source']['text'])} <a href="{e(v['source']['url'])}">Source</a></p>
<script>
const $ = (i) => Number(document.getElementById(i).value) || 0;
function calc() {{
  const visits = $('v') * $('s') / 100 * $('l') / 100, orders = visits * $('c') / 100;
  document.getElementById('ov').textContent = Math.round(visits).toLocaleString();
  document.getElementById('oo').textContent = orders.toFixed(1);
  document.getElementById('or').textContent = '$' + Math.round(orders * $('o') * 12).toLocaleString();
}}
document.querySelectorAll('#calc input').forEach((i) => i.addEventListener('input', calc)); calc();
</script>
</section>

<section><div class="sechead"><span class="num">05</span><h2>What to do next</h2></div>
<ol class="list">{gaps}</ol>
{'<p class="note"><b>For the next video</b>, from the editor review:</p><ul class="note">' + fixes_next + '</ul>' if fixes_next else ''}
</section>

<footer><span>Made by Pimp My Social with Meta Muse Spark, Muse Wonder, Muse Image, SAM 3.1 and Muse Voice Transcribe.</span>
<span>Every fact in the new copy comes from your current site; check prices and hours before you publish.</span></footer>
</main></body></html>"""


def write(r: dict, out: Path) -> Path:
    (out / "report.json").write_text(json.dumps(r, indent=1))
    path = out / "report.html"
    path.write_text(page(r))
    return path
