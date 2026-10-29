---
name: template-rouvenat
description: Rouvenat-style build spec - Parisian fine-jewellery maison with a centred quirky serif wordmark split between two groups of tiny uppercase nav, inset (not full-bleed) warm cinematic campaign images with a light uppercase title, products on cream cards with prices, and a scrolling motto ticker. Use for luxury, warm, dark, editorial brands, especially jewellery and small precious goods.
---

# Rouvenat: inset campaign frames and a motto ticker

Source https://rouvenat.com/ · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** a jeweller's salon with a film-noir edge. Precious, warm, a touch mysterious.

```json
{
  "id": "rouvenat", "name": "Rouvenat", "style": "Salon Frames", "tags": ["luxury", "warm", "dark", "editorial"],
  "pitch": "Fine-jewellery mood: framed cinematic images, cream product cards, a motto ticker.",
  "palette": {"bg": "#FFFFFF", "surface": "#FDF7ED", "ink": "#2C2C2C", "muted": "#8A8378",
              "accent": "#601402", "accent2": "#C3A56B"},
  "fonts": {"display": "Bodoni Moda", "body": "Manrope",
            "axes": {"Bodoni Moda": "ital,opsz,wght@0,6..96,400;0,6..96,500;1,6..96,400", "Manrope": "wght@400;500;600"}},
  "measured": {"family": "Nuckle (Manrope stand-in) for all UI; an idiosyncratic serif wordmark", "hero_title": "32px / 400 / uppercase / -1%",
               "nav": "10px / 500 / uppercase / 0.5px", "body": "12px / 24px", "header": "80px, white, fixed"},
  "layout": "a white fixed header: CONTACT and a language toggle far left, three uppercase nav words, the serif wordmark centred, three more nav words, then hairline icons; the hero is an inset frame (20px margins) holding a warm cinematic campaign photo with a light uppercase title at the left third and a small underlined uppercase link; a product carousel of items on cream cards with small sentence-case names and prices; a scrolling motto ticker of short uppercase phrases separated by small symbols; a second inset campaign frame, dark, with a tiny kicker, a title and an underlined link centred",
  "photo": "cinematic jewellery campaign photography, warm amber and deep shadow, light through blinds, close crops of skin with the piece in focus; product on a cream seamless for cards",
  "signature": ["hero images inset with white margins, never full-bleed", "serif wordmark centred between two groups of nav",
                "light uppercase hero title with an underlined uppercase link", "products on cream cards",
                "scrolling motto ticker of uppercase phrases", "tiny 10px uppercase nav"]
}
```

## Anatomy, top to bottom

1. **Header, 80px, white, fixed.** `CONTACT  EN` at 20px from the left; three 10px uppercase links;
   wordmark centred (serif, 32px, a little eccentric: use the remade logo); three more links;
   search, wishlist, account, bag icons.
2. **Hero frame.** 20px white margin all round, 85vh. Warm image. Title 32px uppercase 400,
   white, at left 12% / 45% height; `DISCOVER THE COLLECTION` 10px underlined under it.
3. **Carousel.** 3 visible items, cream (#FDF7ED) cards 4:5, name 11px sentence case, price
   11px; arrows in small circles.
4. **Motto ticker.** One line of 11px uppercase phrases with a small symbol between, moving
   (CSS animation, paused under reduced motion).
5. **Second frame,** darker, kicker + title + link centred.
6. **Footer** white, small caps.

## Never

Full-bleed images, bold type, bright colours, dense grids, rounded corners.
