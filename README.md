# muse-hackathon

Workbench for the Meta Global AI Developer Hackathon (Oct 26 to Nov 4, 2026;
submissions close **Nov 4, 9 PM ET**). The idea is in [IDEA.md](IDEA.md).

## Setup

```bash
cd ~/Developer/muse-hackathon
# 1. put your key in .env (dev.meta.ai/platform -> API keys)
# 2. check every model:
.venv/bin/python scripts/smoke.py            # text image vision sam video asr
.venv/bin/python scripts/smoke.py sam        # one at a time
```

Before the first call: claim the $150 credit form, add a card on the Billing page,
and set a spend limit there.

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

## Layout

```
muse/client.py     ask, ask_video, generate_image, segment, transcribe
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
