---
name: template-tiffany
description: Tiffany & Co.-style build spec - heritage jewellery house with an enormous serif wordmark centred over the hero, small uppercase nav under it, a full-bleed portrait hero with a serif title and a white rectangular EXPLORE NOW button, a 'Shop by Category' row of small square tiles with underlined labels, and gift sections in the signature colour. Use for luxury, heritage, calm, bright brands, especially gifts and jewellery.
---

# Tiffany & Co.: the enormous serif wordmark

Source https://www.tiffany.com/ · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** the blue box. Heritage, celebration, gifting.

```json
{
  "id": "tiffany", "name": "Tiffany & Co.", "style": "Grand Wordmark", "tags": ["luxury", "heritage", "calm", "bright"],
  "pitch": "An enormous serif wordmark on a portrait, and one signature colour for gifting.",
  "palette": {"bg": "#FFFFFF", "surface": "#F7F6F2", "ink": "#121212", "muted": "#6C6C6C",
              "accent": "#0F4C5C", "accent2": "#DCEBEA"},
  "fonts": {"display": "Cormorant Garamond", "body": "Inter",
            "axes": {"Cormorant Garamond": "ital,wght@0,400;0,500;0,600;1,400", "Inter": "wght@400;500;600"}},
  "measured": {"family": "Sterling (Cormorant Garamond stand-in) + Santral (Inter)", "wordmark": "~70px tall serif caps, centred, white over the hero",
               "hero_title": "52px / 325 / -4% tracking", "section_title": "32px / -4%", "nav": "11px uppercase", "button": "white fill, black 11px uppercase label, square"},
  "layout": "a transparent header over the hero: store and search at left, contact and icons right, an enormous serif wordmark centred, a row of tiny uppercase nav under it; a full-bleed warm portrait hero with a 52px serif title centred low and a white rectangular EXPLORE NOW button; a 'Gifts' pair of images with serif titles and underlined SHOP NOW; a 'Shop by Category' row of six small square image tiles with tiny uppercase underlined labels; a split with a serif title and paragraph at left and a large image in the signature colour at right",
  "photo": "warm luxurious portrait photography, the piece worn close to skin, soft golden light, gift wrapping and ribbon, the business's signature colour as packaging or background",
  "signature": ["enormous serif wordmark centred over the hero", "tiny uppercase nav row under the wordmark",
                "serif title with tight negative tracking", "white rectangular EXPLORE NOW button",
                "Shop by Category row of six small square tiles with underlined labels", "one signature colour used for gifting panels"]
}
```

## Anatomy, top to bottom

1. **Header, transparent, ~160px.** Left: pin + `SEARCH` 11px; right: `CONTACT US` + icons.
   Wordmark centred: serif caps, 60-70px tall, white, tracking -2%. Under it a row of 10px
   uppercase nav, white.
2. **Hero, 100vw x 90vh.** Portrait. Title 48-52px serif, weight 400, tracking -4%, white,
   centred at 75%; a white button 11px uppercase black label, 44px tall.
3. **Gift pair.** Two images (16:11) in a 1100px container, serif 18px titles centred under,
   `SHOP NOW` 9px underlined in the accent.
4. **Shop by Category.** Serif 32px centred title, six 120px square tiles on the accent2 ground,
   9px uppercase labels underlined in the accent.
5. **Split.** Serif 26px title + 13px paragraph left; large image right on the accent.
6. **Footer** white, small serif.

## Never

Grotesk headlines, dark full sections, dense grids, rounded buttons. Use the business's own
signature colour in the accent slot when it has one; never imitate Tiffany Blue for a
business whose colour it isn't.
