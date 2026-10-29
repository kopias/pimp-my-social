---
name: template-net-a-porter
description: Net-a-Porter-style build spec - the editorial luxury retailer with a big centred wordmark, a dense uppercase nav row, an edited 'what's new' story led by a large campaign image with a serif headline and an uppercase shop link, then a magazine-like mix of story blocks and product rows. Use for editorial, bold, luxury, minimal brands that want to read like a fashion magazine shop.
---

# Net-a-Porter: the shop that reads like a magazine

Source https://www.net-a-porter.com/en-us/ · 2026-10-29: the site denies automated browsers
on desktop and mobile, so this skill is written from its public design; no shots on file.

**Feeling:** the front of a fashion magazine you can buy from. Edited, authoritative, crisp.

```json
{
  "id": "net_a_porter", "name": "Net-a-Porter", "style": "Front Page Shop", "tags": ["editorial", "bold", "luxury", "minimal"],
  "pitch": "An edited fashion story you can shop: serif headlines, sharp black and white.",
  "palette": {"bg": "#FFFFFF", "surface": "#F5F5F5", "ink": "#000000", "muted": "#707070",
              "accent": "#000000", "accent2": "#F5F5F5"},
  "fonts": {"display": "Playfair Display", "body": "Inter",
            "axes": {"Playfair Display": "ital,wght@0,400;0,500;1,400", "Inter": "wght@400;500;600"}},
  "measured": {"wordmark": "wide uppercase, centred, ~32px", "nav": "12px / 500 / uppercase / +6%",
               "headline": "40-56px serif, sentence case", "link": "12px uppercase underlined", "body": "14px"},
  "layout": "a white header with a small utility row, a large centred uppercase wordmark, and a dense centred row of uppercase category links; an edited story: a large campaign image (two-thirds width) beside a text column with a small uppercase kicker, a big serif headline, two lines of sans copy and an uppercase underlined shop link; a row of four products with designer name in bold uppercase over the product name; a second story reversed; a three-up 'edit' of portrait images with serif captions; a black newsletter band",
  "photo": "glossy fashion editorial photography, strong styling, clean studio or striking location, crisp light, the product sharp and central; product shots on white",
  "signature": ["large centred uppercase wordmark with a dense uppercase nav row", "story blocks: big image beside a serif headline and an uppercase underlined link",
                "small uppercase kickers above serif headlines", "bold uppercase brand line over each product name",
                "stories alternate image left / image right", "strict black and white"]
}
```

## Anatomy, top to bottom

1. **Utility row, 28px.** 11px links left (locale), right (account, bag).
2. **Header.** Wordmark centred, uppercase, wide tracking, 30-36px. Nav row under it: 9-10
   uppercase links, 12px medium. Hairline under.
3. **Lead story.** Image 64% left (4:5); text column right, vertically centred: kicker 11px
   uppercase tracked, serif headline 44-56px, 14px copy, `SHOP NOW` 12px underlined.
4. **Product row.** 4-up on white, brand line 12px bold uppercase (the business name or the
   collection), product name 13px, price 13px.
5. **Second story** reversed (image right).
6. **The edit.** 3 portrait images with serif 20px captions and underlined links.
7. **Black newsletter band,** white serif line + field.
8. **Footer.**

## Never

Pastel palettes, rounded cards, full-bleed text-on-photo heroes, playful type.
