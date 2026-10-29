# Premium typography

Every reference site in this folder follows these rules, and almost no template does.

## Scale: few sizes, far apart

- Four sizes do most of the work: **display** (hero), **heading**, **body**, **label**.
- Display: `clamp(52px, 8.5vw, 148px)`, line-height 0.9 to 0.98, letter-spacing
  -0.02em to -0.035em. Big type is set tight; small type is set loose.
- Headings: `clamp(28px, 3.4vw, 48px)`, line-height 1.05, letter-spacing -0.01em.
- Body: 15 to 17px, line-height 1.55 to 1.65, measure 56 to 66ch. Never full width.
- Labels (nav, eyebrows, captions, buttons, prices): 11 to 12px, uppercase,
  letter-spacing 0.12em to 0.18em, weight 500. This one style is the single biggest
  "expensive" signal on every reference site.

## Weight: light carries luxury

- Serifs at display size use weight 300 or 400. Never bold a display serif.
- Grotesks at display size may go heavy (700 to 900) only in a deliberate
  poster-style direction (see Our Legacy); everywhere else 400 to 500.
- Hierarchy comes from size and space, not from bold and colour.

## Detail

- `text-wrap: balance` on headings, `text-wrap: pretty` on paragraphs.
- `font-feature-settings: "kern", "liga"`; `font-variant-numeric: tabular-nums` on
  prices and numbers; `-webkit-font-smoothing: antialiased`.
- Italic of the display serif for one word of emphasis, not bold.
- Prices are small, tabular, in the label or body size, never the biggest thing on a
  product card. Sale prices: the old price struck through in the muted colour.
- Links: 1px underline with `text-underline-offset: .22em`, or none plus a hover
  underline. No blue.
- At most two families, plus an optional monospace for labels. No more.

## Buttons and fields

- Buttons are text or flat rectangles: 1px border or solid ink, square corners or
  2px radius, label style (uppercase, tracked, 11 to 12px), padding about 14px 28px.
- No pills with gradients, no shadows, no emoji, no icons inside every button.
- Fields: a single 1px bottom border, generous height, the label above in label style.

## Space

- Section padding is large: `clamp(72px, 12vw, 180px)` top and bottom.
- Let one image breathe in a lot of space rather than packing a grid.
- Hairline rules (1px, 10 to 15% ink) separate things; boxes and cards mostly don't.

## Fonts on Google Fonts that hold up at this level

| Role | Families |
|---|---|
| Refined serif display | Cormorant Garamond, Bodoni Moda, Newsreader, Fraunces (opsz), Instrument Serif, Libre Caslon Display |
| Quiet grotesk body | Hanken Grotesk, Inter Tight, Manrope, Work Sans, Schibsted Grotesk, Geist |
| Poster grotesk display | Archivo (800 to 900), Inter Tight (800), Familjen Grotesk |
| Labels | JetBrains Mono, IBM Plex Mono, or the body grotesk in caps |
