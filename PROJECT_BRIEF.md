# Zevion — Complete Project Brief (for GitHub Copilot / AI)

You are helping with **Zevion**, an AI desktop copilot application. Use this brief to understand the entire project. Do not remove, rewrite, or break existing functionality.

---

## 1. What is Zevion?

Zevion is a **natural-language AI desktop assistant**. The user talks to it (typing or voice) in English, Hindi, or Hinglish, and Zevion controls the computer:

- Opens/closes/minimizes applications
- Creates files & folders (on Desktop, Downloads, Documents, Workspace, or **any drive/absolute path** like `D:\projects\file.txt`)
- Builds complete playable games
- Searches the web, fetches pages, downloads files
- Takes and analyzes screenshots (AI vision)
- Runs PC diagnostics, battery checks, media controls, clipboard, keyboard shortcuts, reminders

It has a **safety-first** architecture — destructive commands are hard-blocked, system paths are protected, and risky actions require user approval.

---

## 2. Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.9+, FastAPI, Uvicorn, Pydantic |
| Frontend | React 18, Vite, Tailwind CSS v4, lucide-react (SVG icons), react-markdown, remark-gfm |
| Desktop automation | pyautogui, psutil, send2trash, Pillow, Win32 API (ctypes/pywin32, Windows-only) |
| AI providers | Gemini, Claude, ChatGPT, NVIDIA (Kimi/DeepSeek/Qwen), plus a Built-in (offline) engine |
| Storage | JSON files in the user home directory (settings, memory, conversations, usage, reminders) |

---

## 3. Project Structure

```
ai-desktop-agent/
├── backend/                    # FastAPI (Python)
│   ├── main.py                 # API routes + action dispatch + safety gating
│   ├── ai_brain.py             # NL intent parser, AI providers, memory, game templates (~5600 lines)
│   ├── desktop_controller.py   # Cross-platform desktop automation, 30+ tools (~4600 lines)
│   ├── safety_guard.py         # 5-layer safety engine + audit log (~290 lines)
│   ├── test_suite.py           # 315 isolated unit tests (~4100 lines)
│   └── requirements.txt        # Python dependencies
├── frontend/                   # React + Vite + Tailwind
│   ├── src/App.jsx             # Main app, tab routing, chat state
│   ├── src/components/         # ChatInterface, Sidebar, SettingsModal, UsageDashboard,
│   │                           # AuditLogViewer, FileOrganizerStudio, WorkflowBuilder,
│   │                           # InstalledAppsDrawer, OnboardingModal, SafetyConfirmationModal,
│   │                           # toolIcons.jsx (central SVG icon map)
│   ├── src/utils/voiceAssistant.js  # Web Speech API (STT + TTS)
│   └── public/assets/          # logo.png, favicon.png, assistant-avatar.png
├── native-windows/             # Windows native launcher
│   ├── run_agent.py
│   └── windows_setup.bat
├── README.md                   # Full documentation
└── .gitignore                  # Excludes secrets & caches
```

---

## 4. Backend Architecture

### 4.1 `main.py` — API Layer
- `POST /api/chat` — main endpoint. Parses intent, evaluates safety, executes actions, returns response + thoughts + actions.
- `GET/POST /api/conversations` — conversation persistence (create, list, get, rename, delete)
- `GET/POST /api/settings` — safety mode, active provider, dry-run, plan-mode
- `GET /api/providers` — AI provider list
- `GET /api/usage` — usage stats (today, last 7 days, per-provider)
- `GET /api/logs` — audit log
- `POST /api/action/confirm` — approve/reject dangerous action
- `POST /api/action/execute` — direct tool execution (for UI buttons/workflows)
- `POST /api/plan/approve` — Plan-Then-Do approval
- `GET /api/export/conversation/{id}` — export chat as Markdown
- `GET /api/export/audit` — export audit log as Markdown
- Attachment endpoints (`/api/attachments/*`)

### 4.2 `ai_brain.py` — Intent Parser & AI
- `AIBrain` class — the core. Has `process_message()` as main entry.
- `_parse_intent_and_plan()` → `_parse_compound_command()` → `_parse_single_clause()`
- `_parse_single_clause()` is a large if/elif chain (~30+ numbered sections) that detects intents:
  - Web search, web fetch, download
  - Game creation (7 game types)
  - Folder/file creation (including absolute/drive paths)
  - App launch, window management, type text, mouse, screenshot
  - Clipboard, media, keyboard, battery, list directory, grep, edit, undo, reminders
- `_handle_conversational_response()` — built-in chat (greetings, capabilities, math, time, identity)
- AI providers: `BaseAIProvider`, `GeminiProvider`, `ClaudeProvider`, `ChatGPTProvider`, `NVIDIAProvider`, `DirectNamedProvider`, `DeterministicFallback`
- `get_game_template(game_type, language)` — returns dict of files for each game
- Memory: `MemoryManager` (Level 2 global memory) + conversation context (Level 1)

