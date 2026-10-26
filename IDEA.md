# Sous

**A sous chef who watches the pan.** Prop your phone up by the stove and open Sous
in the browser. It watches the cooking through the camera, measures what is
happening in the pan, and tells you the moment to flip, lower the heat, or take it
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

1. **Pick a step.** Type or say the step ("sear skin-side down until deep golden,
   6-8 min"), or paste a recipe. **Muse Spark** turns it into a *watch spec*: what
   to segment ("chicken thigh", "onion", "pan"), what signal means done (colour,
   area shrinkage, bubbling), and the expected time window. Structured output, so
   the spec is machine-checkable.
2. **Watch.** The phone records rolling 5-second clips. **SAM 3.1** video mode masks
   and *tracks* each piece of food across frames. Inside each mask we compute real
   numbers: mean browning, the share of each piece past a doneness threshold, and
   how much it has shrunk since the start. Per piece, so "the thigh on the left is
   ahead."
3. **Judge.** When a number crosses a threshold, or every ~15 s, **Muse Spark** gets
   the latest clip (frames plus the sizzle on the soundtrack), the measured numbers,
   and the step. It returns a verdict: `{state, confidence, action, say}`.
4. **Talk.** The phone speaks `say` ("Flip the left one now, give the right one a
   minute"). **Muse Voice Transcribe** listens hands-free on the realtime websocket
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

## The demo (3 minutes)

A real stove and real food. Onions caramelising are cheap and read well on camera;
chicken thighs give the flip moment. A split screen: the live camera with SAM masks
tinted by doneness, and a browning curve climbing toward the target line. Sous calls
the flip, the cook flips, and the curve resets for side two. Then a cold question by
voice, "is it burning?". Close on the replay.

## The 10-day plan

| Day | Deliverable |
|---|---|
| Mon 26 | Environment and smoke test across all models (done, pending key). Create the public repo. Record 5-6 real pan clips as fixtures. |
| Tue 27 | SAM video on the clips: masks → browning % and area per piece. A notebook that plots the curves. |
| Wed 28 | Calibrate: label the clips by hand (raw / almost / done / over) and tune thresholds until the curves agree. Normalise lighting against the pan rim. |
| Thu 29 | Spark: step → watch spec, then clip + metrics → verdict JSON. Offline eval against the labels. |
| Fri 30 | Live loop: a FastAPI backend plus a phone web page (getUserMedia → 5 s clips → verdict → speech). |
| Sat 31 | Hands-free voice (realtime ASR), "show me the target" with Muse Image. |
| Sun 1 | Replay page. Latency and cost pass. |
| Mon 2 | Hardening: no food in frame, steam and glare, phone moved, dropped connection. Deploy over HTTPS (camera access needs it). |
| Tue 3 | Record the demo video and write the submission. |
| Wed 4 | Buffer. Submit before 9 PM ET. |

## Risks, faced up front

- **Eligibility.** The rules exclude spouses of Meta employees and contractors.
  Settle this with the organisers in writing before Day 2.
- **Latency.** Verdicts won't be instant. A 5 s clip plus a SAM pass plus a Spark
  call is likely 10-20 s. For cooking that's fine, since nothing goes from golden to
  burnt in 15 s, except garlic. Measure it on Day 2 and design to the number.
- **Cost.** SAM video is $0.20 per 1,000 frames. A 10-minute cook at 4 fps is 2,400
  frames, about $0.50. Spark judging every 15 s is about 40 calls. Each cook comes to
  roughly $1 with the full loop on, well inside the $150 credit.
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
