---
name: template-mango
description: Mango-style build spec - big-brand Mediterranean fashion with a white header (uppercase nav split around a small wordmark), a full-bleed close-up portrait hero with a huge two-line serif headline (one word in italic) centred and category words under it, then clean footer columns. Use for bold, editorial, bright, minimal brands that want mass-premium confidence.
---

# Mango: the big serif line with an italic word

Source https://shop.mango.com/us · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** a Barcelona billboard. Polished, confident, sunny, a little sexy.

```json
{
  "id": "mango", "name": "Mango", "style": "Billboard Serif", "tags": ["bold", "editorial", "bright", "minimal"],
  "pitch": "A giant serif headline with one italic word over a close-up portrait.",
  "palette": {"bg": "#FFFFFF", "surface": "#F5F3F2", "ink": "#0E0E0E", "muted": "#6E6E6E",
              "accent": "#C00000", "accent2": "#F2E8E6"},
  "fonts": {"display": "Newsreader", "body": "Inter",
            "axes": {"Newsreader": "ital,opsz,wght@0,6..72,300;0,6..72,400;1,6..72,300;1,6..72,400", "Inter": "wght@400;500;600"}},
  "measured": {"family": "Mango headings sans (Inter) + Inspirational serif (Newsreader)", "headline": "96px / 400 serif, white, one word italic",
               "nav": "13px / 600 / uppercase", "header": "56px, white, sticky", "footer_links": "12px / 600 uppercase"},
  "layout": "a white sticky header with uppercase category words left, a small spaced wordmark centred, SEARCH LOG IN WISHLIST BAG (0) right; an optional slim colour promo strip; a full-bleed close-up portrait hero with a huge two-line serif headline centred in white where one word is italic, and a row of uppercase category links centred under it; a newsletter line with a field and an outlined button; social links in a centred row; four columns of small uppercase footer links",
  "photo": "close-up beauty portrait in daylight, saturated fashion colour (a pink, a red), freckles and real skin, the garment's colour filling the frame, Mediterranean light",
  "signature": ["huge two-line serif headline centred on the hero", "exactly one word of the headline in italic",
                "uppercase category words under the headline", "uppercase nav split around a small centred wordmark",
                "close-up portrait hero", "plain uppercase footer columns"]
}
```

## Anatomy, top to bottom

1. **Header, 56px, white, sticky.** `WOMEN MEN …` 13px semibold uppercase left; wordmark
   centred 18px tracked; utility words right.
2. **Hero, 100vw x 100vh.** Close-up portrait. Headline 84-96px serif 400, white, centred,
   two lines, the place or one key word in italic (e.g. "Made in *their town*"). A founding year only if the copy gives one. Under it 12px
   uppercase links 36px apart.
3. **Second hero** (another product, same rule, optional).
4. **Newsletter.** Centred 13px bold line, 240px field + outlined `SIGN ME UP`.
5. **Social row** of uppercase words centred.
6. **Footer** four columns of 12px uppercase semibold links, legal row under.

## Never

Product grids above the fold, sans headlines, small heroes, rounded buttons.
