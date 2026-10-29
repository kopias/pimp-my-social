---
name: premium-site-inspo
description: Reference library for designing premium brand websites. Use when designing or reviewing a small business's site, landing page or storefront so it reads like a top fashion or lifestyle house rather than a template. Holds design notes on real brand sites, a premium typography system, and the rules for using a business's own logo.
---

# Premium site inspiration

What separates a premium site from a template is rarely the colour or the photos. It
is restraint: fewer, larger things; type set with care; space doing the work that
boxes, shadows and badges do on cheap sites. This folder holds the evidence for that,
taken from real brand sites, so a makeover can be built from examples instead of
from memory.

## How to use it

1. Read `typography.md` first. It applies to every direction.
2. Open the references for the direction you're building (each direction in
   `pms/directions.py` lists its `refs`). Borrow the **structure**: grid, rhythm,
   type scale, navigation pattern, how products and prices sit.
3. Never borrow the **content**: their logos, wordmarks, photography, copy or product
   names. The business's own brand goes into the borrowed structure.
4. Screenshots live in `shots/` on the machine that captured them, not in git (they
   are the brands' own images). Refresh them with `uv run scripts/capture_inspo.py`.

## The references

| File | Brand | What to take from it |
|---|---|---|
| `references/toteme.md` | Toteme | quiet luxury: centred wordmark, one small image in vast white, whisper-size captions |
| `references/lemaire.md` | Lemaire | warm off-white, nav as tiny text columns, one large off-centre photograph |
| `references/studio-nicholson.md` | Studio Nicholson | muted, spaced serif wordmark, tonal photography, calm product grid |
| `references/aime-leon-dore.md` | Aimé Leon Dore | heritage: putty ground, product as a still life, a dateline under the masthead |
| `references/our-legacy.md` | Our Legacy | 50/50 split: huge grotesk caps beside a full-height runway photo |
| `references/bode.md` | Bode | craft and archive: a saturated colour-field hero, black-and-white archival grid |
| `references/story-mfg.md` | Story mfg. | handmade collage, earthy olive, stamped labels, texture close-ups |
| `references/kotn.md` | Kotn | direct-to-consumer clarity: two big images, swatches and prices in one tidy row |

## Rules for the business's logo

- The business's current logo is the **reference**, not the asset. The makeover
  remakes it: keep its core idea (the motif, the initial, the shape everyone knows)
  and redraw it to the standard of the new site, as a clean single-colour mark with
  the name set in the direction's display type beside it.
- The new site uses only the remade logo. The original appears in the reveal, next
  to the new one, so the owner can see what changed and why.
- Never invent a motif the original didn't have. If the original can't be read, set
  the name as a wordmark in the display font and say so.
- Give the logo room: at least its own height of clear space on every side. Never
  put it in a coloured box or pill; never add a drop shadow.
- Header logos sit at 28 to 56px tall on desktop. Logos with small text inside
  ("Made in Oakland") need the larger end or the text turns to noise.
