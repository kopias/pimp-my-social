---
name: template-sezane
description: Sézane-style build spec - Parisian romantic boutique on warm white, a tall condensed serif wordmark, handwritten notes laid over product photos, and soft neutral product stories. Use for romantic, warm, natural brands with a personal, hand-signed feel.
---

# Sézane: the handwritten note on the photo

Source https://www.sezane.com/us-en · 2026-10-29: the site shows a bot check to automated
browsers, so this skill is written from its public design (the check page itself confirms
the wordmark); no shots on file.

**Feeling:** a letter from a Parisian friend. Soft, warm, personal, a little nostalgic.

```json
{
  "id": "sezane", "name": "Sézane", "style": "Handwritten", "tags": ["romantic", "warm", "natural", "editorial"],
  "pitch": "Parisian warmth: soft neutrals, a tall serif wordmark, handwritten notes on the photos.",
  "palette": {"bg": "#FBF8F3", "surface": "#F1EBE1", "ink": "#1E1B18", "muted": "#7D756B",
              "accent": "#1E1B18", "accent2": "#C9B79C"},
  "fonts": {"display": "Gloock", "body": "Jost", "label": "Homemade Apple",
            "axes": {"Gloock": "", "Jost": "wght@300;400;500", "Homemade Apple": ""}},
  "measured": {"wordmark": "tall condensed high-contrast serif caps, centred", "nav": "11-12px / 500 / uppercase / +12%",
               "notes": "handwritten script, 20-28px, white or ink, on photos", "body": "14px / 1.6 sans"},
  "layout": "centred tall serif wordmark over a centred row of tracked uppercase nav links; a full-width hero photograph in soft neutral light with a handwritten line written over it and one small uppercase link; product stories as a large photo with a handwritten caption beside a short sans paragraph; a 3-up row of products on warm off-white with name in small caps and price beneath; a centred letter-like note from the founder in the handwritten face",
  "photo": "soft warm daylight in a Parisian apartment, cream walls, wooden floors, neutral and sand tones, the product on a chair or a table, gentle shadows, natural and lived in",
  "signature": ["handwritten script notes written over photographs", "tall condensed serif wordmark centred",
                "centred row of tracked uppercase nav", "warm off-white page, neutral palette",
                "a founder's note set in the handwritten face", "small-caps product names"]
}
```

## Anatomy, top to bottom

1. **Header, ~110px, warm white.** Wordmark centred in the condensed serif (40-48px, caps).
   Under it a centred row of 6-8 uppercase links, 11-12px, tracked +12%. Locale and bag icons
   right.
2. **Hero, 100vw x 80vh.** One soft photograph. A handwritten line (32-44px) in white across
   its lower third, slightly rotated (-2deg). A small uppercase underlined link under it.
3. **Product story.** Image 60% left; right column with an uppercase kicker, a 28px serif
   heading, 14px sans paragraph, and a handwritten aside.
4. **Products.** 3-up, images 4:5 on #F1EBE1, name in uppercase 12px, price 13px.
5. **The note.** Centred, max 520px, handwritten, signed with the founder's name if given.
6. **Footer** warm white, small uppercase columns.

## Never

Black backgrounds, neon accents, bold grotesk headlines, dense grids.
