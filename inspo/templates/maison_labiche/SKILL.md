---
name: template-maison-labiche
description: Maison Labiche-style build spec - Parisian embroidered-basics brand with a navy shipping bar, a navy Caslon wordmark centred above a row of tracked uppercase nav, a full-bleed video-still hero with a subtitle-style caption, a product carousel with name/price on one line and italic material, and a split 'made-to-measure' story. Use for heritage, playful, retro, warm brands with charm.
---

# Maison Labiche: the film subtitle

Source https://www.maisonlabiche.com/ · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** a French film about a corner shop. Witty, warm, a little preppy.

```json
{
  "id": "maison_labiche", "name": "Maison Labiche", "style": "Subtitle", "tags": ["heritage", "playful", "retro", "warm"],
  "pitch": "Parisian charm: a navy serif wordmark and a hero captioned like a French film.",
  "palette": {"bg": "#FFFFFF", "surface": "#EAE9E5", "ink": "#2C344B", "muted": "#8A8A8A",
              "accent": "#2C344B", "accent2": "#F5E663"},
  "fonts": {"display": "Libre Caslon Text", "body": "Montserrat",
            "axes": {"Libre Caslon Text": "ital,wght@0,400;0,700;1,400", "Montserrat": "wght@400;500;600"}},
  "measured": {"family": "Adobe Caslon Pro (Libre Caslon Text) + Montserrat", "wordmark": "30px / 700 / uppercase / +2%, centred, navy",
               "nav": "12px / 400 / uppercase / 0.6px", "product": "11px uppercase name + price on one line, italic material under",
               "header": "153px, fixed: navy bar + locale row + wordmark + nav row"},
  "layout": "a slim navy shipping bar; a header row with locale selectors at left, the navy Caslon wordmark centred, small icons right; under it a centred row of uppercase nav; a full-bleed hero still with one yellow subtitle-style caption line in the lower third, like a film subtitle; a product carousel of garments on light grey with uppercase name left and price right on one line and an italic grey material line beneath; two half-width lifestyle photos with tracked uppercase underlined labels at the bottom; a split 'made-to-measure' story with an image left and an italic serif kicker, a caps serif heading, a small paragraph and an underlined DISCOVER right",
  "photo": "Parisian street lifestyle photography, overcast daylight, real streets and red shopfronts, characterful young models, candid moments, product on a plain light grey for carousel",
  "signature": ["navy Caslon wordmark centred", "a film-subtitle caption in yellow on the hero",
                "uppercase product name and price on one line with an italic material under",
                "slim navy top bar", "italic serif kicker over a caps serif heading", "tracked uppercase underlined links"]
}
```

## Anatomy, top to bottom

1. **Bar, 20px, #2C344B,** white 11px centred, close × right.
2. **Header, white.** Row: locale at left in 11px; wordmark centre (Caslon bold caps 28-30px,
   navy); search and bag icons right. Row 2: centred uppercase nav, 12px, 60px apart.
3. **Hero, 100vw x 90vh.** A still. One subtitle line in #F5E663, 22-26px Montserrat medium
   with a soft shadow, centred at 85% height, a quote from the brand.
4. **Carousel.** 5 items, images on #EAE9E5, name + price on one line (11px uppercase
   semibold), italic 10px material under in muted.
5. **Lifestyle pair**, 50/50 no gutter, tracked underlined uppercase labels centred near the
   bottom.
6. **Split story.** Image 55% left on a warm ground; right: italic serif kicker 18px, caps
   serif heading 22px, 12px paragraph, underlined uppercase link.
7. **Footer.**

## Never

Big hero headlines, black backgrounds, rounded cards, bold sans.
