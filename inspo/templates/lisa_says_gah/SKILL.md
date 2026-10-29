---
name: template-lisa-says-gah
description: Lisa Says Gah-style build spec - retro-playful boutique in red ink on white with a butter-yellow top bar, condensed Times type everywhere, a script wordmark, a two-photo hero with a big script headline over it. Use for playful, retro, romantic, warm brands.
---

# Lisa Says Gah: red ink and a script flourish

Source https://lisasaysgah.com/ · captured 2026-10-29 · shots: `desktop_1-3.jpg`, `mobile_1.jpg`

**Feeling:** a vintage shop's hand-lettered sign. Joyful, girly, a bit kitsch on purpose.

```json
{
  "id": "lisa_says_gah", "name": "Lisa Says Gah", "style": "Red Ink", "tags": ["playful", "retro", "romantic", "warm"],
  "pitch": "Red ink on white, condensed serif type and a script headline. Pure charm.",
  "palette": {"bg": "#FFFFFF", "surface": "#F8F6F2", "ink": "#D21008", "muted": "#9C4A44",
              "accent": "#D21008", "accent2": "#FEF7CB"},
  "fonts": {"display": "Pinyon Script", "body": "Instrument Serif", "label": "Instrument Serif",
            "axes": {"Pinyon Script": "", "Instrument Serif": "ital@0;1"}},
  "measured": {"type": "Times NR Condensed (Instrument Serif stand-in) for nav, titles, prices", "nav": "16px / 400 / title case",
               "section_title": "22px", "wordmark": "script, ~47px, centred", "header": "146px: yellow bar + two nav rows", "ink": "#D21008 on white"},
  "layout": "a butter-yellow top bar with currency at left in red; a header with title-case category links left and right of a centred script wordmark, then a second centred row of category links; a hero of two half-width photographs side by side, a large white script headline sweeping across the left one, and white pill buttons with a tiny emoji sitting on the photo bottoms; New Arrivals as a centred red serif title over a 4-up row of cut-out products on pale grey with name left and price right in red",
  "photo": "playful flash lifestyle photography, styled vintage interiors, saturated pinks and reds, props and pets, for product shots cut-out garments on pale grey",
  "signature": ["every word in red ink on white", "butter-yellow top bar", "centred script wordmark",
                "large script headline over the hero photo", "two half-width hero photos side by side",
                "condensed serif nav in title case", "white pill labels with an emoji sitting on photos"]
}
```

## Anatomy, top to bottom

1. **Top bar, 20px, #FEF7CB.** Currency/locale at left, red 12px serif.
2. **Header, white.** Row 1: four title-case links left, script wordmark centre, two links and
   icons right, all red. Row 2: a centred line of 8-10 category links in 15px. Hairline under.
3. **Hero.** Two photos, 50/50, no gap, ~75vh. A white script headline 90-110px across the
   left photo, slight tilt allowed. A white pill (12px radius) with an emoji and a red label
   on each photo's bottom edge.
4. **New arrivals.** Red serif title centred (22px), 4 products on #F8F6F2, red name left /
   red price right on one line, a red outlined `View All` pill.
5. **Second diptych** of lifestyle photos with pills.
6. **Footer** red on white.

## Never

Black text, grotesk type, minimal beige luxury, uppercase tracking.
