---
name: template-dior
description: Dior-style build spec - haute luxury with a centred serif wordmark, stacked full-bleed campaign tiles each with one centred serif title and a tiny underlined link, and almost no other text. Use for luxury, editorial, calm brands that want to feel like a maison.
---

# Dior: stacked campaign tiles, one serif line each

Source https://www.dior.com/en_us · captured 2026-10-29 (desktop blocks automated browsers;
mobile captured) · shots: `mobile_1.jpg`

**Feeling:** walking past the windows on Avenue Montaigne. Every screen is one campaign image.

```json
{
  "id": "dior", "name": "Dior", "style": "Maison Tiles", "tags": ["luxury", "editorial", "calm", "bold"],
  "pitch": "Maison luxury: one campaign photograph per screen, one serif line, nothing else.",
  "palette": {"bg": "#FFFFFF", "surface": "#F5F3EF", "ink": "#1A1A1A", "muted": "#7B7B7B",
              "accent": "#1A1A1A", "accent2": "#FFFFFF"},
  "fonts": {"display": "Cormorant Garamond", "body": "Jost",
            "axes": {"Cormorant Garamond": "wght@400;500", "Jost": "wght@300;400;500"}},
  "measured": {"wordmark": "serif caps, small, centred, white on the first image", "tile_title": "~28px serif, white, centred",
               "link": "11px underlined sans", "body": "13px Futura-like (Jost)"},
  "layout": "a transparent header with a small serif wordmark centred and hairline icons; the page is a stack of full-bleed campaign photographs, each filling the screen (or half-width pairs on desktop), each with a single centred serif title in white in the lower third and a tiny underlined 'Shop now'; between groups, a white band with a centred serif section title and a row of products small on white with name in 13px sans; footer in light grey small sans",
  "photo": "high-end campaign photography, rich and luminous, warm golden or pastel tones, models with serene expressions, opulent interiors, impeccable retouching, product hero lighting",
  "signature": ["stack of full-bleed campaign tiles, one per screen", "one centred serif title per tile in white",
                "tiny underlined 'Shop now' under each title", "small centred serif wordmark",
                "products shown small on white with lots of space", "almost no body copy above the fold"]
}
```

## Anatomy, top to bottom

1. **Header, ~60px, transparent over the first tile.** Menu and search hairline icons left,
   wordmark centred (serif caps, 20-24px, tracked +8%), bag right.
2. **Tile 1, 100vw x 100vh.** Campaign photo. Title 28-36px serif, centred at 70% height,
   `Shop now` 11px underlined under it.
3. **Tiles 2-3.** On desktop two half-width tiles side by side (each 100vh), same rule.
4. **White band.** Serif title 28px centred, 4 products in a row on #F5F3EF, 13px sans
   name, price muted, 64px padding.
5. **Tile 4** full-bleed, then the footer in small grey sans on white.

## Never

Paragraphs over photos, more than one line per tile, coloured backgrounds, bold sans.
