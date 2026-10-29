---
name: template-sandy-liang
description: Sandy Liang-style build spec - a downtown-girl boutique site with a spaced uppercase wordmark centred between tiny uppercase nav, two large photographs side by side in white, and a pastel ticker line. Use for playful, romantic, minimal brands with a personality.
---

# Sandy Liang: two photographs and a whisper

Source https://www.sandyliang.info/ · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** a friend's flash photos pinned on a white wall. Feminine, nostalgic, a little
off-hand; the whole home page is two pictures.

```json
{
  "id": "sandy_liang", "name": "Sandy Liang", "style": "Flash Diptych", "tags": ["minimal", "playful", "romantic", "editorial"],
  "pitch": "Two big flash photographs in white space, a tiny pink ticker, nothing else.",
  "palette": {"bg": "#FFFFFF", "surface": "#F6F6F4", "ink": "#111111", "muted": "#8A8A86",
              "accent": "#F28DB0", "accent2": "#CFE6EC"},
  "fonts": {"display": "Hanken Grotesk", "body": "Hanken Grotesk",
            "axes": {"Hanken Grotesk": "wght@400;500;600;700"}},
  "measured": {"family": "Calibre (Hanken Grotesk stand-in)", "wordmark": "~22px / 600 / uppercase / +12% tracking, centred",
               "nav": "12px / 400 / uppercase / +4%", "header": "41px, sticky, white, under a 34px ticker",
               "body": "12px uppercase link lists"},
  "layout": "a one-line pink ticker centred at the very top with tiny decorative symbols; header row with three uppercase nav words left, a widely letter-spaced wordmark dead centre, three uppercase words right; two equal portrait photographs side by side filling the first screen with 16-20px white margins; under them a footer of four columns of tiny uppercase links and the street address",
  "photo": "direct on-camera flash, candid and slightly awkward, real interiors with plants and windows, true colour, product fills the frame, shot like a friend's snapshot, no studio polish",
  "signature": ["pastel pink one-line ticker at the top", "letter-spaced uppercase wordmark centred in the header",
                "nav split three words left / three words right, 12px uppercase",
                "two equal portrait photos side by side as the entire hero", "no headline over the photos",
                "tiny uppercase footer link columns"]
}
```

## Anatomy, top to bottom

1. **Ticker, 30-34px.** One centred line in 11-12px pink text with little ornaments either
   side (stars, bows: real characters, not images).
2. **Header, ~41px, white, sticky.** Left: SHOP · SEARCH · COLLECTIONS style words in 12px
   uppercase, 40px apart. Centre: the wordmark in widely tracked caps. Right: INFO · ACCOUNT
   · CART.
3. **Hero: the diptych.** Two portrait images, each ~48% wide, 16px apart, 16px from the page
   edges, tall enough to fill the first screen. One is the product worn, one the product
   alone. No overlay text, no buttons.
4. **Optional second diptych** for another product, same rule.
5. **Footer.** Four columns of 11-12px uppercase links on white; the business address top-left
   in the same type. A newsletter word, not a big form.

On mobile the two photos stack, wordmark centred, MENU left, SEARCH right.

## Never

Headlines over images, rounded cards, buttons in the hero, more than two type sizes above
the fold, any colour except the ticker's pastel.
