---
name: template-sleeper
description: Sleeper-style build spec - festive feminine brand on cream with tan studio backdrops, full-bleed photo pairs, big uppercase condensed serif titles centred over the photos, tiny uppercase nav and a centred small wordmark. Use for warm, romantic, retro, playful brands with an occasion feel.
---

# Sleeper: the party on a tan backdrop

Source https://the-sleeper.com/ · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** getting dressed for a party. Joyful, glamorous, cosy.

```json
{
  "id": "sleeper", "name": "Sleeper", "style": "Tan Backdrop", "tags": ["warm", "romantic", "retro", "playful"],
  "pitch": "Big serif titles over photo pairs on a warm tan backdrop. Feels like a party.",
  "palette": {"bg": "#FDF9F0", "surface": "#E5CCB0", "ink": "#4E2E32", "muted": "#8B6E62",
              "accent": "#4E2E32", "accent2": "#D5B99D"},
  "fonts": {"display": "Instrument Serif", "body": "DM Sans",
            "axes": {"Instrument Serif": "", "DM Sans": "wght@400;500"}},
  "measured": {"family": "Mabry (DM Sans stand-in) for UI; a condensed serif for titles", "nav": "12px / 400 / uppercase / +3%",
               "titles": "~64px uppercase condensed serif, white, centred over photos", "header": "50px, cream", "ink": "#4E2E32 (warm brown)"},
  "layout": "a cream header with four tiny uppercase links left, a small serif wordmark centred, locale, log in and bag right; the hero is two full-height photos side by side on a tan studio backdrop with one huge uppercase condensed serif title centred across both; then a product grid (4-up, no gutters, the tan backdrop continuous) with tiny swatch dots and names over the image bottoms; then two more half-width photo tiles each with a big uppercase serif category title at the bottom",
  "photo": "warm studio photography on a seamless tan or caramel backdrop, soft frontal light, joyful model, feathers and texture, full-length and seated poses, product in true colour",
  "signature": ["continuous tan studio backdrop across photo pairs", "huge uppercase condensed serif titles centred over photos",
                "cream page and warm brown ink, never black", "tiny uppercase nav and a small centred wordmark",
                "product grid with no gutters and info over the image bottom", "swatch dots on product tiles"]
}
```

## Anatomy, top to bottom

1. **Header, 50px, #FDF9F0.** 12px uppercase links left, wordmark centre (serif caps, 18px),
   `US/USD  LOG IN  (0)` right, all #4E2E32.
2. **Hero, 100vw x 100vh.** Two half-width photos, no gutter, same tan backdrop so they read
   as one. Title 64-80px uppercase condensed serif, white, two lines, centred over the seam.
3. **Grid.** 4-up, no gutters, 4:5, swatch dots top-right, name and price 11px over the image
   bottom-left in the warm ink.
4. **Category pair.** Two half-width tiles with a 64px uppercase serif label at the bottom
   centre of each.
5. **Footer** cream, small uppercase.

## Never

Pure white, pure black text, grey studio backdrops, sans headlines.
