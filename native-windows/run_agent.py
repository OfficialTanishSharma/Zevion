"""
Native Windows AI Agent Automation Runner
Can be run on any Windows 10/11 machine to control applications,
mouse, keyboard, files, and browsers with local Windows APIs.
"""

import os
import sys
import time
import subprocess
import platform
import json
import urllib.parse
from pathlib import Path

# Safe imports for Windows automation
try:
    import winreg
    HAS_WINREG = True
except ImportError:
    winreg = None
    HAS_WINREG = False

try:
    import win32gui
    import win32con
    import win32process
    import win32api
    HAS_PYWIN32 = True
except ImportError:
    win32gui = None
    win32con = None
    win32process = None
    win32api = None
    HAS_PYWIN32 = False

try:
    import pyautogui
    pyautogui.PAUSE = 0.05
    HAS_PYAUTOGUI = True
except ImportError:
    pyautogui = None
    HAS_PYAUTOGUI = False

if sys.platform == "win32" or platform.system().lower() == "windows":
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    HAS_WIN_CTYPES = True
else:
    user32 = None
    kernel32 = None
    HAS_WIN_CTYPES = False


class WindowsDesktopAgent:
    def __init__(self, workspace_path: str = None):
        if workspace_path:
            self.workspace = Path(workspace_path)
        else:
            desktop_dir = Path.home() / "Desktop" / "Zevion_Workspace"
            if desktop_dir.parent.exists():
                self.workspace = desktop_dir
            else:
                self.workspace = Path.home() / "ai-desktop-workspace"

        self.workspace.mkdir(parents=True, exist_ok=True)
        print(f"[Windows AI Agent] Workspace initialized at: {self.workspace}")

    def detect_windows_apps(self):
        """Scans Windows Registry for registered application paths."""
        apps = {}
        if not HAS_WINREG:
            print("[Warning] winreg not available on non-Windows host.")
            return apps

        reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                count = winreg.QueryInfoKey(key)[0]
                for i in range(count):
                    try:
                        app_name = winreg.EnumKey(key, i)
                        with winreg.OpenKey(key, app_name) as sub_key:
                            exe_path, _ = winreg.QueryValue(sub_key, None)
                            if exe_path and os.path.exists(exe_path):
                                slug = app_name.lower().replace(".exe", "")
                                apps[slug] = exe_path
                    except Exception:
                        continue
        except Exception as e:
            print(f"[Registry Scan Error] {e}")

        return apps

    def find_discord_executable(self) -> str:
        r"""
        Dynamically finds Discord.exe in C:\Users\%USERNAME%\AppData\Local\Discord\app-*\Discord.exe
        without hardcoding specific version numbers, preferring Discord.exe directly over Update.exe.
        """
        search_patterns = [
            os.path.expandvars(r"%LOCALAPPDATA%\Discord\app-*\Discord.exe"),
            r"C:\Users\*\AppData\Local\Discord\app-*\Discord.exe",
            os.path.expandvars(r"%APPDATA%\..\Local\Discord\app-*\Discord.exe"),
            os.path.expandvars(r"%USERPROFILE%\AppData\Local\Discord\app-*\Discord.exe")
        ]

        found_exes = []
        for pat in search_patterns:
            try:
                import glob
                matches = glob.glob(pat)
                if matches:
                    matches.sort(reverse=True)
                    for m in matches:
                        if os.path.exists(m) and m.lower().endswith("discord.exe") and "update.exe" not in m.lower():
                            found_exes.append(m)
            except Exception:
                continue

        if found_exes:
            return found_exes[0]

        return "discord.exe"

    def launch_app(self, app_name: str, new_window: bool = False):
        """Launches an application without manual user intervention."""
        print(f"[AI Agent] Searching for application '{app_name}' (new_window={new_window})...")
        low = app_name.lower().strip()

        # Handle Discord specifically
        if "discord" in low or "discrod" in low or "disocrd" in low:
            discord_exe = self.find_discord_executable()
            try:
                subprocess.Popen(f'start "" "{discord_exe}"', shell=True)
                print(f"[AI Agent] Successfully launched Discord via: {discord_exe}")
                return True
            except Exception as e:
                print(f"[AI Agent Discord Error] {e}")

        # PowerShell
        if "powershell" in low or "pwsh" in low:
            ps_candidates = [
                r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe",
                r"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe",
                r"C:\Program Files\PowerShell\7\pwsh.exe",
                "powershell.exe"
            ]
            for p in ps_candidates:
                exp = os.path.expandvars(p)
                if os.path.exists(exp):
                    subprocess.Popen(f'start "" "{exp}"', shell=True)
                    return True
            subprocess.Popen('start powershell.exe', shell=True)
            return True

        # Paint
        if "paint" in low or "mspaint" in low:
            paint_candidates = [
                r"%LOCALAPPDATA%\Microsoft\WindowsApps\mspaint.exe",
                r"C:\Windows\System32\mspaint.exe",
                "mspaint.exe"
            ]
            for p in paint_candidates:
                exp = os.path.expandvars(p)
                if os.path.exists(exp):
                    subprocess.Popen(f'start "" "{exp}"', shell=True)
                    return True
            try:
                subprocess.Popen('start ms-paint:', shell=True)
            except Exception:
                subprocess.Popen('start mspaint.exe', shell=True)
            return True

        # Command Prompt
        if low in ["cmd", "command prompt", "commandprompt"]:
            cmd_exe = os.path.expandvars(r"%SystemRoot%\System32\cmd.exe")
            if os.path.exists(cmd_exe):
                subprocess.Popen(f'start "" "{cmd_exe}"', shell=True)
            else:
                subprocess.Popen('start cmd.exe', shell=True)
            return True

        # Chrome
        if "chrome" in low:
            flag = " --new-window" if new_window else ""
            subprocess.Popen(f'start chrome{flag}', shell=True)
            return True

        # File Explorer
        if "explorer" in low:
            if new_window:
                subprocess.Popen('start explorer.exe /separate', shell=True)
            else:
                subprocess.Popen('start explorer.exe', shell=True)
            return True

        shortcuts = {
            "notepad": ["notepad.exe"],
            "code": ["code.cmd", "code.exe"],
            "calc": ["calc.exe"],
            "calculator": ["calc.exe"],
            "terminal": ["wt.exe", "powershell.exe", "cmd.exe"],
            "spotify": [r"%APPDATA%\Spotify\Spotify.exe", "spotify.exe"],
            "word": ["winword.exe"],
            "excel": ["excel.exe"]
        }

        candidates = shortcuts.get(low, [f"{app_name}.exe"])
        launched = False

        for candidate in candidates:
            try:
                expanded = os.path.expandvars(candidate)
                subprocess.Popen(f'start "" "{expanded}"', shell=True)
                print(f"[AI Agent] Successfully launched: {candidate}")
                launched = True
                break
            except Exception as e:
                continue

        if not launched:
            try:
                subprocess.Popen(f'start {app_name}', shell=True)
                print(f"[AI Agent] Executed start for: {app_name}")
                launched = True
            except Exception as e:
                print(f"[AI Agent Launch Error] {e}")

        return launched

    def find_and_focus_window(self, target_app: str = "notepad", timeout: float = 3.0):
        """Finds target window, restores if minimized, brings to foreground, and focuses text area dynamically."""
        if not HAS_WIN_CTYPES and not HAS_PYWIN32:
            return None

        norm_app = target_app.lower().strip()
        app_aliases = [norm_app]
        if norm_app in ["notepad", "notes", "editor"]:
            app_aliases.extend(["notepad", "untitled - notepad", "notes.txt"])
        elif norm_app in ["cmd", "command prompt"]:
            app_aliases.extend(["command prompt", "cmd", "cmd.exe"])
        elif norm_app in ["powershell", "pwsh"]:
            app_aliases.extend(["powershell", "windows powershell"])

        start_wait = time.time()
        while (time.time() - start_wait) <= timeout:
            found_windows = []
            if HAS_WIN_CTYPES:
                WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

                def ctypes_enum_proc(hwnd, lparam):
                    if user32.IsWindowVisible(hwnd):
                        length = user32.GetWindowTextLengthW(hwnd)
                        if length > 0:
                            buff = ctypes.create_unicode_buffer(length + 1)
                            user32.GetWindowTextW(hwnd, buff, length + 1)
                            title = buff.value
                            found_windows.append((hwnd, title))
                    return True

                proc_cb = WNDENUMPROC(ctypes_enum_proc)
                user32.EnumWindows(proc_cb, 0)

            for hwnd, title in found_windows:
                if any(alias in title.lower() for alias in app_aliases):
                    # Restore if minimized
                    if HAS_WIN_CTYPES and user32.IsIconic(hwnd):
                        user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                        time.sleep(0.1)

                    # Foregrounding with thread input attachment
                    if HAS_WIN_CTYPES:
                        fg_hwnd = user32.GetForegroundWindow()
                        cur_thread = kernel32.GetCurrentThreadId()
                        fg_pid = wintypes.DWORD()
                        fg_thread = user32.GetWindowThreadProcessId(fg_hwnd, ctypes.byref(fg_pid)) if fg_hwnd else 0
                        target_pid = wintypes.DWORD()
                        target_thread = user32.GetWindowThreadProcessId(hwnd, ctypes.byref(target_pid))

                        if fg_thread and fg_thread != cur_thread:
                            user32.AttachThreadInput(cur_thread, fg_thread, True)
                        if target_thread and target_thread != cur_thread:
                            user32.AttachThreadInput(cur_thread, target_thread, True)

                        user32.ShowWindow(hwnd, 9)
                        user32.BringWindowToTop(hwnd)
                        user32.SetForegroundWindow(hwnd)
                        user32.SetActiveWindow(hwnd)

                        if fg_thread and fg_thread != cur_thread:
                            user32.AttachThreadInput(cur_thread, fg_thread, False)
                        if target_thread and target_thread != cur_thread:
                            user32.AttachThreadInput(cur_thread, target_thread, False)

                        # Focus child edit control or dynamic window rect
                        for cls_name in ["Edit", "RichEditD2DPT", "NotepadTextBox"]:
                            child_hwnd = user32.FindWindowExW(hwnd, 0, cls_name, None)
                            if child_hwnd:
                                user32.SetFocus(child_hwnd)
                                break

                        # Dynamically click inside window rect (no hardcoded fixed coordinates)
                        rect = wintypes.RECT()
                        if user32.GetWindowRect(hwnd, ctypes.byref(rect)):
                            w_width = max(rect.right - rect.left, 100)
                            w_height = max(rect.bottom - rect.top, 100)
                            click_x = rect.left + (w_width // 2)
                            click_y = rect.top + max(65, min(w_height // 3, 140))
                            if HAS_PYAUTOGUI:
                                pyautogui.click(click_x, click_y)

                    time.sleep(0.08)
                    return hwnd

            time.sleep(0.12)
        return None

    def type_text(self, text: str, target_app: str = "notepad"):
        """Focuses target application and types text via pyautogui."""
        print(f"[AI Agent] Focusing '{target_app}' to type text...")
        hwnd = self.find_and_focus_window(target_app=target_app, timeout=3.0)
        
        if HAS_PYAUTOGUI:
            time.sleep(0.05)
            pyautogui.write(text, interval=0.01)
            print(f"[AI Agent] Successfully typed {len(text)} characters into {target_app}.")
            return True
        else:
            print("[Warning] pyautogui not installed. Please run: pip install pyautogui")
            return False

    def search_web(self, query: str):
        import urllib.parse
        encoded = urllib.parse.quote_plus(query.strip())
        url = f"https://www.google.com/search?q={encoded}"
        self.open_url(url)

    def open_url(self, url: str):
        """Launches real Chrome with URL or default browser."""
        print(f"[AI Agent] Opening URL: '{url}'...")
        final_url = url.strip()
        if not final_url.startswith("http://") and not final_url.startswith("https://"):
            final_url = f"https://{final_url}"

        # Try to locate Chrome executable on Windows
        chrome_exe = None
        if HAS_WINREG:
            try:
                reg_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\chrome.exe"
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                    val, _ = winreg.QueryValue(key, None)
                    if val and os.path.exists(val):
                        chrome_exe = val
            except Exception:
                pass

        if not chrome_exe:
            candidates = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
            ]
            for c in candidates:
                if os.path.exists(c):
                    chrome_exe = c
                    break

        if chrome_exe:
            subprocess.Popen([chrome_exe, final_url], shell=False)
            print(f"[AI Agent] Successfully opened '{final_url}' in Google Chrome.")
        else:
            if platform.system() == "Windows":
                subprocess.Popen(f'start "" "{final_url}"', shell=True)
            else:
                subprocess.Popen(["xdg-open", final_url] if sys.platform.startswith("linux") else ["open", final_url])
            print(f"[AI Agent] Successfully opened '{final_url}' in default browser.")

    def create_project_folder(self, folder_name: str = "Projects"):
        target = self.workspace / folder_name
        target.mkdir(parents=True, exist_ok=True)
        print(f"[AI Agent] Created project folder: {target}")
        return str(target)

if __name__ == "__main__":
    # Add backend path to sys.path
    backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
    if os.path.exists(backend_path) and backend_path not in sys.path:
        sys.path.insert(0, backend_path)

    try:
        from ai_brain import AIBrain
        from desktop_controller import DesktopController
        brain = AIBrain()
        controller = DesktopController()
        HAS_BRAIN_CONTROLLER = True
    except Exception as e:
        HAS_BRAIN_CONTROLLER = False
        agent = WindowsDesktopAgent()

    print("="*60)
    print(" Zevion - AI Desktop Copilot - Windows Native Engine v2.0")
    print("="*60)
    print("Type a natural command (e.g. 'open Chrome and search Minecraft', 'open Notepad and type hello', 'open a new CMD window', 'open yt', 'exit'):")
    
    while True:
        try:
            cmd = input("\nUser > ").strip()
            if not cmd:
                continue
            if cmd.lower() in ["exit", "quit", "q"]:
                print("Exiting AI Agent.")
                break

            if HAS_BRAIN_CONTROLLER:
                brain_res = brain.process_message(cmd, current_workspace=str(controller.workspace_root))
                print(f"[AI Agent] Response: {brain_res.get('response')}")
                actions = brain_res.get("actions", [])
                if actions:
                    print(f"[AI Agent] Executing {len(actions)} sequential actions...")
                    for i, act in enumerate(actions):
                        t_name = act.get("tool")
                        params = act.get("parameters", {})
                        print(f"  Step {i+1}: {act.get('description', t_name)}")
                        if i > 0:
                            controller._wait_for_action_readiness(actions[i-1].get("tool"), actions[i-1].get("parameters", {}))
                        res = controller.execute_action(t_name, params)
                        print(f"  -> Result: {'Success' if res.get('success', True) else 'Failed'}")
            else:
                low = cmd.lower()
                if "notepad" in low and ("type" in low or "write" in low):
                    import re
                    m = re.search(r'(?:type|write|put)\s+(.+)', cmd, re.IGNORECASE)
                    text_to_type = m.group(1).strip('"\' ') if m else "hello from AI"
                    agent.launch_app("notepad")
                    agent.type_text(text_to_type, "notepad")
                elif "chrome" in low:
                    agent.launch_app("chrome", new_window=("new" in low or "another" in low))
                elif "cmd" in low:
                    agent.launch_app("cmd", new_window=("new" in low or "another" in low))
                elif "powershell" in low:
                    agent.launch_app("powershell", new_window=("new" in low or "another" in low))
                elif "notepad" in low:
                    agent.launch_app("notepad", new_window=("new" in low or "another" in low))
                elif "calc" in low:
                    agent.launch_app("calc")
                elif "search" in low:
                    agent.search_web(cmd.replace("search", "").strip())
                elif "folder" in low:
                    agent.create_project_folder("Projects")
                else:
                    agent.launch_app(cmd)
        except KeyboardInterrupt:
            break
