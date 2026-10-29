---
name: template-me-em
description: ME+EM-style build spec - modern British luxury with a dark announcement bar, a crest, a centred wordmark among small sans nav, a moody full-bleed hero with a sans title and light serif subtitle bottom-left, and category tiles with labels inset. Use for luxury, calm, editorial, minimal brands that want to feel established.
---

# ME+EM: a sans title and a serif whisper

Source https://www.meandem.com/us · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** a smart London members' club. Confident, warm, grown-up.

```json
{
  "id": "me_em", "name": "ME+EM", "style": "Members’ Club", "tags": ["luxury", "calm", "editorial", "minimal"],
  "pitch": "Grown-up British luxury: moody photography, a sans title, a light serif line under it.",
  "palette": {"bg": "#F8F7F3", "surface": "#EDEAE4", "ink": "#1A1A1A", "muted": "#746B67",
              "accent": "#2C2C2C", "accent2": "#E1DBDC"},
  "fonts": {"display": "Inter", "body": "Inter", "label": "Newsreader",
            "axes": {"Inter": "wght@400;500;600", "Newsreader": "ital,opsz,wght@0,6..72,200;0,6..72,300;1,6..72,300"}},
  "measured": {"family": "Suisse Intl (Inter) + Times Now light (Newsreader 200)", "hero_title": "30px / 400",
               "hero_sub": "24px / 100 serif", "nav": "10-11px / 400-600", "header": "~70px under a 25px dark bar and a crest row"},
  "layout": "a dark charcoal announcement bar with small uppercase centred text and a phone number right; a slim row with a small crest centred; a header with small sans category links left, a bold sans wordmark centred, hairline icons right; a full-bleed moody photograph (gallery, interior) with a 30px sans title and a 24px light serif line under it at bottom-left, a small underlined link bottom-right; a product carousel row on warm white with tiny sans names, prices and fabric swatches with a material line; a 3-up tile row with labels inset bottom-left; a split section with an image left and a light serif paragraph-headline right with an underlined link",
  "photo": "moody painterly interiors, museum and gallery rooms, deep greens and browns, soft window light, a model in the room, rich texture, cinematic but natural",
  "signature": ["dark announcement bar with tiny uppercase text", "small crest centred above the header",
                "bold sans wordmark centred, small sans nav left", "hero title in sans with a light serif line under it, bottom-left",
                "underlined text links, no filled buttons", "material line under each product price"]
}
```

## Anatomy, top to bottom

1. **Bar, 25px, #2C2C2C.** 10px uppercase white text centred; utility at right.
2. **Crest row, ~28px.** A small mark centred (use the business's mark, 22px).
3. **Header, ~45px.** 11px sans links left, semibold; wordmark centred 22px bold; icons right.
4. **Hero, 100vw x 85vh.** Moody photograph. Bottom-left at 24px: title 30px sans white, then
   a 24px light serif line. Bottom-right: `Shop New In` underlined 13px.
5. **Product row.** 4.5 cards visible (a carousel feel), images on #EDEAE4, name 11px semibold,
   price 11px, a swatch dot + material text, an outlined tag (e.g. 'Made in …') when true.
6. **Tiles.** 3-up, labels 12px white inset bottom-left.
7. **Split story** on #F1ECE9: image left, a 24px serif text-heading right, link underlined.
8. **Footer** warm white.

## Never

Big uppercase headlines, bright colours, card shadows, pill buttons.
