"""
Zevion — GUI Launcher (no terminal window)

Double-click start_zevion.vbs to open a clean graphical window that checks
requirements, installs dependencies, and launches Zevion in a native desktop
window. No scary terminal.

Architecture:
- A background worker thread does the slow work (checks + installs + servers).
- The webview native window is opened on the MAIN thread (pywebview requirement).
"""

import os
import sys
import time
import queue
import threading
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"
FRONTEND_DIR = BASE_DIR / "frontend"

APP_URL = "http://localhost:5173"
BACKEND_URL = "http://127.0.0.1:8000"

LOG_QUEUE = queue.Queue()
READY_EVENT = threading.Event()

# Track spawned server processes so we can kill them on app close
SERVER_PROCESSES = []  # list of subprocess.Popen
SERVER_LOCK = threading.Lock()


def log(msg):
    LOG_QUEUE.put(msg)


def _kill_servers():
    """Terminate all Zevion server processes (backend + frontend)."""
    with SERVER_LOCK:
        procs = list(SERVER_PROCESSES)
    for p in procs:
        try:
            p.terminate()
        except Exception:
            pass
    # Give them a moment, then force kill if still alive
    time.sleep(0.6)
    for p in procs:
        try:
            if p.poll() is None:
                p.kill()
        except Exception:
            pass
    with SERVER_LOCK:
        SERVER_PROCESSES.clear()


def _python_ok():
    try:
        r = subprocess.run([sys.executable, "--version"], capture_output=True, text=True, check=False)
        return r.returncode == 0
    except Exception:
        return False


def _node_ok():
    npm = "npm.cmd" if os.name == "nt" else "npm"
    try:
        r = subprocess.run([npm, "--version"], capture_output=True, text=True, check=False)
        return r.returncode == 0
    except Exception:
        return False


def _wait_for_url(url, timeout=30.0):
    import urllib.request
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1.0)
            return True
        except Exception:
            time.sleep(0.5)
    return False


def _run_hidden(args, cwd):
    """Run a command with NO console window popping up on Windows."""
    kwargs = dict(cwd=str(cwd))
    if os.name == "nt":
        # CREATE_NO_WINDOW = 0x08000000 prevents a console flash
        CREATE_NO_WINDOW = 0x08000000
        kwargs["creationflags"] = CREATE_NO_WINDOW
    kwargs["stdout"] = subprocess.DEVNULL
    kwargs["stderr"] = subprocess.DEVNULL
    kwargs["stdin"] = subprocess.DEVNULL
    return subprocess.run(args, **kwargs, check=False)


def _backend_deps_ok():
    """True if backend deps are already installed (skip pip install)."""
    try:
        import uvicorn  # noqa: F401
        import fastapi  # noqa: F401
        return True
    except ImportError:
        return False


def _frontend_deps_ok():
    """True if node_modules already exists (skip npm install)."""
    return (FRONTEND_DIR / "node_modules").is_dir()


def worker():
    """Background: checks, installs dependencies, starts servers, waits."""
    try:
        log("Preparing Zevion...")

        if not _python_ok():
            log("Python is missing.")
            log("Install Python 3.10+ from python.org")
            return

        if not _node_ok():
            log("Node.js is missing.")
            log("Install Node.js 18+ from nodejs.org")
            return

        # Only install on first run (skip if already present) — this makes
        # subsequent launches much faster.
        if _backend_deps_ok():
            log("Components ready")
        else:
            log("Installing components (first launch, ~1 minute)...")
            _run_hidden(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "pywebview"],
                BACKEND_DIR
            )

        npm = "npm.cmd" if os.name == "nt" else "npm"
        if _frontend_deps_ok():
            log("Components ready")
        else:
            log("Finishing setup (first launch)...")
            _run_hidden([npm, "install", "--legacy-peer-deps"], FRONTEND_DIR)

        log("Starting Zevion...")
        backend_proc = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "8000"],
            cwd=str(BACKEND_DIR),
            creationflags=(0x08000000 if os.name == "nt" else 0),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
        )
        with SERVER_LOCK:
            SERVER_PROCESSES.append(backend_proc)

        frontend_proc = subprocess.Popen(
            [npm, "run", "dev"], cwd=str(FRONTEND_DIR),
            creationflags=(0x08000000 if os.name == "nt" else 0),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
        )
        with SERVER_LOCK:
            SERVER_PROCESSES.append(frontend_proc)

        log("Almost there...")
        _wait_for_url(BACKEND_URL, timeout=30)
        _wait_for_url(APP_URL, timeout=45)

        log("Opening Zevion...")
        READY_EVENT.set()
    except Exception as e:
        log("Something went wrong:")
        log(str(e))


