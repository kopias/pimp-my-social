---
name: template-bouguessa
description: Bouguessa-style build spec - modest-luxury maison with a compact white header (geometric wordmark left, tiny uppercase nav), a full-bleed calm studio portrait, a centred collection statement, a 4-up full-length product row on pale grey with uppercase names, three category tiles with labels centred, and a deep burgundy atelier band. Use for minimal, luxury, calm, dark brands.
---

# Bouguessa: calm tailoring and a burgundy atelier

Source https://bouguessa.com/ · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** a quiet atelier in Dubai. Serene, sculptural, expensive without noise.

```json
{
  "id": "bouguessa", "name": "Bouguessa", "style": "Burgundy Atelier", "tags": ["minimal", "luxury", "calm", "dark"],
  "pitch": "Serene tailoring: one calm portrait, long silhouettes on grey, a burgundy atelier band.",
  "palette": {"bg": "#FFFFFF", "surface": "#E8E8E8", "ink": "#1C1C1C", "muted": "#7C706F",
              "accent": "#3B0A10", "accent2": "#DCDCDC"},
  "fonts": {"display": "Outfit", "body": "Outfit", "label": "Cormorant Garamond",
            "axes": {"Outfit": "wght@300;400;500", "Cormorant Garamond": "wght@400;500"}},
  "measured": {"family": "Galano Grotesque (Outfit) + Moulin", "nav": "10px / 400 / uppercase / 1.4px", "product": "12px / 400 / uppercase / 0.48px",
               "statement": "13px centred", "header": "64px, white, sticky, soft shadow", "atelier_title": "serif caps 26px on burgundy"},
  "layout": "a compact white sticky header with a geometric uppercase wordmark at left, six tiny uppercase nav links next to it, hairline icons right; a full-bleed studio portrait on a pale grey wall, no text; a centred underlined uppercase collection link on the photo bottom; a two-line centred statement paragraph; 4 full-length product photos on pale grey in a row with uppercase name and price under each and an underlined DISCOVER THE COLLECTION; three category tiles (garment flats) with white uppercase labels centred; a deep burgundy textured band with a serif caps title centred and a tiny line under it",
  "photo": "serene studio portraits on a pale grey wall, sculptural poses, rich plum, burgundy and camel fabrics, soft diffuse light; full-length product on light grey seamless; garment flats",
  "signature": ["compact white header with the wordmark left and tiny tracked nav beside it", "full-bleed calm studio portrait with no headline",
                "centred two-line statement paragraph", "4-up full-length products on pale grey with uppercase names",
                "category tiles with centred white uppercase labels", "deep burgundy band with a serif caps title"]
}
```

## Anatomy, top to bottom

1. **Header, 64px, white, sticky, 0 2px 8px rgba(0,0,0,.06).** Wordmark 18px uppercase geometric
   at left; nav 10px tracked 1.4px; icons right.
2. **Hero, 100vw x 90vh.** Portrait, no text but an underlined 11px uppercase link at the bottom
   centre in white.
3. **Statement.** 13px, centred, max 760px, 48px padding.
4. **Product row.** 4-up, 6px gutters, 3:4 on #E8E8E8, uppercase 11px name + 10px price.
   Underlined uppercase link under the row at left.
5. **Category tiles.** 3-up, garment flats on #E8E8E8 (or dark), white 12px uppercase label
   centred.
6. **Atelier band.** #3B0A10 with subtle texture (CSS noise via gradient), serif caps 26px
   centred, 9px tracked line under.
7. **Footer** white.

## Never

Headlines on the hero, bright colour, playful type, rounded buttons.
