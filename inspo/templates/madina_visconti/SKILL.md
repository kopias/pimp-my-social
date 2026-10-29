---
name: template-madina-visconti
description: Madina Visconti-style build spec - nature-inspired Milanese jewellery on a sage-green ground with a coral shipping strip, a small lowercase wordmark left, a full-bleed portrait hero with a big serif collection title, Garamond section headings over light grotesk paragraphs, and a mosaic of portrait photos. Use for natural, romantic, warm, dark brands, especially handmade and craft.
---

# Madina Visconti: sage green and a Garamond story

Source https://madinavisconti.com/ · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** a goldsmith's garden in Milan. Botanical, crafted, romantic.

```json
{
  "id": "madina_visconti", "name": "Madina Visconti", "style": "Sage Garden", "tags": ["natural", "romantic", "warm", "dark"],
  "pitch": "A sage-green world: Garamond stories, botanical portraits, handmade warmth.",
  "palette": {"bg": "#6A8A83", "surface": "#5C7A73", "ink": "#FFFFFF", "muted": "#DDE6E2",
              "accent": "#E8857A", "accent2": "#2D3A37"},
  "fonts": {"display": "EB Garamond", "body": "Inter", "label": "Playfair Display",
            "axes": {"EB Garamond": "ital,wght@0,400;0,500;1,400", "Inter": "wght@300;400;500", "Playfair Display": "wght@500;600"}},
  "measured": {"family": "Adobe Garamond (EB Garamond) + Aktiv Grotesk (Inter) + Acta Display (Playfair)", "section_title": "33.6px / 400 Garamond",
               "hero_title": "~56px Acta Display, white", "nav": "14px / 400", "body": "12.6px / 15px", "ground": "#6A8A83 sage"},
  "layout": "a coral shipping strip; a header on sage with a small lowercase wordmark and tiny subline at left, sentence-case nav centred (current page in coral), language toggle and icons right; a full-bleed soft portrait hero with a large display serif collection title and an underlined 'Shop Now' at the right; two columns on sage, each with a Garamond heading and a light grotesk paragraph in white; a mosaic row of five portrait photos with Garamond captions and tiny 'View more' links; a story section with a dark close-up photo at left and white paragraphs at right",
  "photo": "soft romantic portraits with florals and printed silk headscarves, pastel and coral tones, botanical details, natural light; dark close-ups of hands working metal",
  "signature": ["sage-green page ground with white type", "coral shipping strip and coral current-nav item",
                "Garamond section headings over light grotesk paragraphs", "large display serif title on the hero",
                "mosaic row of portrait photos with Garamond captions", "small lowercase wordmark with a subline"]
}
```

## Anatomy, top to bottom

1. **Strip, 16px, #E8857A,** white 10px centred.
2. **Header, ~70px, sage.** Wordmark left: lowercase serif mark 28px with a 9px subline; nav
   centred 14px sentence case white, current in coral; `Eng / Ita` style toggle and icons right.
3. **Hero, 100vw x 75vh.** Soft portrait. Title 52-60px display serif white at right third,
   underlined 18px `Shop Now` below.
4. **Twin columns** on sage: Garamond 32px headings, 13px light white paragraphs, max 520px each.
5. **Mosaic.** 5 portraits, 2px gaps, Garamond 16px captions + 10px `View more`.
6. **Story.** Dark close-up left 50%, white text right with a Garamond heading.
7. **Footer** on #2D3A37.

## Never

White pages, black type, bold grotesk headlines, hard corporate photography.
