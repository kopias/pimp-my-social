---
name: template-blandin-delloye
description: Blandin & Delloye-style build spec - Parisian tailoring house with a full-bleed group photo, a huge light uppercase serif headline centred, four dark category bars along the bottom of the hero, and offset photo pairs on cream. Use for luxury, heritage, editorial, warm brands, especially made-to-measure.
---

# Blandin & Delloye: the tailor's headline

Source https://www.blandindelloye.com/ · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** an invitation to a fitting. Warm, sociable, quietly grand.

```json
{
  "id": "blandin_delloye", "name": "Blandin & Delloye", "style": "The Fitting", "tags": ["luxury", "heritage", "editorial", "warm"],
  "pitch": "A grand uppercase serif headline on a warm group photo, then cream and quiet.",
  "palette": {"bg": "#FFFCF6", "surface": "#F4EFE6", "ink": "#141414", "muted": "#6F6B68",
              "accent": "#1E1E1E", "accent2": "#FFFFFF"},
  "fonts": {"display": "Cormorant Garamond", "body": "Inter",
            "axes": {"Cormorant Garamond": "ital,wght@0,300;0,400;0,500;1,300", "Inter": "wght@300;400;500"}},
  "measured": {"family": "Roxborough CF (Cormorant Garamond stand-in) + Graphik (Inter)", "hero_h1": "80px / 300 / uppercase",
               "section_h2": "48px / 300 / uppercase", "label": "12px / 700 / uppercase / 3px tracking", "body": "14px / 25px",
               "header": "102px, fixed, transparent"},
  "layout": "transparent fixed header over the hero: a white square menu button left, the serif name centred, a locale and a white rectangular LET'S MEET button right; full-bleed warm group photograph with a tiny tracked kicker and a huge light uppercase serif headline centred; four equal dark charcoal bars across the bottom of the hero with tracked uppercase labels (the categories); below on cream, a centred uppercase serif section title with a short centred paragraph, then photos in offset pairs (one higher than the other) with category names in serif on the photos",
  "photo": "warm natural-light group and portrait photography of well-dressed people in a city, sociable laughter, film-like warmth, textured fabrics, slightly desaturated",
  "signature": ["huge light uppercase serif headline centred on the hero (80px)", "tiny letter-spaced kicker above it",
                "four dark category bars along the bottom edge of the hero", "white rectangular CTA button in the header",
                "cream page with offset (staggered) photo pairs", "uppercase serif section titles centred"]
}
```

## Anatomy, top to bottom

1. **Header, fixed, transparent, ~100px.** A white 34px square with a hamburger at left; the
   name centred in the serif, 24px, white; a white rectangle button with dark tracked 11px
   uppercase label at right.
2. **Hero, 100vw x 100vh.** Group photo. Kicker in 11px uppercase tracked 3px; headline 72-80px,
   300 weight, uppercase, white, centred, max two lines. At the bottom, 40px from the edges,
   four equal #1E1E1E bars (52px tall) with white tracked uppercase labels.
3. **Section intro on cream.** Centred serif title 44-48px uppercase light, a 14px sans
   paragraph max 420px centred.
4. **Offset pairs.** Two photos per row, the right one starts 90px lower; serif label + 12px
   sub-label centred on each photo's lower third.
5. **Footer** on cream, small serif name, tracked uppercase links.

## Never

Bold sans headlines, bright colours, rounded corners, grids where every photo aligns.
