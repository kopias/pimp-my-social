# Pimp My Social: submission notes

**Track:** Indie Developer. **Theme:** Build for Your World. Small businesses are
the ones left behind by every shift in how people find things: first search, then
social, now AI assistants and agents. Pimp My Social takes a business's existing
website and hands back everything they'd need an agency for, in about ten minutes.

## What it does

1. **Inspection.** Chrome renders the site the way a customer, a search engine and an
   AI agent see it. 17 measured checks score it across search, AI answers, agent
   readiness, social sharing and speed.
2. **Brand read.** Muse Spark reads the screenshots, photos and pages into a brand
   profile: products with exact prices matched to their photos, voice, FAQs
   answered from the site's own words, and what customers can't find out.
3. **Paint job.** Spark picks three style directions for the brand plus one random
   wildcard. Muse Image previews each on the owner's own hero photo. The owner picks.
4. **Photo studio.** SAM 3.1 isolates each product from the owner's photo; Muse Image
   reshoots it (set, light, lens, depth of field); SAM finds it again and scores
   fidelity, so a reshoot that changed the product is caught.
5. **The build.** Spark writes the copy; **Muse Wonder** designs and codes a bespoke
   editorial site. Code adds what must be right every time: JSON-LD, Open Graph,
   robots.txt that welcomes AI crawlers, sitemap.xml, llms.txt, and **WebMCP** tools
   so browser agents can query products, prices, hours and answers directly.
6. **Social kit.** Posts for each chosen channel (Instagram, TikTok, Facebook,
   LinkedIn, X) in the brand's voice, type-set in the direction's fonts.
7. **Short video.** A 15-second vertical video: SAM lifts each product off its
   background for parallax depth; every voiceover line is checked by **Muse Voice
   Transcribe**; **Spark watches the finished cut** like an editor, scores it, and
   if it's weak, rewrites the script from its own notes and the cut is made again.
8. **The reveal.** The same 17 checks on the new site, a before/after report with
   what was missing, what was added, and a value calculator built on published
   figures, a brand **skill file** any AI tool can load, and one zip.

## Every Meta model, doing what only it can

| Model | Job |
|---|---|
| Muse Spark 1.3 | vision brand read, art direction picks, copy, social plan, **video review** (it watches and listens to the cut) |
| Muse Wonder 1.0 | designs and codes the website |
| Muse Image 1.0 | direction previews, product reshoots |
| SAM 3.1 | product isolation, reshoot fidelity check, parallax layers in the video |
| Muse Voice Transcribe | checks every voiceover line against the script; captions file |

## Not an anti-project

> **Not a simple image analyzer.** No photo goes in for a description. Images are
> segmented, reshot, verified and composed into a website, posts and a video.
>
> **Not a dashboard.** The output is a working website, assets and a video. The
> report explains them.
>
> **Not a basic RAG app or a chatbot.** Nothing is answered from documents. The
> pipeline measures, builds and verifies.

## Guardrails

- **No invented facts.** Prices, hours, products and testimonials come only from the
  business's own site. Star ratings, review counts and awards are forbidden in every
  prompt; a code pass tones down shouting; the report asks the owner to check before
  publishing.
- **Product truth.** SAM's fidelity score flags any reshoot that changed the product.
- **Consent.** The owner confirms they own the business or have its permission.
- **Safety.** The crawler refuses private and local addresses (the URL comes from
  strangers), and at most two makeovers run at once to cap spend.
- **The demo business is fictional.** Marigold Lane Bakery and its photos were made
  for the demo, so no real business is made over without asking.

## Built during the event

The repo started Oct 26 as "Sous" (a pan-watching cooking assistant, tag
`sous-final`) and pivoted to Pimp My Social on Oct 28. All code is from the event.
