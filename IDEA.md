# Chef's Touch: Sous

**A sous chef who watches the pan.** Prop your phone up by the stove. Sous watches
the cooking through the camera, measures what is happening in the pan, and tells you
the moment to flip, lower the heat, or take it off. You don't have to touch the
screen with greasy hands.

Track: **Indie Developer**, judged on creativity, technical ambition, and whether
it works.
Theme: **Build for Your World**, with a strong edge of **Push the Frontier**: it gives
a phone a sense it doesn't have today, which is reading a physical process in real
time and steering it.

## Why Chef's Touch, and why not just port it

Chef's Touch is the right base. It has real users, a working recipe and photo
pipeline, and an App Store listing. Every model in it maps straight onto Muse:

| Today | Muse |
|---|---|
| GPT for recipes and vision | Muse Spark 1.3 |
| Gemini "Nano Banana" step photos | Muse Image 1.0 ($0.01 per image) |
| Whisper voice notes | Muse Voice Transcribe |
| (nothing) | **SAM 3.1** and **Muse Spark video** |

But a provider swap isn't a hackathon entry. Indie judges score creativity and
technical ambition, and a swap shows neither. It is day-one plumbing. The entry is
the new capability that only becomes possible with SAM and video understanding:
measuring a physical process from a phone camera and acting on it. That covers the
ambition. "Whether it works" is the third criterion, and a live cook on camera
proves it in a way a slide can't. Building on an app that already ships means the
ten days go into the new part, not the scaffolding. Today Chef's Touch writes you a recipe and then leaves you
alone at the stove, which is exactly where people fail.

## What Sous does

1. **Pick a step.** Sous reads the recipe's current step ("sear skin-side down
   until deep golden, 6-8 min") and turns it into a *watch spec*: what to segment
   ("chicken thigh", "onion", "pan"), what signal means done (colour, area
   shrinkage, bubbling), and the time window.
2. **Watch.** Every few seconds the phone sends a frame. **SAM 3.1** masks each
   piece of food. Inside each mask we compute real numbers: mean browning, how much
   of each piece has passed a doneness threshold, and how much it has shrunk since
   the start. Per piece, so "the thigh on the left is ahead."
3. **Judge.** Every ~15 s, or when a number crosses a threshold, **Muse Spark** gets
   the last few seconds as a short video, the measured numbers, and the step. It
   returns a structured verdict: `{state, confidence, action, say}`.
4. **Talk.** The phone speaks `say` ("Flip the left one now, give the right one a
   minute"). **Muse Voice Transcribe** listens hands-free ("how long left?", "is it
   burning?", "next step").
5. **Show the target.** **Muse Image** renders what *this* dish should look like at
   *this* step, edited from your own pan photo, so the comparison is like for like.
6. **Remember.** After the cook, a timeline of the session with SAM overlays becomes
   a shareable "cook replay". That feeds the existing Reels feature, so the
   hackathon work also grows the product.

The point that makes this credible: **the decision rests on measurement, not
vibes.** SAM gives pixel-accurate regions, so "62% of the skin surface is past
golden" is a number we can plot live on screen. The VLM explains it; it doesn't
invent it. That is what we demo.

## The demo (3 minutes)

Real stove, real chicken thighs (or onions caramelising, which is cheaper and reads
just as well on camera). A split screen: the live camera with SAM masks tinted by
doneness, plus a browning curve climbing toward the target line. Sous calls the flip,
the cook flips, and the curve resets for side two. Then a cold question by voice:
"is it burning?" Close on the generated cook replay posted to The Pass feed.

## The 10-day plan

| Day | Deliverable |
|---|---|
| Mon 26 | Environment and smoke test across all models (this repo). Record 5-6 real pan clips as fixtures. |
| Tue 27 | Swap Chef's Touch's `backend/ai.py` onto Muse (Spark, Image, Transcribe) behind a flag. Ship to the VM. |
| Wed 28 | SAM doneness metric on recorded clips: masks → browning % and area per piece. Tune the thresholds against what a cook would say. |
| Thu 29 | Spark judge: step → watch spec, then frames + metrics → verdict JSON. Offline eval on the clips. |
| Fri 30 | Live loop: frame capture in the Capacitor app → backend → spoken callouts. |
| Sat 31 | Hands-free voice (realtime ASR websocket), "show me the target" Muse Image. |
| Sun 1 | Cook replay → Reels. Latency and cost pass (Contributor mode for the judge if allowed in the US). |
| Mon 2 | Hardening: no-food-in-frame, steam/glare, phone moved, lost connection. |
| Tue 3 | Record the demo video and write the submission. |
| Wed 4 | Buffer. Submit before 9 PM ET. |

## Risks, faced up front

- **Eligibility.** The rules exclude spouses of Meta employees and contractors.
  Settle this with the organisers in writing before Day 2.
- **Prior work.** Chef's Touch predates the event. Check the Official Rules on
  pre-existing projects, and keep everything Sous-specific in commits dated in the
  window, so the new work is obvious to judges.
- **Latency.** Video judging won't be real-time. That's fine: SAM masks plus local
  maths run every couple of seconds, and the VLM runs only on threshold crossings.
  Measure end-to-end in the first two days and design to that number.
- **Cost.** SAM is $2.50 per 1,000 images. One frame every 2 s for a 10-minute cook
  is 300 frames, about $0.75 per cook. Fine for a demo; for production, drop to one
  frame every 5 s with on-device motion triggers.
- **Lighting.** Browning measured as colour drifts with light. Normalise against the
  pan rim (also segmented by SAM) as a reference.

## Alternatives considered

- **Play Smooth Piano hand-tracking.** SAM tracks hands over a keyboard and the
  pipeline checks the notes. Technically strong, but the pipeline is mostly audio,
  where Muse is weakest today (Spark 1.3 audio is flagged as degraded).
- **Tyngo on Muse Wonder.** A polished agent, but "the same agent on a different
  model" is the weakest story for judges.

Sous wins because it uses every model for something only that model can do, and
the demo is physical and instantly legible.
