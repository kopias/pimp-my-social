# Pimp My Social: submission notes

**Track:** Indie Developer. **Theme:** Build for Your World. Small businesses are
the ones left behind by every shift in how people find things: first search, then
social, now AI assistants and agents. Pimp My Social takes a business's existing
website and hands back everything they'd need an agency for, in about ten minutes.

## What it does

1. **Inspection.** Chrome renders the site the way a customer, a search engine and an
   AI agent see it. 17 measured checks score it across search, AI answers, agent
   readiness, social sharing and speed.
2. **Your feeds.** A homepage shows a few products; the feed shows the rest. Under the
   URL the owner can paste their Instagram, TikTok or shop link and the page says
   what it is as they type (an Instagram link pasted into the website box moves itself
   over). The Instagram their site links to is read anyway, as is a Shopify store's
   public catalogue. Chrome opens the profile as a logged-out visitor; Muse Spark looks
   at each post with its caption and sorts it: product, worn, event, behind the scenes,
   announcement, someone else's post. A platform that shows a bot check (Etsy does) is
   reported as unreadable, never worked around.
3. **Brand read.** Muse Spark reads the screenshots, the site's photos, the catalogue,
   the product posts and the pages into a brand profile: products chosen to cover the
   whole range, with exact prices matched to their photos, voice, FAQs answered from
   the site's own words, and what customers can't find out.
4. **Paint job.** The owner's style tags map to a library of 25 template skills, each a
   measured build spec of a leading fashion site (COS, GANNI, KHY, Sézane, Dior,
   Tiffany & Co., Net-a-Porter...). Spark picks the ones that fit the brand (3 to 6
   options, fewer when the ask is precise) plus a random wildcard. Muse Image reshoots a
   product in each look and **Muse Wonder sketches the owner's own homepage in each**,
   drawing a different headline, lead product and twist every time, so the same inputs
   never give the same set. The owner picks from the thumbnails; that sketch is the
   brief for the full build.
5. **Photo studio.** SAM 3.1 isolates each product from the owner's photo; Muse Image
   reshoots it (set, light, lens, depth of field); SAM finds it again and scores
   fidelity, so a reshoot that changed the product is caught.
6. **Logo.** Spark reads what the current logo is about; Muse Image redraws it as one
   clean mark; Spark checks the remake still reads as the business. The old logo is
   the reference, never the asset.
7. **The build.** Spark writes the copy; **Muse Wonder** builds the site on the chosen
   template from its skill and screenshots. Spark then screenshots the result on desktop
   and phone and scores it against the template side by side; below 8/10 Wonder revises
   from Spark's list of differences. Code adds what must be right every time: JSON-LD, Open Graph,
   robots.txt that welcomes AI crawlers, sitemap.xml, llms.txt, and **WebMCP** tools
   so browser agents can query products, prices, hours and answers directly.
8. **Social kit.** Posts for each chosen channel (Instagram, TikTok, Facebook,
   LinkedIn, X) in the brand's voice, type-set in the direction's fonts.
9. **The campaign.** One idea, every post, in the Got Milk register. Spark finds
   the brand's flip ("You are not the wrong size. You are in clothes cut for
   someone else.") and a lockup (8 AM Fashion's came back "got fit?"), then writes
   three posters (glamorous people in their element, fist under the chin, wearing
   the real pieces), a deprivation still and a four-beat observational film. Code
   gates the copy (no claims, no prices, no banned words). **Muse Image** shoots it
   from the studio photos, passing one cast reference into every film shot so it's
   the same person from cut to cut. **SAM 3.1 finds every hand** and Spark counts
   the fingers; stray lettering is softened in place, never reshot. The browser
   sets every word. **Spark watches the film** and one revision follows its notes.
10. **Remix a hit** (optional). Popular post formats, reverse engineered into their essence
   (hook, beats, motion, text, sound, why it works), then rebuilt with only this
   business's products, prices and place. Owners can upload a post that's working:
   **Spark watches it** and **Muse Voice Transcribe hears its speech**, and the
   format joins the library. Muse Image shoots any new angle a format needs (a
   location lookbook puts the real garment on an AI model, labelled "Made with AI").
   **Spark watches each cut** against the format and the facts; a weak one is
   re-grounded from its notes. The library ranges from a fast fit check to a
   letterboxed, graded campaign film.
11. **The reveal.** The same 17 checks on the new site, a before/after report with
   what was missing, what was added, and a value calculator built on published
   figures, a brand **skill file** any AI tool can load, and one zip.

## Every Meta model, doing what only it can

| Model | Job |
|---|---|
| Muse Spark 1.3 | vision brand read, art direction picks, **site-vs-template fidelity check**, logo read + check, copy, social plan, **campaign brief + every image check (hands, product match, lettering) + film review**, **reverse engineering popular posts** (it watches them), grounding, **video review** |
| Muse Wonder 1.0 | sketches the owner's homepage in every option they're offered, then builds the website on the chosen one of 25 measured fashion-site templates (it sees the template's screenshots) and revises it from Spark's side-by-side check |
| Muse Image 1.0 | direction previews, product reshoots, logo redraw, campaign casting (multi-image edits: cast reference + product photo), new angles for video formats |
| SAM 3.1 | product isolation, reshoot fidelity check, finding every hand for the campaign check, lifting the person off the set for film parallax |
| Muse Voice Transcribe | hears the speech in an uploaded post so its script's shape carries into the remix |

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
