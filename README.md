# muse-hackathon

Workbench for the Meta Global AI Developer Hackathon (Oct 26 to Nov 4, 2026;
submissions close **Nov 4, 9 PM ET**). The idea is in [IDEA.md](IDEA.md).

## Setup

```bash
cd ~/Developer/muse-hackathon
uv sync                            # first time only: makes .venv from uv.lock
# 1. put your key in .env (dev.meta.ai/platform -> API keys)
# 2. check every model:
uv run scripts/smoke.py            # text image vision sam video asr
uv run scripts/smoke.py sam        # one at a time
```

Before the first call: submit the Cerebral Valley form to claim the $150 credit
(it arrives in batches and is not on the account yet), and set a spend alert on Billing.

## Run Sous live

```bash
uv run scripts/serve.py            # http://localhost:8000 in a desktop browser
uv run scripts/serve.py --https    # prints https://<LAN IP>:8443 for a phone on the same wifi
```

Pick or type the step, choose **Camera** or **Replay a clip**, press Start. A frame
goes to SAM every 3 s; Spark judges in the background when progress crosses a band
or every 15 s; the phone speaks each new call (repeats are held back for 45 s).
Piles (onions, mushrooms) show a 3x3 map of the pan; separate pieces show a bar
each. Replay runs a clip from `fixtures/` through the same pipeline: real SAM,
real Spark, real speech. For the AI test clips use 120 cooking minutes per clip
minute at ¼×. Every session is saved to `out/sessions/<id>/` (frames, readings,
verdicts), so a real cook doubles as a calibration clip.

On a phone, `--https` uses a self-signed certificate (in `certs/`, git-ignored):
accept the warning once. iPhone: "Show Details" → "visit this website".

## Meta Model API at a glance

One base URL (`https://api.meta.ai/v1`), one bearer key (`MODEL_API_KEY`). It is
compatible with the OpenAI SDK (Responses and Chat Completions) and the Anthropic
Messages API.

| Model | ID | Use | Price |
|---|---|---|---|
| Muse Wonder | `muse-wonder-1.0` | hardest agentic and coding work, 1M ctx | $4 in / $20 out per M |
| Muse Spark 1.3 | `muse-spark-1.3` | text, vision, **video**, tools, structured output | $1.25 / $4.25 per M |
| Spark Contributor | `muse-spark-1.3-contributor` | same model, trains on your data, select countries | $0.10 / $0.20 per M |
| Muse Image | `muse-image-1.0` | generate and edit, multi-turn | $0.01 / image |
| SAM 3.1 | `sam-3.1` | text-prompted boxes and masks, image and video tracking | $2.50 / 1k images, $0.20 / 1k frames |
| Voice Transcribe | `muse-voice-transcribe-1.0` | STT, file or realtime websocket | $0.18 / hr |

Things worth knowing:
- **Video:** upload an mp4 via `files.create(purpose="user_data")` and pass it as
  `input_file`. Spark also hears the soundtrack.
- **Audio in Spark 1.3 is degraded.** Use Voice Transcribe, or Spark 1.2 for audio.
- **Reasoning eats the output budget.** Keep `max_output_tokens` at 4000 or more, or
  answers come back empty with `finish_reason: length`.
- **SAM** prompts are one short noun phrase per request ("chicken thigh"). The
  output is a special-token grammar; `meta_sam_parser` decodes it (wrapped in
  `muse.client.segment`). Max 16 objects. Ask for `mask_encoding: one_bit`.
- **Muse Image** accepts only the `image_generation` tool. It does its own web
  search; turn that off (`fast=True`) for speed when realism isn't needed.
- **Transcribe** wants mono 16-bit PCM WAV at 16 or 24 kHz, at most 10 minutes.

## Measured so far (Oct 26)

- SAM 3.1, one 960 px image: **2.0 s**. A 42-frame clip, one concept: **19.6 s**
  (about 0.5 s per frame). Two concepts sent at once on the same clip took 104 s,
  so don't run several SAM video jobs in parallel.
- Spark judge: watch spec in 2.4 s; verdicts 2.7-9.1 s each. On the AI clip it waits
  through the sear, calls the flip at progress ~1.0, and flags overdone past ~1.4.
  Given uneven pieces it says "flip the right one now, give the left one another
  minute", once positions come from the masks rather than from the model.
- One verdict on that clip went wrong in a way that matters: the AI frames show the
  skin facing up mid-sear, so Spark decided the thighs hadn't been flipped. A real
  camera above the pan never sees a face-down sear. **So the demo is onions,
  mushrooms and garlic, whose browning faces the camera**; seared meat waits for a
  45° camera (stretch goal). See IDEA.md.
