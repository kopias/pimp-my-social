---
name: template-khy
description: KHY-style build spec - after-dark campaign site with a full-bleed black-and-white hero, typewriter monospace for every word, a Times wordmark centred, and a product row on warm off-white. Use for dark, bold, editorial, nightlife or statement brands.
---

# KHY: typewriter type over a black-and-white film still

Source https://www.khy.com/ · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** a campaign zine. Moody, sexy, low-key expensive; every word looks typed.

```json
{
  "id": "khy", "name": "KHY", "style": "After Dark", "tags": ["dark", "bold", "editorial", "street"],
  "pitch": "A black-and-white film still and typewriter type. Feels like a night out.",
  "palette": {"bg": "#FAF9F6", "surface": "#F1EFEA", "ink": "#161316", "muted": "#6E6B70",
              "accent": "#161316", "accent2": "#FAF9F6"},
  "fonts": {"display": "Tinos", "body": "IBM Plex Mono",
            "axes": {"Tinos": "wght@400;700", "IBM Plex Mono": "wght@400;500"}},
  "measured": {"wordmark": "Times, ~40px tall, centred", "everything_else": "Monospace typewriter 13px / 500 / uppercase / +10%",
               "hero_labels": "20px mono uppercase, staggered", "header": "72px, transparent over the hero"},
  "layout": "a tiny uppercase mono link strip at the top; transparent header over the hero with MENU at left, the serif wordmark centred, SEARCH WISHLIST ACCOUNT BAG right in mono; a full-bleed black-and-white hero photo with short mono lines (collection name, season) placed in a staggered, offset scatter rather than one block, and an underlined mono CTA at the right; below, a collage of small photos with an off-centre heading, then a NEW ARRIVALS row of 4 products on off-white with mono uppercase name and price",
  "photo": "grainy black-and-white film photography, night, flash or low light, extreme close crop, cinematic, high contrast, product shots on a plain light grey wall full-length",
  "signature": ["monospace typewriter type for all copy and nav", "serif wordmark centred in a transparent header",
                "full-bleed black-and-white hero", "hero text as short mono lines in a staggered scatter, not a block",
                "underlined uppercase mono links instead of buttons", "warm off-white page under the hero"]
}
```

## Anatomy, top to bottom

1. **Link strip, 18px.** `SHOP X · SHOP Y` in 11px mono uppercase, underlined, centred.
2. **Header, transparent, over the hero.** MENU left; wordmark centre in the serif, white on
   the photo; mono uppercase utility words right, 13px, 30px apart.
3. **Hero, 100vw x 100vh, black and white.** Mono uppercase lines, white, 18-20px: the
   collection name at left-third, the season repeated in a staggered stack mid-page, an
   underlined `SHOP …` at the right. Nothing centred.
4. **Collage.** Three or four photos of different sizes set loosely on off-white, a mono
   heading off to one side with a 12px sentence-case line under it.
5. **New arrivals.** Mono label left-indented, 4 product images on #F1EFEA, name and price in
   11px mono uppercase, a centred underlined `SHOP NEW ARRIVALS`.
6. **Second full-bleed photo** (colour allowed), mono caption.
7. **Footer** in mono, small.

## Never

Sans-serif headlines, centred hero blocks, filled buttons, rounded corners, colour grading in
the hero.
