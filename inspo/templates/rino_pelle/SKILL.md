---
name: template-rino-pelle
description: Rino & Pelle-style build spec - Dutch outerwear with a tan rewards strip, a spaced serif-caps wordmark left, centred sentence-case nav, a full-bleed hero on a bold saturated backdrop with a huge light high-contrast serif headline left and two black buttons, then a centred 'Mix & Match' serif title over a 4-up product row with name left and price right. Use for bold, warm, luxury, editorial brands.
---

# Rino & Pelle: a light serif on a bold red backdrop

Source https://rino-pelle.com/ · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** a winter campaign that's warm. Polished, bold colour, approachable luxury.

```json
{
  "id": "rino_pelle", "name": "Rino & Pelle", "style": "Colour Backdrop", "tags": ["bold", "warm", "luxury", "editorial"],
  "pitch": "A huge light serif headline on a saturated backdrop, black buttons, tidy product rows.",
  "palette": {"bg": "#FFFFFF", "surface": "#F3F2F4", "ink": "#111111", "muted": "#78433D",
              "accent": "#E52B1E", "accent2": "#BE8B70"},
  "fonts": {"display": "Cormorant Garamond", "body": "Inter",
            "axes": {"Cormorant Garamond": "ital,wght@0,300;0,400;1,300", "Inter": "wght@400;500"}},
  "measured": {"family": "Saol Display light (Cormorant Garamond 300) + Akzidenz Grotesk (Inter)", "headline": "90px / 300",
               "section": "32px / 300 serif", "nav": "14px / 400", "kicker": "9px uppercase tracked", "buttons": "black fill, white 13px label, square, side by side"},
  "layout": "a tan strip with a centred line; a header with a spaced serif-caps wordmark at left, centred sentence-case nav, search/locale/sign in/cart words at right; a thin row with a sign-in prompt; a full-bleed hero photograph on a bold saturated colour backdrop (red satin, a colour wall), the model right of centre, at the left a tiny uppercase kicker, a 90px light serif headline in two lines and two black square buttons side by side; a centred tiny kicker, a 32px light serif title and an underlined link; a 4-up edge-to-edge product row on pale grey with small 'New' tags, name left and price right",
  "photo": "fashion campaign on a bold saturated backdrop (red satin, painted colour wall), model confident and warm, soft key light, textured outerwear in focus; products full length on pale grey",
  "signature": ["huge light serif headline (90px, 300) at the hero's left", "bold saturated colour backdrop in the hero",
                "two black square buttons side by side", "tan strip at the very top", "spaced serif-caps wordmark at left",
                "centred kicker + light serif title + underlined link above product rows"]
}
```

## Anatomy, top to bottom

1. **Strip, 20px, #BE8B70,** white 10px centred.
2. **Header, 50px.** Wordmark left: serif caps tracked 0.3em, 14px bold. Nav centred 14px
   sentence case. Right: `Search  EN  Sign in  Cart` 13px.
3. **Hero, 100vw x 85vh.** Saturated backdrop photo. At left 7%: kicker 9px uppercase tracked white,
   headline 84-90px serif 300 white two lines, buttons 120x34 black, 12px gap.
4. **Section intro.** Kicker 9px, title 32px serif 300 centred, underlined 13px link.
5. **Product row.** 4-up, 2px gaps, 3:4 on #F3F2F4, 'New' tag 9px in a grey box top-left,
   name 13px left / price 13px right.
6. **Second campaign** split, then footer.

## Never

Bold weights in headlines, muted colourless heroes, rounded buttons, centred hero copy.
