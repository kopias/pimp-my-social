---
name: template-cos
description: COS-style build spec for a makeover - modern minimalism, a white page, one neutral grotesk, uppercase micro-navigation and a strict product grid. Use when the style inputs map to minimal, calm or bright and the business sells considered everyday pieces.
---

# COS: modern minimalism, nothing extra

Source https://www.cos.com/en-us · captured 2026-10-29 (desktop blocks automated browsers;
mobile captured and measured) · shots: `mobile_1.jpg`

**Feeling:** a well-run gallery shop. Calm, neutral, precise; the clothes are the colour.

```json
{
  "id": "cos", "name": "COS", "style": "Gallery White", "tags": ["minimal", "calm", "bright"],
  "pitch": "Modern minimalism: a white page, one grotesk, the product as the only colour.",
  "palette": {"bg": "#FFFFFF", "surface": "#F4F4F2", "ink": "#080808", "muted": "#6F6F6F",
              "accent": "#080808", "accent2": "#E6E6E6"},
  "fonts": {"display": "Inter Tight", "body": "Inter",
            "axes": {"Inter Tight": "wght@400;500;600;700", "Inter": "wght@400;500;600"}},
  "measured": {"family": "SuisseIntl (Inter Tight is the stand-in)", "hero_label": "35px / 700 / uppercase / +1%",
               "nav": "13px / 600 / uppercase / +3%", "body": "13px / 18px", "buttons": "black fill, square, 16px label"},
  "layout": "tiny left wordmark in plain caps; full-bleed hero photograph with one bold uppercase label (SHOP WOMEN style) set over it, bottom-left; then a strict 4-column product grid with name and price under each image in 13px; square black buttons; generous white between rows; footer in four plain uppercase link columns",
  "photo": "clean modern studio, seamless light grey or white wall, soft even daylight, model or product centred with lots of space, neutral tones, crisp fabric detail, minimal styling",
  "signature": ["white page with no decorative colour", "single grotesk family for everything",
                "uppercase micro-labels for nav and section titles", "bold uppercase label over a full-bleed hero photo",
                "4-up product grid with name + price in small type, no cards or shadows", "square black buttons"]
}
```

## Anatomy, top to bottom

1. **Header, 48-56px, white.** Wordmark at left in uppercase grotesk, ~18px, no symbol. Nav
   items inline after it in 13px uppercase semibold. Search, account, bag on the right as
   words or hairline icons.
2. **Hero, 100vw x 85-100vh.** One photograph edge to edge. A single label set over it in
   35-48px bold uppercase, white, bottom-left with 32px inset, plus a small underlined
   link. No subhead paragraph.
3. **Category pair.** Two half-width images side by side, each with an uppercase label.
4. **Product grid.** 4 columns desktop / 2 mobile, 2px gutters or none, images 3:4 on
   `surface`. Name (13px) and price (13px, muted) under each, left aligned.
5. **Story strip.** Text left (one short paragraph, 15px), image right. Plain.
6. **Footer.** Four columns of uppercase 12px links on white, newsletter field with a
   square black button, hairline above.

## Never

Rounded corners, shadows, gradients, coloured sections, serif type, centred hero copy,
more than one label on the hero.
