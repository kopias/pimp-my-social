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
          logo: dict | None = None) -> dict:
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
:root { --bg:#f6f2ea; --ink:#16130f; --muted:#6d655a; --line:#ddd4c4; --good:#2f7a4a; --bad:#b4442c;
        --accent:#d0512a; --card:#fffdf8; }
@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {
  --bg:#14120f; --ink:#f3ede4; --muted:#a59c8e; --line:#36302a; --card:#1d1a16; --good:#6cc08a; --bad:#e2775f; } }
* { box-sizing:border-box } body { margin:0; background:var(--bg); color:var(--ink);
  font:16px/1.55 "Inter", system-ui, sans-serif; }
main { max-width:920px; margin:0 auto; padding:48px 20px 80px; }
h1,h2 { font-family:"Fraunces", Georgia, serif; font-weight:600; letter-spacing:-.01em; }
h1 { font-size:clamp(34px,6vw,58px); line-height:1.02; margin:6px 0 10px; }
h2 { font-size:28px; margin:56px 0 14px; border-top:1px solid var(--line); padding-top:28px; }
.kicker { text-transform:uppercase; letter-spacing:.14em; font-size:12px; color:var(--accent); font-weight:700; }
.lede { color:var(--muted); font-size:18px; max-width:640px; }
.scores { display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr)); gap:12px; margin-top:24px; }
.score { background:var(--card); border:1px solid var(--line); border-radius:14px; padding:16px; }
.score b { display:block; font-size:30px; font-family:"Fraunces",serif; }
.score small { color:var(--muted); } .arrow { color:var(--muted); font-weight:400; }
.up { color:var(--good); }
table { width:100%; border-collapse:collapse; font-size:15px; }
th,td { text-align:left; vertical-align:top; padding:12px 8px; border-bottom:1px solid var(--line); }
th { font-size:12px; text-transform:uppercase; letter-spacing:.08em; color:var(--muted); }
td.why { color:var(--muted); } .ok { color:var(--good); font-weight:600; } .no { color:var(--bad); font-weight:600; }
ul.clean { padding-left:18px; } .calc { background:var(--card); border:1px solid var(--line); border-radius:16px; padding:20px; }
.calc label { display:flex; justify-content:space-between; gap:12px; margin:10px 0; align-items:center; }
.calc input { width:120px; padding:8px; border-radius:8px; border:1px solid var(--line); background:var(--bg); color:var(--ink); font:inherit; }
.out { display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:12px; margin-top:16px; }
.out div { border-top:3px solid var(--accent); padding-top:8px; } .out b { font-size:26px; font-family:"Fraunces",serif; display:block; }
.note { color:var(--muted); font-size:13px; }
@media (max-width:640px) { th:nth-child(3), td:nth-child(3) { display:none; } }
"""


def page(r: dict) -> str:
    e = html.escape
    sb, sa = r["score_before"], r["score_after"]
    cats = [("overall", "Overall")] + [(k, v) for k, v in audit.CATEGORIES.items()]
    score_cards = "".join(
        f'<div class="score"><small>{e(label)}</small><b>{sb[k]} <span class="arrow">→</span> '
        f'<span class="up">{sa[k]}</span></b></div>' for k, label in cats)
    rows = "".join(
        f"<tr><td><b>{e(f['label'])}</b><br><small>{e(f['category'])}</small></td>"
        f"<td>{e(f['found'])}</td><td class='why'>{e(f['why'])}</td><td>{e(f['added'])}<br>"
        f"<span class='{'ok' if f['passes_now'] else 'no'}'>{'✓ passes now' if f['passes_now'] else '✗ still failing'}</span></td></tr>"
        for f in r["fixed"])
    m = r["made"]
    photos = "".join(f"<li>{e(p['product'])}: fidelity {p['fidelity'] if p['fidelity'] is not None else 'n/a'}"
                     f"{' (' + e(p['note']) + ')' if p['note'] else ''}</li>" for p in m["photos"])
    posts = ", ".join(f"{n} for {e(ch.title() if ch != 'x' else 'X')}" for ch, n in m["posts"].items())
    vid_line = "".join(
        f"<li>“{e(x['title'])}”: a {x['duration_s']}s vertical video remixing the {e(x['format'])} format "
        f"({e(x['essence'])}) with your own products. Muse Spark's editor review: essence "
        f"{x['review']['essence']}/10, grounded {x['review']['grounded']}/10, overall {x['review']['overall']}/10. "
        f"“{e(x['review']['verdict'])}”</li>" for x in m.get("remixes", []))
    lg = m.get("logo") or {}
    if lg.get("mark"):
        vid_line += (f"<li>Your logo, remade from the original ({e(lg.get('motif') or '')}): "
                     f"{e(lg['note'])}</li>")
    agent = "".join(f"<li>{e(a)}</li>" for a in r["agent_ready"])
    gaps = "".join(f"<li>{e(g)}</li>" for g in r["gaps"])
    fixes = "".join(f"<li>{e(f)}</li>" for x in m.get("remixes", [])[:1] for f in x["review"]["fixes"])
    v = r["value"]
    sp_b, sp_a = r["speed"]["before"], r["speed"]["after"]

    def mb(x: dict) -> str:
        return f"{x.get('bytes', 0) / 1e6:.1f} MB, {x.get('requests', 0)} requests, main content at {x.get('lcp_ms', 0) / 1000:.1f}s" if x else "n/a"
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Makeover Report</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:wght@500;600&family=Inter:wght@400;600;700&display=swap">
<style>{CSS}</style></head><body><main>
<div class="kicker">Pimp My Social · makeover report · {e(r['date'])}</div>
<h1>{e(r['business'])}, before and after</h1>
<p class="lede">We inspected <b>{e(r['url'])}</b> the way a search engine, an AI assistant and a
customer would, then rebuilt it in the “{e(r['direction'])}” direction. Every score below is measured
by the same 17 checks on the old site and the new one.</p>
<div class="scores">{score_cards}</div>

<h2>What was missing, and what we added</h2>
<table><thead><tr><th>Check</th><th>Before</th><th>Why it matters</th><th>Now</th></tr></thead>
<tbody>{rows}</tbody></table>
<p class="note">Already in good shape before: {e(', '.join(r['kept'])) or 'nothing'}.</p>

<h2>Ready for AI assistants and agents</h2>
<ul class="clean">{agent}</ul>
<p class="note">Being recommended by an AI assistant can't be measured from outside yet, so we don't put a number on it. These are the things those systems read.</p>

<h2>What we made</h2>
<ul class="clean">
<li>A new homepage designed and coded by Muse Wonder, with search, share and agent files.</li>
<li>{len(m['photos'])} professional product photos, reshot by Muse Image from your own. SAM 3.1 isolated each product and checked the reshoot still shows the same thing:<ul>{photos}</ul></li>
<li>Social posts: {posts or 'none'}.</li>
{vid_line}
<li>A brand skill file, so any AI tool you use next writes and designs in your voice.</li>
</ul>
<p class="note">Speed, same machine and network: before {e(mb(sp_b))}; after {e(mb(sp_a))}.</p>

<h2>What it could be worth</h2>
<div class="calc" id="calc">
<p class="note">An estimate you control: put in your own numbers. The click-through lift defaults to the most
conservative published figure we could find ({e(v['source']['text'])} <a href="{e(v['source']['url'])}">Source</a>).
It applies to visits from search.</p>
<label>Website visitors per month <input type="number" id="v" value="{v['monthly_visitors']}" min="0"></label>
<label>Share of visitors from search (%) <input type="number" id="s" value="{round(v['search_share'] * 100)}" min="0" max="100"></label>
<label>Visitors who buy or book (%) <input type="number" id="c" value="{v['conversion'] * 100:g}" min="0" max="100" step="0.5"></label>
<label>Typical order ($) <input type="number" id="o" value="{v['order_value']:g}" min="0"></label>
<label>Click-through lift from rich results (%) <input type="number" id="l" value="{round(v['ctr_lift'] * 100)}" min="0" max="100"></label>
<div class="out"><div><small>Extra visits / month</small><b id="ov">–</b></div>
<div><small>Extra orders / month</small><b id="oo">–</b></div>
<div><small>Extra revenue / year</small><b id="or">–</b></div></div>
</div>
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

<h2>What to do next</h2>
<ul class="clean">{gaps}</ul>
{'<p><b>For the next video</b>, from the editor review:</p><ul class="clean">' + fixes + '</ul>' if fixes else ''}
<p class="note">Made by Pimp My Social with Meta Muse Spark, Muse Wonder, Muse Image, SAM 3.1 and Muse Voice Transcribe.
Every fact in the new copy comes from your current site; please check prices and hours before you publish.</p>
</main></body></html>"""


def write(r: dict, out: Path) -> Path:
    (out / "report.json").write_text(json.dumps(r, indent=1))
    path = out / "report.html"
    path.write_text(page(r))
    return path
