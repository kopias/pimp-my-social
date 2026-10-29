---
name: got-x-campaign
description: Framework for a small business's social campaign in the "got milk?" register - a poster roster, a deprivation still and a short observational metaphor film, all ending on a "got ___?" lockup. Use when writing or judging social content for a makeover, so the posts sell the way great commercials do (by allusion) instead of by product claims. Ported from the Loreto "got skills?" campaign; pms/campaign.py runs it with Meta models.
---

# The rule that decides everything

Every piece is the same sentence underneath: **the customer believed a problem was a
deficiency in them, and it was something this business fixes all along.** Write it as
**"You are not X. You are Y."** If a concept cannot be reduced to that sentence it is
off brief, however good the picture is.

- Reformer film: *you are not weak, you are on three springs.*
- Piano film: *you are not unmusical, nobody showed you the shape of the song.*

Every example line in this file belongs to another brand's campaign. They show the
shape. **Never reuse their words**; write this business's own.

Got Milk never argued milk was nutritious. **Never argue the product is good.** No
claims, no features, no prices, no "quality", no "handcrafted with love". Situation,
then card. The card does the work.

# The lockup

Three elements and nothing else, at the bottom or dead centre:

    got ___?          the business's own word, lowercase: got milk? got skills? got songs?
    ────────          a 200px rule in the brand's accent colour
    business.com      the bare address in a monospace

The question ports between brands by swapping one word and the accent colour; nothing
else changes. The word is plain and from the customer's world (got linen? got bread?
got rhythm?), never the business name and never a slogan.

# Register 1: the poster roster

Copied from the milk mustache ads. One portrait per post, so a month of posts is a roster.

- **Casting is glamorous on purpose.** The milk ads were celebrities. Beautiful women,
  handsome men, children in sport, robots. Never a real or famous person, never a
  lookalike. Vary age, build and background across the roster.
- **Each person is in their element**, visibly brilliant at a discipline: a boxer, a
  ballet dancer, a pastry chef, a climber, a cellist. Pick disciplines whose world rhymes
  with the business's customers. Waist up, so the discipline reads from clothes and
  setting while the pixels stay on the face and hand.
- **The pose is fixed: a closed fist resting against the chin and jaw**, the back of the
  hand beside the face, looking straight down the lens. It is literally the Shaq milk
  ad pose. Never a pointing finger (see the traps).
- **They wear or hold the real product**, exactly as it is. The product is in the picture;
  it is never mentioned in the copy.
- **Headline:** a wry first-person aside, two short lines. *"I blamed my abs for a month."*
  *"I counted it wrong for eleven years."* Not a claim, not a pun on the product.
- **Body:** about forty words, first person, arriving at the thesis without stating it as
  a slogan. It is about the person: what they believed, what they did about it, the
  moment it turned out not to be them. It never describes the product or what it does
  ("buttons without a fight", "cut with room" are claims; leave them to the picture). Never the words AI, agent, algorithm, elevate, unlock, game changer.

# Register 2: the deprivation still

The Aaron Burr mechanic from the original "got milk?" TV spot: show the world without
the thing. Loreto's best asset was **humanoid robots piled against the barrier past the
finish line of a track race, handlers walking in with hands on their heads**, over
*"Nobody wrote down how to stop."*

- **One gross, unambiguous physical event.** Image models refuse to depict subtle
  failure; they render competence. A pile-up, a collapse, a spill, a tear, a heap reads;
  "struggling" never does.
- **Ground it in real furniture.** The robot crash only worked once it had the real look:
  blue track, padded barriers, numbered bibs, handlers in team polos, a fire
  extinguisher. Name those details.
- **Keep it generic and unbranded.** Showing a real company's product failing is
  disparagement, not a joke.
- **Nobody is mocked.** Robots, mannequins, objects and weather can fail comically. A
  person in this register is dignified and the situation is what's absurd.
- **One deadpan line**, no exclamation, no explanation, in this business's own words
  (not "Nobody wrote down...", which is Loreto's).

# Register 3: the metaphor film

The reformer film, the one the client called *the template for everything after*. A man
fails at Pilates for weeks; an instructor unclips two of the three springs. The product
is never demonstrated.

1. **The misconfiguration flip.** Someone believes the failure is in them; it was a wrong
   setting, a wrong size, a missing instruction all along.
2. **Observational, never a talking head.** Nobody addresses the camera, no selfie
   framing, no first-person voiceover, until the very last beat's glance to the lens.
3. **Ordinary, dignified casting.** Never a model, never comic, never anyone mocked. The
   person is competent and trying; the instruction failed them, not their body. Getting
   this wrong turns the whole argument onto the person.
4. **Four beats:** *failure* (the gross physical event), *face* (a reaction close-up
   before the reveal, eyes sharp), *fix* (the one thing that changes, which is where the
   product arrives), *payoff* (the same person, now in their element, ending on a wry
   glance straight to the lens). Then the lockup.
5. **Captions are seven words at most** and together they are the thesis.
   *Six years. It held the mail. / I thought I wasn't musical. / Nobody showed me the
   shape. / Turns out it was written down.*
6. **Describe movement mechanically, never emotionally.** Not "she looks frustrated":
   "her shoulders rise, the seam across her back pulls tight, she stops mid-reach".
   Not "he looks relieved": "his gaze drops, holds, comes back, brows lift a fraction".
7. **Restate the wardrobe and the set in every shot.** Continuity is per prompt.
8. **The proof is real.** The product in the fix and payoff is the business's own
   reshoot, passed to the image model as a reference, never reinvented.

# Not this: the testimonial

Loreto also shipped a literal first-person story (a student explaining how the product
saved her degree). It worked, and the client asked for the metaphor instead from then
on: *a literal testimonial spends attention; a metaphor earns it.* Don't write
testimonials, before/after product demos or "3 reasons to shop" lists here.

# The traps (each one happened)

- **The middle finger.** A finger-to-the-temple pose renders as an unmistakable middle
  finger about one time in three. The closed fist has no offensive failure mode. Every
  hand is still checked close up.
- **The magazine.** The words *editorial*, *magazine* and *full length* return a photo of
  a printed magazine spread. Never use them; waist-up framing fixes it.
- **Hallucinated lettering** appears about half the time. Patch it with a local defocus;
  **never reshoot an approved cast to fix lettering**. Reshoot only when the shot itself
  is wrong (a bad hand, a page border, the wrong product).
- **Same prompt, different person.** Separate prompts return different people. Make one
  cast reference and pass it into every shot.
- **The Nike spec ad.** Cinematic words win over the action. Lead with the action and
  name every flourish you don't want: no haze, no god rays, no grading, no slow motion.
- **The model never draws type.** Every word is set by the browser.

# Disclosure

Realistic people made by an image model get "Made with AI" on the post. The persona is
fictional: never give them a real name, a handle or a backstory presented as true.