### 4.3 `desktop_controller.py` — Desktop Automation
- `DesktopController` class — the tool executor.
- `execute_action(tool_name, parameters)` — dispatches 30+ tools.
- **Path resolution**: `get_desktop_path()`, `get_documents_path()`, `get_downloads_path()`, `resolve_path()` (handles Windows registry, OneDrive redirection, backslashes, env vars, tilde, absolute paths)
- Tools include: `open_application`, `open_website`, `create_folder`, `create_file`, `write_file`, `read_file`, `delete_file` (→ Recycle Bin), `create_project`, `organize_files`, `type_text`, `control_mouse`, `take_screenshot`, `analyze_screenshot`, `execute_command`, `get_system_info`, `clipboard_set/get`, `find_files`, `grep_files`, `edit_file`, `undo_edit`, `download_file`, `media_control`, `press_keys`, `get_battery`, `add_note`, `list_directory`, `set_reminder`, window management (minimize/maximize/restore/close)
- Windows app discovery: Start Menu `.lnk` parsing, Registry App Paths, System32, URI schemes, fuzzy matching

### 4.4 `safety_guard.py` — Safety Engine
- `SafetyGuard` class with `evaluate_action(tool_name, parameters)` → returns `(risk_level, requires_confirmation, warning_message)`
- Risk levels: `blocked`, `safe`, `moderate`, `dangerous`
- `HARD_BLOCKED_PATTERNS` — commands that NEVER run (rm -rf, format, diskpart, bcdedit, taskkill /f, etc.)
- `DESTRUCTIVE_COMMAND_PATTERNS` — approvable dangerous commands
- `is_protected_path()` — system path protection (C:\Windows, Program Files, /etc, /usr, /bin — only at path start, so user's ~/bin is safe)
- `has_chained_operators()` — detects &&, ;, |, ||
- `sanitize_safe_payload()` — redacts API keys/tokens from all logs
- Modes: strict, balanced, developer + `dry_run` and `plan_mode` flags

---

## 5. Frontend Architecture

- **React SPA** with tab-based navigation (no router, uses state)
- **App.jsx** — holds conversation state, active tab, settings, handles `/api/chat` sending, confirmation modal
- **ChatInterface.jsx** — the main chat: message list, markdown rendering, thought timeline, action cards (expandable), workspace preview panel (Preview/Code/Activity tabs), attachment upload with rate limits, voice input, stop generation
- **Sidebar.jsx** — brand/logo, new chat, recent chats (rename/delete/export), navigation tabs, quick prompts, system status (CPU/RAM)
- **SettingsModal.jsx** — provider management (API keys), safety mode selector, dry-run + plan-mode toggles, memory management
- **toolIcons.jsx** — central SVG icon map for all tool types (no emojis)
- **Theme**: warm dark palette (amber/orange/rose accents), custom logo, premium modern design

---

## 6. Key Features Summary

### Files & Folders
Create/read/delete/list/search files & folders on any drive or path. Delete goes to Recycle Bin. Edit has auto `.bak` backup + undo.

### 7 Games (offline, no API key)
Snake, Tic-Tac-Toe, Pong, Flappy Bird, 2048, Breakout, Memory Match. Each with sound, score, high-score, touch support.

### Web
Real web search (DuckDuckGo), page fetch, file download.

### Automation
App launch, window management, mouse control, keyboard shortcuts, type text, clipboard, media controls, screenshots, screen vision analysis.

### System
PC diagnostics, battery status, reminders, notes.

### Smart Assistant (built-in)
Greetings, capabilities list, math calculation, time, identity, casual chat in English/Hinglish.

### AI Providers
Gemini, Claude, ChatGPT, NVIDIA, Kimi, DeepSeek, Qwen, Built-in. API keys verified, never logged (masked).

### Safety (5 layers)
Hard-block, system path protection, chained command detection, recycle bin delete, tiered risk + dry-run + plan-mode.

### Extras
Usage dashboard, export chat/audit as Markdown, RAM/CPU widget, Level 1 + Level 2 memory, attachments (image/PDF/video/code, 5 files/25MB each), voice input/output, conversation persistence.

---

## 7. Important Constraints (do NOT break these)

1. **Backend must not be rewritten from scratch** — modify in place only.
2. **Safety must stay intact** — hard-block list, system path protection, chained command detection, recycle bin delete, API key redaction.
3. **315 tests must pass** — run `python test_suite.py` from `backend/`. Tests use isolated temp storage (`IsolatedBrainTestCase`).
4. **No API key leaks** — never print/log/return keys; mask as `sk-a••••••••2345`.
5. **Conversational safety** — casual mentions of apps/screenshots must produce 0 actions. Imperatives should still execute.
6. **Frontend preview runs in a sandboxed iframe** (`allow-scripts`, no network) — use inline styles, embedded SVG, data URIs; no external CDN/fonts inside iframes.
7. **No emojis in UI** — use lucide-react SVG icons (see `toolIcons.jsx`).
8. **Windows-first** — desktop automation targets Windows 11/10, with graceful cross-platform fallback.

---

## 8. How to Run

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm install --legacy-peer-deps
npm run dev
# open http://localhost:5173

# Tests
cd backend
python test_suite.py
```

---

## 9. Tech Notes for Copilot

- `DesktopController.resolve_path()` already handles absolute paths, Windows drive letters, backslashes, env vars, tilde, and Desktop/Downloads/Documents/Workspace keywords.
- Intent parser is a large regex-based if/elif chain in `_parse_single_clause()` — add new intents as new numbered sections before the `return None` fallback.
- New tools need 4 things: (1) method in `DesktopController`, (2) dispatch in `execute_action()`, (3) safety classification in `SafetyGuard.evaluate_action()`, (4) intent detection in `_parse_single_clause()`.
- Safety evaluation happens in `main.py` before every action execution.
- Game templates are returned by `get_game_template()` as `{filename: content}` dicts, then written by `create_project()` with physical verification.
