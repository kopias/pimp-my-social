"""The scorecard: what a site is missing for search engines, answer engines and agents.

Every check is measured from the rendered site by code (pms.crawl), never judged by
a model, and the same checks run on the old site and on the makeover so the
before/after numbers are like for like. Each check carries why it matters and what
the makeover adds, which is what the report shows the owner.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .crawl import Site

# Crawlers that feed AI answers and agents. Being disallowed in robots.txt keeps a
# business out of those answers.
AI_BOTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User",
           "PerplexityBot", "Google-Extended", "meta-externalagent", "Applebot-Extended",
           "CCBot"]

CATEGORIES = {
    "seo": "Search engines",
    "aeo": "Answer engines (AI search)",
    "agents": "AI agents",
    "social": "Social sharing",
    "speed": "Speed",
}


@dataclass
class Check:
    id: str
    category: str
    label: str
    passed: bool
    found: str  # what we saw
    why: str  # why it matters, one sentence, for the owner
    fix: str  # what the makeover adds
    weight: int = 1


def _schema_types(site: Site) -> set[str]:
    types: set[str] = set()

    def walk(x):
        if isinstance(x, dict):
            t = x.get("@type")
            for v in ([t] if isinstance(t, str) else t or []):
                types.add(str(v))
            for v in x.values():
                walk(v)
        elif isinstance(x, list):
            for v in x:
                walk(v)
    walk(site.jsonld)
    return types


def blocked_ai_bots(robots: str | None) -> list[str]:
    """AI crawlers that robots.txt shuts out of the whole site."""
    if not robots:
        return []
    groups: list[tuple[list[str], list[str]]] = []
    agents: list[str] = []
    rules: list[str] = []
    last_was_agent = False
    for line in robots.splitlines():
        line = line.split("#")[0].strip()
        if ":" not in line:
            continue
        k, v = (x.strip() for x in line.split(":", 1))
        k = k.lower()
        if k == "user-agent":
            if not last_was_agent and agents:
                groups.append((agents, rules))
                agents, rules = [], []
            agents.append(v.lower())
            last_was_agent = True
        elif k == "disallow":
            rules.append(v)
            last_was_agent = False
        else:
            last_was_agent = False
    if agents:
        groups.append((agents, rules))

    def rules_for(bot: str) -> list[str]:
        for ags, rs in groups:
            if bot.lower() in ags:
                return rs
        for ags, rs in groups:
            if "*" in ags:
                return rs
        return []
    return [b for b in AI_BOTS if "/" in rules_for(b)]


def run(site: Site) -> list[Check]:
    home = site.pages[0] if site.pages else None
    title = home.title if home else ""
    desc = (home.description if home else "") or site.meta.get("description", "")
    sig = site.signals
    types = _schema_types(site)
    blocked = blocked_ai_bots(site.robots_txt)
    og = [k for k in ("og:title", "og:description", "og:image") if site.meta.get(k)]
    no_alt, imgs = sig.get("images_no_alt", 0), sig.get("images", 0)
    lcp = site.perf.get("lcp_ms") or site.perf.get("load_ms") or 0
    mb = site.perf.get("bytes", 0) / 1e6

    c = [
        Check("title", "seo", "Page title", 20 <= len(title) <= 65,
              f"{len(title)} characters: “{title[:70]}”" if title else "missing",
              "The title is the blue link in search results; too short says nothing, too long gets cut off.",
              "A 40-60 character title that leads with what you sell and where."),
        Check("description", "seo", "Meta description", 70 <= len(desc) <= 170,
              f"{len(desc)} characters" if desc else "missing",
              "It's the two lines under your link in search, and many AI tools quote it as the summary.",
              "A specific description of who you are, what you sell and for whom."),
        Check("h1", "seo", "One clear headline (H1)", sig.get("h1") == 1,
              f"{sig.get('h1', 0)} H1 headings", "Search engines read the H1 as the page's topic.",
              "Exactly one H1 per page, saying what the page is about."),
        Check("alt", "seo", "Image descriptions (alt text)", imgs > 0 and no_alt / imgs <= 0.1,
              f"{no_alt} of {imgs} images have none" if imgs else "no images found",
              "Alt text is how search, screen readers and AI understand your photos.",
              "Descriptive alt text on every product photo."),
        Check("canonical", "seo", "Canonical URL", bool(sig.get("canonical")),
              sig.get("canonical") or "missing",
              "Tells search engines which address is the real page, so ranking isn't split.",
              "A canonical link on every page."),
        Check("lang", "seo", "Language declared", bool(sig.get("lang")), sig.get("lang") or "missing",
              "Helps search engines serve the page to the right audience.", "lang set on every page."),
        Check("sitemap", "seo", "sitemap.xml", site.sitemap, "present" if site.sitemap else "missing",
              "A map of every page so search engines find them all.", "A generated sitemap.xml."),
        Check("org_schema", "seo", "Business details as structured data",
              bool(types & {"Organization", "LocalBusiness", "Store", "Restaurant", "Corporation",
                            "ProfessionalService"} or any(t.endswith("Business") for t in types)),
              ", ".join(sorted(types)) or "none",
              "Structured data is how Google and AI assistants know your name, logo, hours and location for sure.",
              "Organization / LocalBusiness JSON-LD with logo, contact and social profiles.", 2),
        Check("product_schema", "seo", "Products as structured data",
              bool(types & {"Product", "Offer", "Service", "Menu", "Course"}),
              "present" if types & {"Product", "Offer", "Service", "Menu", "Course"} else "none",
              "Eligible for rich results (price, availability) and for shopping answers in AI tools.",
              "Product / Offer JSON-LD for each product.", 2),
        Check("faq", "aeo", "Answers to common questions", bool(sig.get("faq")) or "FAQPage" in types,
              "found" if sig.get("faq") or "FAQPage" in types else "none",
              "AI answer engines quote pages that answer the question asked, in plain words.",
              "An FAQ section written from your real offer, marked up as FAQPage.", 2),
        Check("ai_bots", "aeo", "AI crawlers allowed", not blocked,
              ("blocked: " + ", ".join(blocked)) if blocked else
              ("allowed" if site.robots_txt else "no robots.txt (allowed by default)"),
              "If AI crawlers are shut out, ChatGPT, Claude, Perplexity and Meta AI can't recommend you.",
              "A robots.txt that welcomes search and AI crawlers by name and points to the sitemap.", 2),
        Check("llms_txt", "aeo", "llms.txt", site.llms_txt, "present" if site.llms_txt else "missing",
              "A plain-language guide to your site written for AI models, the robots.txt of the AI era.",
              "An llms.txt summarising the business, offer and key pages."),
        Check("webmcp", "agents", "WebMCP tools for AI agents", bool(sig.get("webmcp")),
              "found" if sig.get("webmcp") else "none",
              "Browser agents can call typed tools (search products, get prices, book) instead of guessing at buttons.",
              "WebMCP tools registered on the page: list products, get details, contact.", 2),
        Check("og", "social", "Share previews (Open Graph)", len(og) == 3,
              f"{len(og)} of 3 tags ({', '.join(og) or 'none'})",
              "Controls the image and text people see when your link is shared in chats and feeds.",
              "Open Graph and Twitter card tags with a designed share image."),
        Check("social_links", "social", "Links to your social profiles", len(site.socials) >= 2,
              ", ".join(site.socials) or "none",
              "Ties your accounts to your site so search and AI treat them as one business.",
              "Profile links in the footer and in structured data (sameAs)."),
        Check("viewport", "speed", "Built for phones", bool(sig.get("viewport")),
              "yes" if sig.get("viewport") else "no viewport tag",
              "Most small-business visits are on a phone; Google ranks the mobile version.",
              "A phone-first layout."),
        Check("speed", "speed", "Main content shows fast", 0 < lcp <= 2500,
              f"largest content at {lcp / 1000:.1f}s, {mb:.1f} MB over {site.perf.get('requests', 0)} requests"
              if lcp else "not measured",
              "Slow pages lose visitors before they see anything, and rank lower.",
              "A light static site with compressed, right-sized images.", 2),
    ]
    return c


def score(checks: list[Check]) -> dict:
    """Overall and per-category scores, 0-100, weighted."""
    def pct(cs: list[Check]) -> int:
        total = sum(x.weight for x in cs)
        return round(100 * sum(x.weight for x in cs if x.passed) / total) if total else 0
    out = {"overall": pct(checks)}
    for cat in CATEGORIES:
        out[cat] = pct([x for x in checks if x.category == cat])
    return out


def as_dicts(checks: list[Check]) -> list[dict]:
    return [asdict(x) for x in checks]


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:40] or "business"
