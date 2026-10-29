---
name: template-olive
description: Olive-style build spec - calm independent boutique with a dark shipping bar, a tracked spaced-out wordmark centred, a full-bleed crop-detail hero, and a 'closer look' split pairing one product photo with an uppercase futura heading, an italic serif product name and a small dark button. Use for minimal, calm, natural, editorial brands.
---

# Olive: a closer look

Source https://www.oliveclothing.com/ · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** a quiet independent shop on a side street. Thoughtful, unhurried, honest.

```json
{
  "id": "olive", "name": "Olive", "style": "Closer Look", "tags": ["minimal", "calm", "natural", "editorial"],
  "pitch": "Quiet and considered: one product at a time, a tracked wordmark, italic serif names.",
  "palette": {"bg": "#FFFFFF", "surface": "#F6F6F5", "ink": "#292929", "muted": "#9F9D9B",
              "accent": "#292929", "accent2": "#DCD6D0"},
  "fonts": {"display": "Jost", "body": "Gelasio",
            "axes": {"Jost": "wght@300;400;500", "Gelasio": "ital,wght@0,400;1,400"}},
  "measured": {"family": "futura-pt (Jost) + Georgia (Gelasio)", "wordmark": "letter-spaced caps O L I V E, ~14px, centred",
               "nav": "11px / 400 / uppercase / 0.7px", "heading": "26px / 400 / uppercase / 2px tracking",
               "product_name": "26px italic serif", "body": "15px serif", "header": "~50px under a 16px dark bar"},
  "layout": "a dark charcoal shipping bar; a white header with WOMEN/MEN dropdown words left, a widely letter-spaced wordmark centred, SEARCH SIGN IN MY CART right in tiny caps; a full-bleed close crop hero (a shoe stepping, a hem) with no text; a 'closer look' split: a large product photo on white at left, at right a tiny uppercase kicker, a 26px tracked uppercase heading, a tiny category label, a 26px italic serif product name, a 15px serif sentence, the price small, and a small dark rectangular button; a 'more to consider' row with a tiny label at left and three product images on light grey with centred uppercase names and muted prices",
  "photo": "quiet natural daylight, detail crops of garments in motion on pavement or floorboards, muted earth tones; product on a plain white or pale grey studio wall, full length, honest",
  "signature": ["letter-spaced wordmark (O L I V E style) centred", "full-bleed detail-crop hero with no text",
                "closer-look split: tracked uppercase heading + italic serif product name + small dark button",
                "tiny uppercase utility words instead of icons", "centred uppercase product names with muted prices"]
}
```

## Anatomy, top to bottom

1. **Bar, 16px, #292929.** 10px uppercase white at left.
2. **Header, ~50px.** Left: two category words with tiny chevrons; centre: wordmark with
   letter-spacing 0.6em; right: `SEARCH  SIGN IN  MY CART(0)` in 11px caps. Hairline under.
3. **Hero, 100vw x 90vh.** One detail crop. No text, no button.
4. **A closer look.** 64px padding. Product image 45% at left on white. Right column (vertically
   centred, max 340px): kicker 9px caps tracked, heading 26px caps tracked 2px, label 9px caps,
   product name 26px italic serif, a 15px serif sentence, price 11px, button #292929 with 11px
   white label, 2px radius.
5. **More to consider.** Small caps label at left; 3 images on #F6F6F5; centred uppercase 11px
   names, muted prices.
6. **Footer** white.

## Never

Headlines on the hero, colour, bold weights, big buttons, dense grids.
