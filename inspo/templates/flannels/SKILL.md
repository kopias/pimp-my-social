---
name: template-flannels
description: Flannels-style build spec - luxury multi-brand retailer with a black header and full search bar, a punchy campaign banner with bold sans type and black buttons, outlined designer chips, dense product carousels and image tiles with white buttons. Use for bold, techy, dark, street brands that sell lots of things and want a shop that moves.
---

# Flannels: the luxury department store

Source https://www.flannels.com/ · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** a big flagship store on a Saturday. Energetic, commercial, organised.

```json
{
  "id": "flannels", "name": "Flannels", "style": "Flagship", "tags": ["bold", "techy", "dark", "street"],
  "pitch": "A busy luxury flagship: black header, bold banners, chips and carousels.",
  "palette": {"bg": "#FFFFFF", "surface": "#F3F3F3", "ink": "#000000", "muted": "#5F5F5F",
              "accent": "#000000", "accent2": "#EAFF00"},
  "fonts": {"display": "Montserrat", "body": "Montserrat",
            "axes": {"Montserrat": "ital,wght@0,400;0,500;0,600;0,700;0,800;1,400"}},
  "measured": {"family": "Montserrat everywhere", "section": "18-20px / 500", "nav": "13-16px / 400",
               "header": "152px, black, sticky: logo + search + icons, then a nav row", "buttons": "black fill white label, square"},
  "layout": "a neon accent strip; a black header with a bold white wordmark left, a wide search bar with an icon, white icons right, and a centred row of category links in white; a full-width campaign banner with bold sans type and a row of black square buttons; 'Discover our…' outlined rectangular chips scrolling horizontally; product carousels with small heart icons, brand name in semibold over the product name and price; tiles of three styled still-lifes with a label and white square 'Shop Now' buttons centred near the bottom",
  "photo": "crisp commercial e-commerce photography, products on light grey, styled still-life sets with props on plinths, high-key and sharp, plus cold-weather lifestyle shots",
  "signature": ["black header with a full-width search bar", "neon accent strip at the very top",
                "outlined rectangular chips for categories", "dense product carousels with heart icons",
                "black square buttons in banners, white square buttons on image tiles", "Montserrat everywhere"]
}
```

## Anatomy, top to bottom

1. **Strip, 20px, #EAFF00,** black 11px centred.
2. **Header, black, ~110px.** Wordmark 22px bold white left; search bar (#FFF, 2px radius, 40%
   width) centre; white icons right. Nav row: centred white 13px links.
3. **Campaign banner.** Full width ~45vh on a solid or photo ground, bold sans headline
   (italic accent allowed), a row of 4 black buttons with white 12px labels.
4. **Chips.** Section title 18px medium, a row of outlined 1px chips (32px tall) scrolling.
5. **Carousel.** 6 visible, images on #F3F3F3, heart icon top-right, semibold 13px brand line,
   12px product name, price.
6. **Image tiles** 3-up, label in white 14px, white square `Shop Now` with black label.
7. **Footer** black.

## Never

Huge whitespace, serif type, single-product heroes, muted beige palettes.
