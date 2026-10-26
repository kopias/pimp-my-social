# Sous

**A sous chef who watches the pan.** Prop your phone up by the stove and open Sous
in the browser. It watches the cooking through the camera, measures what is
happening in the pan, and tells you the moment to stir, lower the heat, or take it
off. You don't have to touch the screen with greasy hands.

Track: **Indie Developer**, judged on creativity, technical ambition, and whether
it works.
Theme: **Build for Your World**, with a strong edge of **Push the Frontier**: it gives
a phone a sense it doesn't have today, which is reading a physical process in real
time and steering it.

## Where it comes from, and why it is a new build

The problem comes from Chef's Touch, which writes people a recipe and then leaves
them alone at the stove. That is exactly where home cooks fail. Undercooked
chicken, burnt garlic, onions pulled before they caramelise.

**Sous is built from scratch in this public repo, between Oct 26 and Nov 4.** The
rules say only work from the event counts, and that judges must be able to tell
what was built during the event or the project is disqualified. So:

- No code, assets or data copied from Chef's Touch, or from any other existing
  project. Chef's Touch is the reason Sous exists, not a dependency.
- Sous is a standalone web app. The phone browser's camera is enough; no App Store
  build is needed.
- Every commit is in the event window, in a public GitHub repo.
- The demo shows only Sous.

## What Sous does

