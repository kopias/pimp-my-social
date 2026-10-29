---
name: template-carolina-herrera
description: Carolina Herrera-style build spec - couture house with a spaced serif-caps wordmark left, small uppercase nav with one highlighted pill, a full-bleed studio portrait hero with a gradient and a medium sans title plus two underlined links bottom-centre with carousel dots, a tabbed product carousel with one featured larger item and a mono SHOP NOW button, and a bold red colour-field section. Use for luxury, bold, editorial, techy brands.
---

# Carolina Herrera: couture with a mono accent

Source https://www.carolinaherrera.com/us/en · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** a couture salon that's also very online. Elegant, bold, graphic.

```json
{
  "id": "carolina_herrera", "name": "Carolina Herrera", "style": "Couture Red", "tags": ["luxury", "bold", "editorial", "techy"],
  "pitch": "Couture and graphic: studio portraits, a featured product carousel, a bold red field.",
  "palette": {"bg": "#FFFFFF", "surface": "#F7F7F8", "ink": "#151515", "muted": "#8B8B8B",
              "accent": "#A51C1F", "accent2": "#151515"},
  "fonts": {"display": "Inter Tight", "body": "Inter Tight", "label": "Space Mono",
            "axes": {"Inter Tight": "wght@400;500;600", "Space Mono": "wght@400;700"}},
  "measured": {"family": "Herrera sans (Inter Tight) + Herrera Sans Mono (Space Mono)", "hero_title": "28px / 500",
               "nav": "11px / 600 / uppercase", "button": "black fill, mono uppercase 11px label, 4px radius", "header": "72px, transparent over hero"},
  "layout": "a transparent header over the hero with the business name in spaced serif caps at left, small uppercase nav centred with one item in a grey pill, icons right; a full-bleed studio portrait with a dark gradient at the bottom, a 28px sans title and two underlined small links centred low, carousel dots under; a tab row of uppercase category names with an underline under the active one; a product carousel where the centre item is larger and gets its name and a black mono SHOP NOW button under it with a small 'view all' link; a full-width deep red section with a portrait-format image left and a centred sans title, a short paragraph and an underlined uppercase link",
  "photo": "high-fashion studio portraits on pale grey, sculptural poses with the product held to the face, crisp light, graphic and bold; product shots on white, full length, small",
  "signature": ["spaced serif-caps wordmark at top-left", "one nav item highlighted in a pill",
                "hero title in medium sans with two underlined links and carousel dots", "tab row with an underlined active category",
                "product carousel with a larger centred featured item and a black mono button", "a full-width deep red colour-field section"]
}
```

## Anatomy, top to bottom

1. **Header, 72px, transparent.** Wordmark left: serif caps 22px tracked +8%, white. Nav centred,
   11px semibold uppercase, the first item in a #6B6B6B pill with white text. Icons right.
2. **Hero, 100vw x 100vh.** Studio portrait, gradient to 45% black at the bottom. Title 28px
   500 white centred at 80%; `Shop` `Discover` 12px underlined; dots 8px under.
3. **Tabs.** Centred uppercase 10px tabs, 1px underline on the active.
4. **Featured carousel.** 5 items; the centre one 1.4x larger. Under it: name 16px medium,
   black button with Space Mono 10px uppercase `SHOP NOW`, 4px radius, then 10px underlined
   `View All`.
5. **Red field.** #A51C1F, image 40% left (bleeds past the top edge), right: 22px white title,
   11px paragraph, 11px underlined uppercase link, all centred.
6. **Footer** white.

## Never

Serif body copy, warm beige, square tiles in a uniform grid, all-caps headlines.
