# 🚀 Zevion — Your AI Desktop Copilot

<div align="center">

**Control your Windows PC with natural language — open apps, create files, build games, search the web, and automate workflows — safely.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![React](https://img.shields.io/badge/React-18-61dafb.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-315%20passing-brightgreen.svg)](backend/test_suite.py)

</div>

---

**Zevion** is a natural-language AI desktop assistant that executes real actions on your Windows computer — open apps, create files & folders on any drive, build playable games, search the web, take and analyze screenshots, run diagnostics, and automate multi-step workflows — all by just talking to it (type or voice).

Built with a **safety-first** design: destructive commands are hard-blocked, system paths are protected, and every risky action requires your explicit approval.

> Zevion understands **English** (and also Hindi / Hinglish). All examples below use English commands.

---

## ✨ Features

### 🗣️ Natural-Language Desktop Control
Just type (or speak) what you want:

| You say | Zevion does |
|---|---|
| `open chrome` | Launches Google Chrome |
| `open notepad` / `open discord` / `open vscode` | Launches any installed app (100+ fuzzy-matched) |
| `open a new chrome window` | Opens a **new window** instance |
| `minimize / maximize / close chrome` | Controls windows via Win32 |
| `type this in notepad` | Types text into apps |
| `press ctrl+c` / `press win+d` | Sends keyboard shortcuts |
| `click at 500,300` | Controls the mouse |

### 📁 Files & Folders (any drive, any folder)
| You say | Zevion does |
|---|---|
| `create a folder named TestAgent on Desktop` | Creates a folder on Desktop |
| `write Hello in hello.txt` | Writes content to a file |
| `create D:\projects\data.txt` | Creates a file on **any drive / absolute path** |
| `create a file on D drive` | Creates on a specific drive |
| `read this file` | Reads a file |
| `delete this file` | Sends to **Recycle Bin** (recoverable) |
| `organize my files` | Auto-sorts by category |
| `what's on my desktop` | Lists folder contents |
| `find the report file` | Searches files by name |
| `grep for TODO in downloads` | Searches **inside** file contents |
| `edit notes.txt replace hello with hi` | Find & replace (+ auto `.bak` backup) |
| `undo` | Restores the last edit |
| `note: buy milk` | Saves a timestamped note |

### 🎮 7 Built-in Games (no API key needed)
Zevion generates **complete, playable games** on your Desktop — with sound effects, score/high-score, and touch support:

| Game | Command |
|---|---|
| 🐍 Snake | `create a snake game` |
| ⭕ Tic-Tac-Toe | `create a tic tac toe game` |
| 🏓 Pong | `create a pong game` |
| 🐦 Flappy Bird | `create a flappy bird game` |
| 🔢 2048 | `create a 2048 game` |
| 🧱 Breakout | `create a breakout game` |
| 🃏 Memory Match | `create a memory game` |

### 📸 Screenshot & Vision
- `take a screenshot` — captures the screen
- `analyze my screen` — captures + **AI vision analysis** (needs a Gemini key)

### 🌐 Web & Internet
| You say | Zevion does |
|---|---|
| `search the web for X` | **Real web search** (title + URL + snippet) |
| `open youtube` / `play minecraft video` | YouTube open + playback |
| `fetch https://example.com` | Extracts page content |
| `download https://.../file.zip` | Downloads to Downloads folder |

### 📋 Clipboard, Media & System
- `copy hello to clipboard` / `paste` — clipboard control
- `pause music` / `next song` / `volume up` / `mute` — media control
- `battery status` — battery status
- `diagnose my pc` — CPU/RAM/Disk diagnostics
- `remind me in 10 minutes to call mom` — timed reminders

### 🧠 Smart Assistant (built-in)
Even without an API key, Zevion answers:
- `what can you do` → feature list
- `calculate 5 * 7` → **35** (math)
- `what time is it` → current time
- `who are you` → intro
- `hello` → casual chat

Connect **Gemini, Claude, ChatGPT, NVIDIA, Kimi, DeepSeek, or Qwen** in Settings for full intelligent responses.

---

## 🛡️ Safety-First Architecture (5 layers)

Zevion is designed so it can **never** destroy your system:

1. **HARD-BLOCK list** — `rm -rf`, `format`, `diskpart`, `bcdedit`, `taskkill /f`, `del /s`… **never run**, not even with manual approval. Re-checked at 3 code layers.
2. **System Path Protection** — write/delete into `C:\Windows`, `Program Files`, `/etc`, `/usr`, `/bin`… is auto-blocked (user folders like `~/bin` are still safe).
3. **Chained Command Detection** — `&&`, `;`, `|` combos always require confirmation (a dangerous command can hide behind a safe one).
4. **Delete → Recycle Bin** — files go to the Recycle Bin (recoverable) by default, never hard-deleted.
5. **Tiered Risk Classification** — Safe (auto), Moderate (mode-dependent), Dangerous (mandatory modal).

Plus:
- **Dry-Run Mode** — "show but don't run"
- **Plan-Then-Do Mode** — multi-step commands show a plan and wait for approval
- **3 Safety Modes** — Strict / Balanced / Developer
- **API Key Redaction** — keys are never logged, printed, or returned (always masked as `sk-a••••••••2345`)

---

## 🏗️ Tech Stack & Architecture

```
ai-desktop-agent/
├── backend/                    # FastAPI (Python)
│   ├── main.py                 # API routes + action dispatch + safety gating
│   ├── ai_brain.py             # NL intent parser, AI providers, memory, games
│   ├── desktop_controller.py   # Cross-platform desktop automation (30+ tools)
│   ├── safety_guard.py         # 5-layer safety engine + audit log
│   └── test_suite.py           # 315 isolated tests
├── frontend/                   # React + Vite + Tailwind
│   ├── src/App.jsx
│   ├── src/components/         # Chat, Sidebar, Settings, Usage dashboard…
│   └── public/assets/          # Logo & icons
├── native-windows/             # Windows native launcher & desktop app
│   ├── launcher.pyw            # GUI launcher (no terminal, native window)
│   ├── start_zevion.vbs        # Silent one-click launcher
│   ├── run_agent.py            # Terminal/CLI runner
│   └── windows_setup.bat       # One-click setup
├── requirements.txt
└── .gitignore
```

| Layer | Tech |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Frontend | React 18, Vite, Tailwind CSS v4, lucide-react |
| Desktop automation | pyautogui, psutil, send2trash, Win32 (ctypes/pywin32) |
| AI providers | Gemini, Claude, ChatGPT, NVIDIA (Kimi/DeepSeek/Qwen), Built-in |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- (Windows only) `pywin32` for full native window control

### Option A: One-click Native Desktop App (Windows)
**Double-click `native-windows\start_zevion.vbs`** (or `windows_setup.bat`) — a clean **graphical launcher** opens (no terminal). It will:
1. Verify Python & Node.js are installed
2. Install dependencies (first run only)
3. Launch Zevion in a **native desktop window** (no browser tab)

> ⚠️ **Windows SmartScreen note:** Because this is an unsigned open-source script,
> Windows may show an "Unknown Publisher" warning on first run. This is normal for
> any unsigned project. Click **"More info" → "Run anyway"** to proceed. The code is
> fully open source — you can inspect every line before running it.

### Option B: Manual Setup (developers)
```bash
# Terminal 1 — backend
cd backend
pip install -r requirements.txt
python -m uvicorn main:app --host 0.0.0.0 --port 8000

# Terminal 2 — frontend
cd frontend
npm install --legacy-peer-deps
npm run dev
```

Open **http://localhost:5173** and start talking to Zevion.

### (Optional) Terminal / CLI version
```bash
cd native-windows
python run_agent.py
```

### (Optional) Connect an AI provider
1. Open **Settings → AI Providers**
2. Add your Gemini / Claude / ChatGPT / NVIDIA API key
3. Select it as the active provider — now Zevion gives full intelligent responses.

> 🔒 **Security:** API keys are stored locally and **never** logged, printed, or committed. `.gitignore` already excludes all credential files.

---

## 🧪 Testing

```bash
cd backend
python test_suite.py
```

**315 isolated tests** covering:
- Intent parsing (English + Hindi/Hinglish)
- Action dispatch + real filesystem verification
- Safety hardening (hard-block, system paths, chained commands)
- Games, web tools, clipboard, reminders, usage tracking
- All tests use isolated temp storage — they never pollute your real Desktop.

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. **Fork** the repository
2. Create a branch: `git checkout -b feature/my-feature`
3. Make your changes
4. Run tests: `cd backend && python test_suite.py`
5. Commit & push, then open a **Pull Request**

**Guidelines:**
- Keep safety intact — never weaken the hard-block list or path protection
- Don't log or expose API keys (always mask/redact)
- Run the test suite before submitting

---

## 🐛 Reporting Issues

Found a bug? Please open an issue with:
- A clear description
- Steps to reproduce
- Expected vs actual behavior
- Your OS (Windows 10/11) and Python version

For **security vulnerabilities**, see [SECURITY.md](SECURITY.md) — do not open a public issue.

---

## 📄 License

MIT — free to use, modify, and share. See [LICENSE](LICENSE).

---

## 🙏 Credits

Zevion — built with ❤️ to make desktop automation safe and natural.
