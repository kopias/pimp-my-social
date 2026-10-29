---
name: template-everlane
description: Everlane-style build spec - honest direct-to-consumer basics with a centred tracked wordmark, two-level uppercase nav, muted colour-block promo bars, a full-bleed product hero with a light thin sans headline centred, half-width category tiles, and a tidy row of cut-out products with uppercase shop labels. Use for minimal, natural, calm, bright brands built on transparency and good basics.
---

# Everlane: light type, colour blocks, honest basics

Source https://www.everlane.com/ · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** a clean, honest store. Calm, practical, a little warm.

```json
{
  "id": "everlane", "name": "Everlane", "style": "Honest Basics", "tags": ["minimal", "natural", "calm", "bright"],
  "pitch": "Honest basics: a thin light headline on a big product photo, muted colour bands.",
  "palette": {"bg": "#FFFFFF", "surface": "#F2F1EF", "ink": "#1C1C1C", "muted": "#6F6A66",
              "accent": "#6F7E8C", "accent2": "#3B1219"},
  "fonts": {"display": "Inter", "body": "Inter",
            "axes": {"Inter": "wght@300;400;500"}},
  "measured": {"family": "Maison Neue (Inter stand-in)", "headline": "60px / 300 / +4% tracking", "tile_title": "23px / 400 / uppercase / +4%",
               "nav": "12px / 400 / uppercase", "wordmark": "~20px / 400 / uppercase / +20% tracking, centred", "body": "16px / 24px"},
  "layout": "a muted taupe shipping bar; header row with WOMEN MEN and two more uppercase words left, a widely tracked wordmark centred, SEARCH ACCOUNT BAG right; a second centred row of small uppercase category links; a muted slate-blue promo band with three uppercase phrases spread across; a full-bleed hero photo of the product with a small kicker, a 60px light thin headline and a one-line subhead centred in white, two tiny uppercase links; a long statement sentence in 16px across the page; two half-width tiles with uppercase titles, a small line and SHOP NOW bottom-left; a deep wine band with an uppercase line and links; a row of six cut-out products on light grey with SHOP <CATEGORY> labels under",
  "photo": "clean soft studio and lifestyle photography, product close-ups of fabric texture, muted earth and wine tones, natural window light, honest unretouched feel; cut-out products on light grey",
  "signature": ["60px light (300) headline centred over the hero", "widely tracked uppercase wordmark centred",
                "two-level uppercase nav", "muted colour-block bands (slate, wine) with uppercase text",
                "row of cut-out products with SHOP <CATEGORY> labels", "half-width tiles with uppercase titles bottom-left"]
}
```

## Anatomy, top to bottom

1. **Bar, 16px, #C8BFB8,** 10px uppercase centred.
2. **Header.** Row 1 (40px): 12px uppercase links left (active underlined), wordmark centred
   tracked 0.2em, utility right. Row 2: centred 10px uppercase categories; one in red if a
   sale exists in the profile, else none.
3. **Promo band, 64px, #6F7E8C.** Three uppercase phrases spaced across (small, big, small)
   in white: use real offers only (shipping, hours), never invented.
4. **Hero, 100vw x 80vh.** Kicker 14px, headline 56-60px weight 300, subhead 15px, two 10px
   uppercase links, all white, centred.
5. **Statement.** One sentence, 16px, left aligned in a 1100px measure.
6. **Tile pair**, 50/50, 23px uppercase titles bottom-left, `SHOP NOW` 10px.
7. **Wine band**, #3B1219, uppercase 18px line + links.
8. **Product row.** 6-up cut-outs on #F2F1EF, `SHOP TEES` labels 10px uppercase under.
9. **Footer.**

## Never

Serif type, heavy weights, decorative ornaments, full-black sections.
