---
name: template-ganni
description: GANNI-style build spec - Scandinavian playful retail with a full-bleed street-photo hero, the brand name set enormous in white over the photo, a dense product grid on light grey with small black add buttons. Use for bold, playful, bright, street brands.
---

# GANNI: the giant wordmark on a street photo

Source https://www.ganni.com/us/home · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** Copenhagen confidence. Busy, fun, a little loud, but organised like a
department store.

```json
{
  "id": "ganni", "name": "GANNI", "style": "Big Name", "tags": ["bold", "playful", "bright", "street"],
  "pitch": "Your name huge across a street photo, then a tidy, busy shop.",
  "palette": {"bg": "#FFFFFF", "surface": "#EFEFEF", "ink": "#000000", "muted": "#6B6B6B",
              "accent": "#E4002B", "accent2": "#F2F2F2"},
  "fonts": {"display": "Inter Tight", "body": "Inter",
            "axes": {"Inter Tight": "wght@500;600;700;800", "Inter": "wght@400;500;600"}},
  "measured": {"family": "Helvetica Neue for Ganni (Inter stand-in)", "nav": "13-14px / 500 / sentence case",
               "section_title": "18px / 500", "body": "14px", "header": "84px incl. 30px black-on-white promo strip, sticky"},
  "layout": "thin announcement strip; header with a bold wordmark left, a row of sentence-case category links (one in red), a grey search pill and hairline icons right; full-bleed street-photography hero with the business name set enormous (15vw) in white at bottom-left and a small 'Discover ->' link bottom-centre; a 4-column product grid on light grey tiles with a small black square '+' button bottom-right of each image, name and price under; category tiles with bold labels",
  "photo": "candid street fashion photography, city sidewalk, natural daylight, motion, real people energy, saturated true colour, product on a light grey seamless for grid shots",
  "signature": ["business name set huge (about 15vw) in white over the hero photo",
                "sentence-case category nav with one item in red", "grey rounded search field in the header",
                "product tiles on light grey with a small black square plus button",
                "'Discover ->' style links with an arrow", "dense 4-up grid, small sans captions"]
}
```

## Anatomy, top to bottom

1. **Strip, 28px.** Centred 13px bold line, close × at the right.
2. **Header, ~56px, white, sticky.** Wordmark left (bold condensed caps, ~28px). Category links
   in 13-14px sentence case, 20px apart; one link (the offer or the newest thing) in red.
   Right: a grey 200px search field with a magnifier, then hairline icons.
3. **Hero, 100vw x 70vh.** A real street photograph. The business name in white, 700 weight,
   ~15vw, flush bottom-left, cropped by nothing. Collection name and `Discover →` in 15px
   white near the bottom centre.
4. **New in.** 4-column grid, 8px gutters, each image on #EFEFEF, 'New' tag top-left in 12px,
   a 24px black square + bottom-right. Name 14px, price 14px under.
5. **Collection banner** with title and `Discover →`, then category tiles (T-Shirts, Knitwear)
   with bold 18px labels under.
6. **Footer** black text on white, link columns, newsletter.

## Never

Serif type, centred hero headline, soft beige palette, big rounded buttons.
