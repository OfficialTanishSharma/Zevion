# 🤖 Model Card — Zevion

## Summary

Zevion is **not a single model** — it is an application that can route to
multiple AI providers for natural-language understanding, with a deterministic
built-in engine as the default.

## AI Providers

| Provider | Type | Requires Key | Notes |
|---|---|---|---|
| **Built-in** | Deterministic rule engine | No | Default. Offline, handles all desktop automation + small talk |
| **Gemini** | Google LLM | Yes | Includes vision (screenshot analysis) |
| **Claude** | Anthropic LLM | Yes | |
| **ChatGPT** | OpenAI LLM | Yes | |
| **NVIDIA** | NVIDIA-hosted | Yes | Hosts Kimi, DeepSeek, Qwen |

## How the model is used

1. **Intent parsing**: primarily deterministic (regex/rules). The LLM is used
   only as a fallback for unrecognized commands.
2. **Conversational responses**: small talk and general questions go to the
   active LLM provider (or the built-in engine if no key is configured).
3. **Vision**: screenshot analysis uses Gemini's vision capability when a key
   is present.

## Capabilities & Limitations

### ✅ What it does well
- Desktop automation (apps, files, games, web, clipboard, media, diagnostics)
- Multi-language input (English, Hindi, Hinglish)
- Offline operation (built-in engine, no key needed)

### ⚠️ Limitations
- Without an API key, general-knowledge answers are limited (falls back to a
  helpful message pointing to Settings).
- Vision analysis requires a Gemini API key.
- Desktop automation is Windows-first; other platforms have graceful fallback.

## Safety & Ethics

- Destructive commands are hard-blocked.
- System paths are protected.
- API keys are never logged or exposed.
- See `SECURITY.md` for the full safety model.

## Training Data / Provenance

This application ships **no bundled model weights** and performs no training.
It uses third-party hosted models via their public APIs. No user data is used
for training by Zevion itself.
