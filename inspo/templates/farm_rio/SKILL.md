---
name: template-farm-rio
description: FARM Rio-style build spec - joyful Brazilian print brand with a plum announcement bar, a light geometric sans, a full-bleed sunny lifestyle hero with a condensed italic serif headline centred, and a lush lifestyle photo grid. Use for playful, warm, bright, natural brands full of colour and print.
---

# FARM Rio: italic headline in the sunshine

Source https://farmrio.com/ · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** a sunny street in Rio. Warm, colourful, optimistic, feminine.

```json
{
  "id": "farm_rio", "name": "FARM Rio", "style": "Sunshine Italic", "tags": ["playful", "warm", "bright", "natural"],
  "pitch": "Sunshine and print: a big italic headline on a joyful street photo.",
  "palette": {"bg": "#FFFFFF", "surface": "#F6F5F1", "ink": "#1E1B19", "muted": "#7A6452",
              "accent": "#6F3D49", "accent2": "#D3C5B3"},
  "fonts": {"display": "Bodoni Moda", "body": "Montserrat",
            "axes": {"Bodoni Moda": "ital,opsz,wght@1,6..96,400;1,6..96,500;0,6..96,400", "Montserrat": "wght@300;400;500"}},
  "measured": {"family": "Montserrat everywhere + a condensed italic didone for headlines", "nav": "14px / 400 / title case",
               "section": "24px / 500", "headline": "~64px italic serif, white, centred", "header": "49px under a 37px plum bar"},
  "layout": "plum announcement bar with a centred white line and arrows; a white header with the light sans wordmark left, title-case links centred, a search field with placeholder text and small icons right; a full-bleed sunny lifestyle photo with the wordmark small and a large condensed italic serif headline centred in white, an underlined lowercase link under it; a 4-up product row with name and price in light sans; then two half-width lifestyle photos edge to edge; category tiles with uppercase label, sentence description and underlined 'discover' at bottom-left",
  "photo": "sunny lifestyle street photography, warm golden daylight, smiling models walking, bold prints and embroidery in focus, lush plants, saturated warm colour",
  "signature": ["plum announcement bar", "large condensed italic serif headline centred on the hero",
                "underlined lowercase 'meet the collection' style link", "light geometric sans for all UI",
                "edge-to-edge lifestyle photo pairs", "category tiles with label + sentence + underlined discover"]
}
```

## Anatomy, top to bottom

1. **Bar, 37px, #6F3D49.** White 12px centred line, chevrons either side.
2. **Header, 49px.** Wordmark left in light wide caps (two weights). Title-case links, 14px,
   centred. Right: a borderless search with placeholder 'What are you looking for?' and icons.
3. **Hero, 100vw x 75vh.** Sunny street photograph. The wordmark small (24px) above a 56-72px
   italic serif headline, white, centred; an underlined lowercase link 16px under it.
4. **Product row.** 4-up, 8px gutters, images 3:4, name and price 13px light.
5. **Lifestyle pair.** Two half-width photos with no gutter.
6. **Category tiles** 2-up: 13px uppercase label, a 13px sentence, underlined 'discover', inset
   bottom-left in white.
7. **Footer** white, light sans.

## Never

Black or dark sections, bold condensed sans, monochrome photography, square heavy buttons.