1. **Pick a step.** Type or say the step ("cook the onions low and slow until deep
   brown, 25-30 min"), or paste a recipe. **Muse Spark** turns it into a *watch spec*: what
   to segment ("sliced onion", "mushroom", "pan"), what signal means done (colour,
   area shrinkage, bubbling), and the expected time window. Structured output, so
   the spec is machine-checkable.
2. **Watch.** The phone records rolling 5-second clips. **SAM 3.1** video mode masks
   and *tracks* each piece of food across frames. Inside each mask we compute real
   numbers: mean browning, the share of each piece past a doneness threshold, and
   how much it has shrunk since the start. Per piece or per region of the pan, so
   "the onions at the back are catching."
3. **Judge.** When a number crosses a threshold, or every ~15 s, **Muse Spark** gets
   the latest clip (frames plus the sizzle on the soundtrack), the measured numbers,
   and the step. It returns a verdict: `{state, confidence, action, say}`.
4. **Talk.** The phone speaks `say` ("Stir now, the back of the pan is catching",
   "Turn the heat down, the garlic is going"). **Muse Voice Transcribe** listens hands-free on the realtime websocket
   ("how long left?", "is it burning?", "next step").
5. **Show the target.** **Muse Image** edits your own pan photo into what it should
   look like when done, so the comparison is like for like.
6. **Replay.** After the cook, a timeline of the session with SAM overlays and the
   browning curves, shareable as a link.

The point that makes this credible: **the decision rests on measurement, not
vibes.** SAM gives pixel-accurate regions, so "62% of the skin surface is past
golden" is a number we plot live on screen. The VLM explains it; it doesn't invent
it. That is what we demo.

Every model does something only it can do: Spark for planning and judgement, SAM for
geometry, Voice Transcribe for hands-free control, Image for the target. Muse
Wonder, run through Claude Code (`bin/claude-muse`), does the coding.

## What the camera can see (why the demo is onions, not steak)

The phone sits above the pan, so Sous can only judge the surface facing up. That
rules out the obvious showcase: a thigh seared skin-side down browns on the side
touching the pan, and from above you only see pale raw flesh until the flip. The
Day 4 judge test tripped on exactly this (see the README).

So Sous leads with food whose browning faces the camera and changes the whole way
through:
- **Caramelising onions:** pale, then golden, then deep brown over 25-30 minutes.
  They need stirring, catch at the edges first, and forgive a restart. This is the
  hero demo.
- **Mushrooms:** they release water and shrink, then brown. Shrinkage (area) and
  browning together tell "still steaming" apart from "searing now".
- **Garlic:** golden to bitter in under a minute. This is the stress test for
  latency, and the place a "turn the heat down" call earns its keep.

Searing meat is a stretch goal, not the pitch. If there is time, a phone at about
45° can watch the opaque band climb up the side of a thigh ("flip when it's cooked
halfway up"), which is a different measurement from surface browning. Until then
the README and video don't claim meat.

## The demo (3 minutes)

A real stove and real onions, filmed from above. A split screen: the live camera
with SAM masks tinted by doneness, and a browning curve climbing toward the target
line. Sous notices the edge of the pan running ahead and says "stir now"; the cook
stirs and the uneven patch evens out on the curve. A cold question by voice, "how
long left?". Then a cut to garlic: Sous calls "heat down" before it turns. Close on
the replay of the whole onion cook, compressed to 20 seconds.

## How it gets judged, and what that means for the build

1. **Pass/fail:** does it fit a theme and use Meta AI products? Sous names its theme
   in the first line of the submission, and the README lists the Muse model behind
   each feature.
2. **Rubric, 0-10:** creativity, technical ambition, whether it works. (Fill in the
   exact rubric once it is published.)
3. **Live final, Nov 9, 12:00 PM ET:** the top 5 indie entries demo live and
   judges rank them. A live cook is the strongest demo here, and also the riskiest.
   So build for it from the start:
   - **Replay mode.** Feed a recorded pan clip through the *same* live pipeline
     (real SAM, real Spark, real speech), selectable with one switch. That is not a
     faked demo: everything after the camera is live. Use it if the stove, the light
     or the network misbehaves.
   - **A kitchen rehearsal** at noon ET on a weekday before Nov 4: same light, same
     phone stand, same wifi.
   - **Cheap food on standby:** onions, which forgive a restart. Pre-slice and
     part-cook a batch so the live demo starts at golden, not raw.

## The 10-day plan

Done on Day 1 (Mon 26), ahead of plan: environment, smoke test across all models,
public repo, browning measurement (BI inside SAM masks, curves, overlay) and the
Spark judge (watch spec, verdicts, safety guard), tested on an AI-generated clip.

| Day | Deliverable |
|---|---|
| Mon 26 | ✅ The above. **Film the real clips** (list below). |
| Tue 27 | Run the real clips through `scripts/browning.py`. Onions are many small pieces, not two thighs: measure the pile as a whole plus a 3x3 grid of pan regions, so "the back is catching" is a measured fact. |
| Wed 28 | Calibrate: label the clips by hand (raw / golden / deep brown / burnt) and set `SHADE_BI` and `BROWNED_BI` from them. Check the lighting correction against the stove or pan rim. Teach the judge "stir" (one region ahead of the rest) and "lower heat" (rate too fast for the step's time). |
| Thu 29 | Judge eval on the real clips: replay each, compare calls to the hand labels. Fix what's wrong. |
| Fri 30 | ✅ (done Mon 26) Live loop: a FastAPI backend plus a phone web page (getUserMedia → a frame every few seconds → verdict → speech). |
| Sat 31 | Hands-free voice (realtime ASR), "show me the target" with Muse Image. |
| Sun 1 | Replay page. Latency and cost pass. |
| Mon 2 | Replay mode for the live final. Hardening: no food in frame, steam and glare, phone moved, dropped connection. Deploy over HTTPS (camera access needs it). |
| Tue 3 | Record the demo video and write the submission. |
| Wed 4 | Buffer. Submit before 9 PM ET. |

Stretch, only if the days above finish early: the 45° camera for searing meat.

### Clips to film (into `fixtures/`, git-ignored)

All from directly above, phone fixed on a stand, the whole pan in frame plus a
strip of stove or counter around it (the lighting reference). Kitchen lights on as
they'll be for the demo; no hand-held, no zoom. Keep the phone still for the whole
clip, apart from the cook's hand coming in to stir.

1. **Onions, the full caramelisation**, raw to deep brown, 25-30 min, stirring as
   normal. The hero clip.
2. **Onions pushed too far**: medium-high heat, stop stirring near the end so the
   edges blacken. This gives the "stir now" and "overdone" labels.
3. **Mushrooms**, sliced, from raw through the wet stage to browned, ~10 min.
4. **Garlic, taken too far**: sliced garlic in oil until it's past golden, ~2 min.
5. **Onions under different light**: 2-3 minutes with only the hood light, or
   a window, to test the lighting correction.
6. **Optional, for the stretch goal:** chicken thighs from a 45° angle, through the
   flip.

Note roughly when you'd have called each stage (golden, deep brown, burnt, when
you stirred). Those are the labels for calibration.

## Not an anti-project (for the submission)

The kickoff listed overdone projects to skip. Sous sits next to three of them, so
the submission says plainly why it is none of them:

> **Not a simple image analyzer.** Sous never answers a one-off question about a
> photo. It is a closed loop: it tracks each piece of food through continuous video
> with SAM 3.1, measures how its surface changes over time, decides when a threshold
> has been crossed, and acts by speaking to the cook, who answers by voice. The
> output is a timed action ("stir now, the back is catching"), not a description.
>
> **Not a nutrition coach.** Sous knows nothing about calories, macros or diet. It
> is about technique, meaning heat and timing, the way a sous chef stands beside a
> cook.
>
> **Not a dashboard.** The browning curve on screen is the evidence behind each
> spoken call. The product is the call.
>
> **Not food-safety or medical advice.** A camera sees surfaces, not the inside of a
> chicken thigh. Sous judges browning only, and for poultry and pork it always says
> to confirm with a thermometer (74 °C / 165 °F for poultry). It never says "safe to
> eat".

Guardrails this puts on the build:
- Never call it a "coach" anywhere: UI, README, video, submission.
- No calorie, diet or health features, even as stretch goals.
- Thermometer prompt hard-coded for poultry and pork; "done" means "surface done".
- No Streamlit. The FastAPI backend and phone web page stay as planned.
- The demo leads with the spoken call and the stir, not the chart.

## Risks, faced up front

- **Eligibility.** The rules exclude spouses of Meta employees and contractors.
  Settle this with the organisers in writing before Day 2.
- **What the camera can see.** From above, Sous only sees the top surface. Food
  that browns face-down (seared meat) is out of reach until the 45° stretch goal.
  The pitch and the demo stick to onions, mushrooms and garlic.
- **Latency.** Measured on Day 1: SAM is 2.0 s per frame, Spark verdicts 2.7-9 s.
  So a call lands 5-12 s after the frame. Fine for onions and mushrooms. Garlic is
  the tight one: the judge has to call "heat down" from the rate of change, early,
  not wait for the colour to arrive.
- **Cost.** Live, one SAM image every 3 s is $2.50 per 1,000, so a 30-minute
  onion cook is 600 frames, about $1.50. Spark judging every 15 s adds about 120
  calls, well under $1. Call it $2-3 per cook, inside the $150 credit. Calibration
  replays use video mode at $0.20 per 1,000 frames, which is cheap.
- **Lighting.** Colour-based browning drifts with light. Normalise against a
  reference region (the pan rim, also segmented by SAM), and lock white balance
  where the browser allows it.
- **Steam and glare.** These are the reason for using tracking over several frames
  rather than a single shot. Confidence values from SAM gate the verdict.

## Alternatives considered

- **Play Smooth Piano hand-tracking.** SAM tracks hands over a keyboard and the
  pipeline checks the notes. Technically strong, but it is entangled with an
  existing product, and its audio side is where Muse is weakest today (Spark 1.3
  audio is flagged as degraded).
- **A Tyngo-style travel agent on Muse Wonder.** Polished, but it is the same story
  every other entry will tell.

Sous wins because it uses every model for something only that model can do, and
the demo is physical and instantly legible.
