---
name: template-idioma
description: Idioma-style build spec - eco streetwear brand with a full-bleed street portrait hero, uppercase Helvetica headline plus Courier body copy, a highlighter-yellow button, carousels of products on light grey, and a big circular badge logo. Use for street, playful, retro, techy brands with a message.
---

# Idioma: Courier copy and a highlighter button

Source https://idioma.world/ · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** a skate-shop zine with a conscience. Direct, graphic, global.

```json
{
  "id": "idioma", "name": "Idioma", "style": "Highlighter", "tags": ["street", "playful", "retro", "techy"],
  "pitch": "Street portraits, typewriter copy and a highlighter-yellow button.",
  "palette": {"bg": "#FFFFFF", "surface": "#ECEDEC", "ink": "#131313", "muted": "#636661",
              "accent": "#FDFF08", "accent2": "#E8461E"},
  "fonts": {"display": "Archivo", "body": "Courier Prime",
            "axes": {"Archivo": "wght@400;500;600", "Courier Prime": "wght@400;700"}},
  "measured": {"family": "Helvetica (Archivo) for titles, Courier New (Courier Prime) for copy and product text",
               "section_title": "29px / 400 / uppercase", "hero_title": "21px / 400 / uppercase", "body": "14px / 19.6px Courier",
               "button": "#FDFF08 fill, square, 18px Courier label"},
  "layout": "a black ticker bar; header with a menu icon left, a round badge logo centred, icons right; full-bleed street-portrait hero with a white uppercase grotesk headline left, a few lines of Courier text under it and a square highlighter-yellow button; NEW ARRIVALS as a left-aligned uppercase grotesk title over a horizontal product carousel on light grey, Courier names and prices; an about split with the circular badge logo large at left and Courier paragraphs plus a yellow 'Read more' button at right; BEST SELLERS carousel",
  "photo": "documentary street portraits on brick and concrete, overcast London daylight, real young people, honest framing, 35mm film colour; products flat on light grey",
  "signature": ["Courier typewriter body copy and product text", "uppercase grotesk section titles left-aligned",
                "square highlighter-yellow buttons", "round badge logo, large in the about section",
                "street portrait hero with left-aligned text block", "horizontal product carousels on light grey"]
}
```

## Anatomy, top to bottom

1. **Ticker, 22px, black.** White 11px Courier, chevrons.
2. **Header, ~80px, white.** Hamburger left, a round badge logo (64px) centred, search and bag
   right.
3. **Hero, 100vw x 75vh.** Portrait photo. At left 40px: uppercase grotesk headline 21-28px
   white, three lines of 12px Courier white, a #FDFF08 square button with black Courier label.
4. **NEW ARRIVALS.** Grotesk 29px uppercase at left, 5 products on #ECEDEC with Courier 12px
   name and `$xx.00 USD` under, a white circular arrow at the right edge.
5. **About split.** Big circular badge logo left (the business's mark redrawn as a stamp ring
   with text around it), Courier paragraphs right, yellow `Read more`.
6. **BEST SELLERS** carousel, then a footer in Courier.

## Never

Serif headlines, pastel palettes, rounded pill buttons, luxury whitespace.
