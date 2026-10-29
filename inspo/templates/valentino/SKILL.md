---
name: template-valentino
description: Valentino-style build spec - maison luxury with a black announcement bar, a two-line serif wordmark top-left, a centred row of condensed DIN-style uppercase nav, a full-bleed cinematic hero with a small serif title and a dark DISCOVER MORE button at the bottom centre, four-up category tiles with serif labels, and products on pale warm grey cards. Use for luxury, dark, minimal, bold brands that want maison gravity.
---

# Valentino: craft close-ups and a serif caption

Source https://www.valentino.com/en-us/ · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** the atelier at night. Serious craft, expensive restraint.

```json
{
  "id": "valentino", "name": "Valentino", "style": "Atelier Night", "tags": ["luxury", "dark", "minimal", "bold"],
  "pitch": "Maison gravity: cinematic craft close-ups, a quiet serif caption, a dark button.",
  "palette": {"bg": "#FFFFFF", "surface": "#F4F2EE", "ink": "#000000", "muted": "#7D7D7D",
              "accent": "#000000", "accent2": "#EFE8DE"},
  "fonts": {"display": "Tinos", "body": "Barlow Semi Condensed",
            "axes": {"Tinos": "ital,wght@0,400;1,400", "Barlow Semi Condensed": "wght@400;500"}},
  "measured": {"family": "DIN Pro (Barlow Semi Condensed) + Times (Tinos)", "titles": "20-24px / 400 serif / -3% tracking",
               "nav": "12px / 400 / uppercase", "body": "12px / 16px", "header": "56px, transparent over hero, under a 45px black bar"},
  "layout": "a black announcement bar with a centred one-line message and arrows; a transparent header with the wordmark set in two lines (name over a small sub-line) at top-left, a centred row of small condensed uppercase nav, hairline icons right; a full-bleed cinematic hero (hands at work, a close craft moment) with a small serif title at the bottom centre and a dark translucent rectangular DISCOVER MORE button under it, a pause control bottom-right; four equal category tiles edge to edge with serif labels at the bottom centre; a centred serif section title; products on pale warm grey cards with a tiny status label top-left and name left / price right in small sans",
  "photo": "cinematic craft and campaign photography, dark moody interiors, hands at work in close-up, deep blacks, controlled single light, rich materials, film still",
  "signature": ["wordmark in two lines at top-left (name over a small sub-line)", "centred condensed uppercase nav in small DIN-like type",
                "full-bleed cinematic hero with a small serif title bottom-centre", "dark translucent rectangular DISCOVER MORE button",
                "four edge-to-edge category tiles with serif labels", "products on pale warm grey cards, name left price right"]
}
```

## Anatomy, top to bottom

1. **Bar, 22px, black.** 11px white centred message, chevrons left, × right.
2. **Header, 56px, transparent.** Wordmark top-left (serif caps 22px over an 8px tracked
   sub-line: the business's tagline or city). Nav centred, 12px uppercase condensed, 22px apart.
   Icons right.
3. **Hero, 100vw x 100vh.** Cinematic still. Title 20px serif white, centred at 88% height;
   button below it: rgba(0,0,0,.55), 11px uppercase white label, 36px tall, 140px wide.
4. **Category tiles.** 4 equal, edge to edge, 3:4, 18px serif labels white bottom-centre.
5. **Section title**, 24px serif centred, 80px padding.
6. **Product cards** 4-up on #F4F2EE, 8px gutters, a 10px muted tag top-left, name 11px left,
   price 11px right.
7. **Footer** white, condensed small caps.

## Never

Bright colour, large headlines, rounded corners, playful type.
