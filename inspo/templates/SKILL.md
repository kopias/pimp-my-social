---
name: fashion-site-templates
description: Library of 25 build-spec skills, one per leading fashion website (COS, GANNI, KHY, Sézane, Dior, Tiffany & Co., Net-a-Porter and more, from Linguise's "Top 25 fashion website design for inspiration"). Use when a makeover's style inputs need to become a concrete website design - map the owner's style tags to a template, then build to that template's SKILL.md and check the result against its screenshots.
---

# Fashion site templates

Each folder is one template: a real fashion site, captured and measured in a browser on
2026-10-29, written up as a spec a builder can follow and a checker can hold it to.

- `SKILL.md`: a JSON token block (palette roles, Google Fonts stand-ins for the site's own
  faces, the measured type, the layout, the photo brief, and the **signature moves** that
  make it recognisable), then the anatomy section by section and what never to do.
- `measured.json`: what the browser computed on the live site: font families, sizes,
  weights, tracking, header height, logo position, nav labels, button styles.
- `desktop_1.jpg`, `desktop_2.jpg`, `mobile_1.jpg`: the site's first screen, one scroll
  down, and the phone (kept out of git: they are the brands' images). Refresh with
  `uv run scripts/capture_templates.py [ids]`. COS and Dior block automated desktop
  browsers (phone only); Sézane and Net-a-Porter block both, so theirs are written from
  the public design with no shots.

## How a makeover uses them

1. **Map.** The owner's style tags (up to three) shortlist every template that carries the
   most of them (`pms/templates.py: rank`), shuffled so no two makeovers meet the same list.
   Spark picks the ones that fit the business best, plus a random wildcard: 3 options when
   one template matches every tag, up to 6 when the ask is broad.
2. **Sketch.** Muse Wonder sketches the business's own homepage (header, hero, first
   section) on each shortlisted template, with its real copy and a product photo reshot to
   that template's photo brief. Each sketch draws a variant: which product leads, which of
   Spark's headlines, wide or tall crop, one small twist. A browser screenshots each on
   desktop and phone; code checks it (borrowed menu words, invented numbers, missing
   images, measured headline contrast) and Wonder fixes it once if needed. The owner picks
   from these thumbnails (`pms/mockups.py`).
3. **Build.** Muse Wonder gets the chosen template's skill, its screenshots and the sketch
   the owner picked (same headline, lead product and twist), and builds the full page: same header, hero composition, type scale,
   section order and product presentation; the business's own name, remade logo, photos
   and words.
4. **Check.** The built page is screenshotted (desktop, scroll, phone) and Muse Spark
   compares it side by side with the template: nine scores, every signature move present
   or not, and a list of concrete fixes. Below 8/10, Wonder revises from the fixes (up to
   twice) and the best round ships. `uv run scripts/template_qa.py <job> <ids|--all>`
   runs the same build and check on a finished job and writes a comparison sheet.

Borrow the design, never the brand: no template's name, logo, photographs or copy ends up
on a client's site.

## The templates

| Folder | Site | Direction | Tags | Pitch |
|---|---|---|---|---|
| `cos/` | COS | Gallery White | minimal, calm, bright | Modern minimalism: a white page, one grotesk, the product as the only colour. |
| `sandy_liang/` | Sandy Liang | Flash Diptych | minimal, playful, romantic, editorial | Two big flash photographs in white space, a tiny pink ticker, nothing else. |
| `ganni/` | GANNI | Big Name | bold, playful, bright, street | Your name huge across a street photo, then a tidy, busy shop. |
| `khy/` | KHY | After Dark | dark, bold, editorial, street | A black-and-white film still and typewriter type. Feels like a night out. |
| `lisa_says_gah/` | Lisa Says Gah | Red Ink | playful, retro, romantic, warm | Red ink on white, condensed serif type and a script headline. Pure charm. |
| `sezane/` | Sézane | Handwritten | romantic, warm, natural, editorial | Parisian warmth: soft neutrals, a tall serif wordmark, handwritten notes on the photos. |
| `blandin_delloye/` | Blandin & Delloye | The Fitting | luxury, heritage, editorial, warm | A grand uppercase serif headline on a warm group photo, then cream and quiet. |
| `me_em/` | ME+EM | Members’ Club | luxury, calm, editorial, minimal | Grown-up British luxury: moody photography, a sans title, a light serif line under it. |
| `farm_rio/` | FARM Rio | Sunshine Italic | playful, warm, bright, natural | Sunshine and print: a big italic headline on a joyful street photo. |
| `dior/` | Dior | Maison Tiles | luxury, editorial, calm, bold | Maison luxury: one campaign photograph per screen, one serif line, nothing else. |
| `maison_labiche/` | Maison Labiche | Subtitle | heritage, playful, retro, warm | Parisian charm: a navy serif wordmark and a hero captioned like a French film. |
| `idioma/` | Idioma | Highlighter | street, playful, retro, techy | Street portraits, typewriter copy and a highlighter-yellow button. |
| `sleeper/` | Sleeper | Tan Backdrop | warm, romantic, retro, playful | Big serif titles over photo pairs on a warm tan backdrop. Feels like a party. |
| `olive/` | Olive | Closer Look | minimal, calm, natural, editorial | Quiet and considered: one product at a time, a tracked wordmark, italic serif names. |
| `rouvenat/` | Rouvenat | Salon Frames | luxury, warm, dark, editorial | Fine-jewellery mood: framed cinematic images, cream product cards, a motto ticker. |
| `mango/` | Mango | Billboard Serif | bold, editorial, bright, minimal | A giant serif headline with one italic word over a close-up portrait. |
| `flannels/` | Flannels | Flagship | bold, techy, dark, street | A busy luxury flagship: black header, bold banners, chips and carousels. |
| `everlane/` | Everlane | Honest Basics | minimal, natural, calm, bright | Honest basics: a thin light headline on a big product photo, muted colour bands. |
| `valentino/` | Valentino | Atelier Night | luxury, dark, minimal, bold | Maison gravity: cinematic craft close-ups, a quiet serif caption, a dark button. |
| `tiffany/` | Tiffany & Co. | Grand Wordmark | luxury, heritage, calm, bright | An enormous serif wordmark on a portrait, and one signature colour for gifting. |
| `carolina_herrera/` | Carolina Herrera | Couture Red | luxury, bold, editorial, techy | Couture and graphic: studio portraits, a featured product carousel, a bold red field. |
| `bouguessa/` | Bouguessa | Burgundy Atelier | minimal, luxury, calm, dark | Serene tailoring: one calm portrait, long silhouettes on grey, a burgundy atelier band. |
| `net_a_porter/` | Net-a-Porter | Front Page Shop | editorial, bold, luxury, minimal | An edited fashion story you can shop: serif headlines, sharp black and white. |
| `madina_visconti/` | Madina Visconti | Sage Garden | natural, romantic, warm, dark | A sage-green world: Garamond stories, botanical portraits, handmade warmth. |
| `rino_pelle/` | Rino & Pelle | Colour Backdrop | bold, warm, luxury, editorial | A huge light serif headline on a saturated backdrop, black buttons, tidy product rows. |