- **AI onion clip** (`uv run scripts/make_test_clip.py onions`, raw → catching at the
  back → stirred → deep brown → nearly black). SAM sees onions as one pile
  (`"sliced onions"`, conf 0.85; `"onion"` finds nothing), so `--regions` cuts the
  mask into a 3x3 grid of pan regions. While the back catches, back cells read BI
  250-280 against ~110 at the front. **BI peaks at deep brown (~290) and then falls
  as the onions blacken (→ 239) while L\* keeps dropping (72 → 28)**, so the judge
  flags charring from lightness and treats it as overdone. Judge replay at 120x: wait
  ×4, "stir, the back is browning faster" ×2, almost, ready/remove at deep brown,
  overdone ×2. Verdicts 4-17 s. The lighting reference is `"pan handle"` (conf 0.94);
  `"gas stove"` finds nothing on a black stovetop. Muse Image refuses prompts with
  "burnt" in them.
- **Live loop** (headless Chrome, phone viewport, onion clip replayed): ~2 s per
  frame round trip (SAM 1.5-2.7 s), verdicts land a frame or two later. Spoken:
  "let them cook slowly" → "stir well, the back is catching" → "a few more minutes"
  → "take them off the heat". On single frames SAM loses `"sliced onions"` as they
  darken (0.54, then nothing), while `"food"` holds at 0.91-0.93, so the session
  falls back to `"food"` and stays there. Fake camera with no food: "I can't see
  the food" once, after two empty frames.
- So the **live loop segments one frame at a time** every few seconds; video mode
  is for replays and calibration.
- Browning Index on the AI cook-through clip climbs 22 → 263 (piece 0) and
  26 → 292 (piece 1), steadily, with SAM confidence ≥ 0.95 throughout. The
  thresholds still need real footage.

## Layout

```
muse/client.py     ask, ask_video, generate_image, segment, transcribe
muse/browning.py   Browning Index inside SAM masks, lighting reference, per-piece readings
scripts/browning.py      clip or photo -> out/<name>/{readings.json,curves.png,overlay.png}; --regions for piles
muse/live.py       one live cook: frame -> SAM -> readings -> background verdict; saves the session
server/            FastAPI app + the phone page (server/static/index.html)
scripts/serve.py   run it: localhost, or --https for a phone
muse/judge.py      Spark judge: step -> watch spec, readings + frame -> verdict; hard safety rules
scripts/judge.py   replay a measured clip through the judge, checkpoint by checkpoint
scripts/make_test_clip.py  AI cook-through clips (sear | onions) for testing without a stove
tests/             offline tests: `uv run pytest -q`
scripts/smoke.py   one live call per model, on fixtures it makes itself
bin/claude-muse    Claude Code driven by Muse Wonder (Anthropic-compatible surface)
fixtures/          generated test media (git-ignored)
```

## Coding with Muse

- `bin/claude-muse` runs Claude Code with Muse Wonder as the model
  (`MUSE_CODE_MODEL=muse-spark-1.3 bin/claude-muse` for the cheaper one). This costs
  API credit like any other call.
- Meta's own agent: `curl -fsSL https://dev.meta.ai/install.sh | sh`, then `muse`.
  Read the installer before you run it.

Docs: https://dev.meta.ai/docs

## Rules that shape this repo

From the kickoff: new work only (built Oct 26 to Nov 4), the GitHub repo must be
**public**, and judges must be able to tell what was built during the event, or the
project is disqualified. Nothing here is copied from earlier projects. `.env` is
git-ignored; never commit a key.

## Event logistics

- **Submissions close Wed Nov 4, 9:00 PM ET.** Judging Nov 5-8, closing ceremony
  and live finals Nov 9 at 12:00 PM ET, community vote winner announced Nov 16 on
  Discord.
- **Prizes, indie track:** $150K / $100K / $75K / $50K / $25K, plus $50K in bonus
  prizes across the event.
- **Discord** (home base): https://cv.inc/e/meta-ai-developer-hackathon/discord
  - `#questions`: ask the CV team (ping @CV). Rules and eligibility go here.
  - `#office-hours`: ask the Meta team. API and model questions go here.
  - `#resources`: docs, **credit forms**, session recordings.
  - `#intros`: say what you're building.
- **Credits** (request forms in `#resources`, opened at kickoff):
  - Meta Model API: $150 per participant. This is what Sous runs on.
  - Baseten: $100 plus 2M TPM, **first 2,000 participants**. Open weights (Muse Spark Open).
  - Modal: $100 for open weights and GPUs, **first 1,000 participants**.
  - Fireworks: $25, select participants.
- **Live sessions** (12:00 PM ET, recorded to `#resources`):
  - Tue Oct 27: Meta Engineering Workshop P1 (Suraj Subramanian)
  - Wed Oct 28: Meta Engineering Workshop P2 (Yash Khare)
  - Fri Oct 30: Fireworks AI Workshop (Sinan Ozdemir)