def open_app_window(root_ref=None):
    """Opens the Zevion app — native window if pywebview is available,
    otherwise falls back to the default browser. MUST run on the main thread.
    After the window closes, kills the server processes.

    The launcher GUI (if passed) is closed FIRST so it doesn't sit in the
    taskbar showing "not responding" while webview runs.
    """
    # Close the launcher GUI before starting webview (its job is done).
    if root_ref is not None:
        try:
            root_ref.destroy()
        except Exception:
            pass

    try:
        import webview
    except ImportError:
        import webbrowser
        webbrowser.open(APP_URL)
        log("Opened in browser (install pywebview for a native window).")
        return

    webview.create_window(
        title="Zevion — AI Desktop Copilot",
        url=APP_URL, width=1280, height=820, min_size=(900, 600),
        confirm_close=True
    )
    webview.start()

    # When the Zevion window is closed, stop the servers so no leftover
    # processes remain in Task Manager.
    _kill_servers()


def build_gui():
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("Zevion — AI Desktop Copilot")
    root.geometry("520x480")
    root.resizable(False, False)
    root.configure(bg="#141110")

    # Force window to appear on top / focused (not hidden in taskbar)
    root.lift()
    root.attributes("-topmost", True)
    root.after(400, lambda: root.attributes("-topmost", False))
    root.focus_force()

    # Logo + window icon
    logo_path = BASE_DIR / "frontend" / "public" / "assets" / "logo.png"
    logo = None
    try:
        from PIL import Image, ImageTk
        img = Image.open(logo_path)
        icon_img = img.resize((72, 72))
        logo = ImageTk.PhotoImage(icon_img)
        # Set the taskbar/window icon so it shows the Zevion logo, not the
        # default "feather" Python icon.
        icon = ImageTk.PhotoImage(img.resize((64, 64)))
        root.iconphoto(True, icon)
    except Exception:
        logo = None

    header = tk.Frame(root, bg="#141110")
    header.pack(pady=(28, 8))
    if logo:
        tk.Label(header, image=logo, bg="#141110").pack()
    else:
        tk.Label(header, text="🤖", font=("Segoe UI", 40), bg="#141110").pack()

    tk.Label(header, text="Zevion", font=("Segoe UI", 24, "bold"),
             fg="#f59e0b", bg="#141110").pack()
    tk.Label(header, text="AI Desktop Copilot", font=("Segoe UI", 11),
             fg="#a8a29e", bg="#141110").pack()

    status = tk.Text(root, height=8, width=60, bg="#1f1a17", fg="#e7e5e4",
                     font=("Consolas", 9), relief="flat", bd=10, wrap="word", state="disabled")
    status.pack(padx=25, pady=12, fill="both", expand=True)

    progress = ttk.Progressbar(root, mode="indeterminate", length=420)
    progress.pack(pady=(0, 10))

    launch_btn = tk.Button(
        root, text="Launch Zevion", font=("Segoe UI", 12, "bold"),
        bg="#f59e0b", fg="#141110", activebackground="#fb923c",
        activeforeground="#141110", relief="flat", cursor="hand2",
        padx=30, pady=8, bd=0
    )
    launch_btn.pack(pady=(0, 10))

    # Reassurance footer — makes the user feel safe.
    footer = tk.Label(
        root,
        text="Runs 100% on your PC — no data leaves your computer.",
        font=("Segoe UI", 8), fg="#57534e", bg="#141110"
    )
    footer.pack(pady=(0, 14))

    def append_log(text):
        status.configure(state="normal")
        status.insert("end", "• " + text + "\n")
        status.see("end")
        status.configure(state="disabled")

    def poll_queue():
        try:
            while True:
                msg = LOG_QUEUE.get_nowait()
                append_log(msg)
                if msg.startswith("Something went wrong") or msg.startswith("Python is missing") or msg.startswith("Node.js is missing"):
                    progress.stop()
                    launch_btn.configure(text="Retry", state="normal")
        except queue.Empty:
            pass
        # When setup is ready, open the app window on the main thread
        if READY_EVENT.is_set():
            READY_EVENT.clear()
            progress.stop()
            launch_btn.configure(text="Zevion is running ✓", state="disabled")
            # Pass root so the launcher closes itself before webview runs,
            # avoiding a "not responding" ghost window in the taskbar.
            root.after(300, lambda: open_app_window(root))
        root.after(150, poll_queue)

    def on_launch():
        launch_btn.configure(text="Launching...", state="disabled")
        progress.start(12)
        threading.Thread(target=worker, daemon=True).start()

    def on_close():
        """When the launcher GUI is closed, stop any running servers."""
        _kill_servers()
        root.destroy()

    launch_btn.configure(command=on_launch)
    root.protocol("WM_DELETE_WINDOW", on_close)
    root.after(150, poll_queue)
    root.mainloop()

    # Safety net: if mainloop exits, ensure servers are stopped.
    _kill_servers()


if __name__ == "__main__":
    build_gui()
