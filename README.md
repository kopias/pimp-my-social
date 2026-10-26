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
- So the **live loop segments one frame at a time** every few seconds; video mode
  is for replays and calibration.
- Browning Index on the AI cook-through clip climbs 22 → 263 (piece 0) and
  26 → 292 (piece 1), steadily, with SAM confidence ≥ 0.95 throughout. The
  thresholds still need real footage.

## Layout

```
muse/client.py     ask, ask_video, generate_image, segment, transcribe
muse/browning.py   Browning Index inside SAM masks, lighting reference, per-piece readings
scripts/browning.py      clip or photo -> out/<name>/{readings.json,curves.png,overlay.png}
muse/judge.py      Spark judge: step -> watch spec, readings + frame -> verdict; hard safety rules
scripts/judge.py   replay a measured clip through the judge, checkpoint by checkpoint
scripts/make_test_clip.py  AI cook-through clip (Muse Image edits) for testing without a stove
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
