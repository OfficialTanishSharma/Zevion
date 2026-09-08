# 🏗️ Design Document — Zevion

## Overview

Zevion is a **natural-language desktop copilot** with a three-tier architecture:

```
[ User ]  ←voice/text→  [ Frontend (React) ]  ←HTTP/JSON→  [ Backend (FastAPI) ]  →  [ OS / Desktop ]
```

The user speaks or types a command. The backend parses the intent, evaluates
safety, executes the action on the desktop, and returns a natural-language
response plus a structured record of what happened.

---

## Backend

### Request Flow (`main.py`)

```
POST /api/chat
  → brain.process_message()          # parse intent, build plan, safety level
  → for each action:
      → safety.evaluate_action()     # risk_level + requires_confirmation
      → if blocked  → skip + audit
      → if approval required → create approval token (modal shown to user)
      → else → controller.execute_action()
  → persist conversation
  → return { response, thoughts, actions, safety_level }
```

### Intent Parser (`ai_brain.py`)

The parser is a deterministic pipeline, not an LLM call (the LLM is only used as
a fallback for unrecognized intents when a provider is configured):

1. `_handle_conversational_response()` — small talk (greetings, math, time, identity)
2. `_parse_compound_command()` — multi-step commands ("open X and do Y")
3. `_parse_single_clause()` — a large regex if/elif chain (~30 sections) for
   single intents (open app, create file, search web, build game, …)
4. External AI provider (optional) — natural-language fallback

### Tool Layer (`desktop_controller.py`)

`DesktopController.execute_action(tool_name, parameters)` dispatches 30+ tools.
Every tool returns a structured record with `success`, `duration_ms`, and
physical verification where applicable.

Path resolution (`resolve_path()`) handles:
- Windows Desktop redirection (OneDrive, Registry, Win32 Shell API)
- Absolute paths, drive letters (`D:\...`), forward/back slashes
- Env vars (`%USERPROFILE%`), tilde (`~`)
- Desktop/Downloads/Documents/Workspace keywords

### Safety (`safety_guard.py`)

`SafetyGuard.evaluate_action()` returns `(risk_level, requires_confirmation, warning)`.
Risk levels: `blocked` > `dangerous` > `moderate` > `safe`.

---

## Frontend

- **React SPA** with state-based tab routing (no router).
- `App.jsx` holds conversation state and sends `/api/chat` requests.
- `ChatInterface.jsx` renders messages, thought timelines, action cards,
  and a workspace preview panel (Preview / Code / Activity).
- `toolIcons.jsx` is the single source of truth for SVG icons (no emojis).
- Theme: warm dark palette (amber/orange/rose), custom logo assets.

---

## Data Storage

All state is stored as JSON files in the user's home directory:

| File | Purpose |
|---|---|
| `~/.ai_desktop_settings.json` | Safety mode, active provider, onboarding |
| `~/.ai_desktop_conversations.json` | Conversation history |
| `~/.ai_desktop_memory.json` | Level 2 global memory |
| `~/.ai_desktop_usage.json` | Usage stats (requests/tokens per provider) |
| `~/.ai_desktop_reminders.json` | Timed reminders |
| `~/.ai_desktop_attachments/` | Uploaded attachment files + rate limits |

---

## Key Design Decisions

1. **Deterministic intent parsing first, LLM second** — desktop control must
   never depend on an LLM being available or reliable.
2. **Safety at every layer** — safety is not a single gate; it's re-checked in
   SafetyGuard, the API dispatch, and the controller.
3. **Physical verification** — file/folder/project tools return success only
   after confirming the result on the real filesystem.
4. **Offline-first games** — game templates are static HTML/CSS/JS so they work
   with zero API keys.
