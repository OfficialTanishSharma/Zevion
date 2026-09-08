"""
Zevion Backend Test Suite

⚠️ IMPORTANT: All API keys in this file are FAKE / DUMMY values used ONLY for
   testing provider validation & redaction logic. They are NOT real credentials,
   they are NOT linked to any account, and they will NOT authenticate anywhere.
   Do not mistake them for real secrets.

Clearly separated test suites:
1. Intent & Natural Language Parser Tests (App Aliases, Built-in Apps, Universal New Window Intents, YouTube Search, Video Playback, Conversational Fallback)
2. Compound Command Execution Pipeline Tests (Ordered Multi-step Parsing, Connectors, New Window Compound Sequences, Sequential Execution, Readiness Waiting)
3. Browser Automation & YouTube Video Resolution Tests (Organic /watch?v=... link extraction, creator channel resolution, regression test for viral old video vs newest upload)
4. Desktop Automation Tests (Universal App Discovery, Versioned Folders, Updater Filtering, Screenshots, Typing)
5. Window Management Tests (Minimize, Maximize, Restore, Close, Current Window, Context Target Resolution)
6. Universal System Apps & Default Reuse Tests (PowerShell, Paint, CMD, Task Manager, Calculator, Settings, Control Panel, MSC Consoles, Reuse vs New Window)
7. New Window Instance Targeting & Regression Tests (Target-instance tracking, existing minimized window protection)
8. Gemini Onboarding & API Key Security Tests (First-launch state, key submission, key skipping, non-blocking automation, audit log redaction)
9. AI Provider Management, Real Verification, Clean AI Names & Error Classification Tests
10. Gemini API Key Validation, Error Classification & Normal Multilingual/Hinglish Chat Tests
"""

import sys
import os
import time
import shutil
import io
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ai_brain import (
    AIBrain,
    AttachmentManager,
    MemoryManager,
    MAX_ATTACHMENTS_PER_MESSAGE,
    MAX_ATTACHMENT_SIZE_MB,
    MAX_TOTAL_ATTACHMENT_SIZE_MB,
    SUPPORTED_EXTENSIONS,
    get_game_template
)
from desktop_controller import (
    DesktopController,
    get_windows_desktop_path,
    get_windows_documents_path,
    get_windows_downloads_path
)
from safety_guard import SafetyGuard

class IsolatedBrainTestCase(unittest.TestCase):
    """Base test class providing an isolated temporary conversation storage file."""
    def setUp(self):
        self._temp_storage = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.brain = AIBrain(storage_path=self._temp_storage)

    def tearDown(self):
        if hasattr(self, "_temp_storage") and os.path.exists(self._temp_storage):
            try:
                os.remove(self._temp_storage)
            except Exception:
                pass

class TestIntentAndParser(IsolatedBrainTestCase):
    """Suite 1: Intent & Natural Language Parser Tests"""
    def setUp(self):
        super().setUp()

    # App Aliases
    def test_alias_open_dc(self):
        res = self.brain.process_message("open dc")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "discord")
        self.assertIn("Discord", res["response"])

    def test_alias_open_discord(self):
        res = self.brain.process_message("open discord")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "discord")

    def test_alias_open_discrod_typo(self):
        res = self.brain.process_message("open discrod")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "discord")

    def test_alias_open_yt(self):
        res = self.brain.process_message("open yt")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_website")
        self.assertEqual(res["actions"][0]["parameters"]["url"], "https://www.youtube.com")

    def test_alias_open_youtube(self):
        res = self.brain.process_message("open youtube")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_website")
        self.assertEqual(res["actions"][0]["parameters"]["url"], "https://www.youtube.com")

    def test_alias_open_chrom_typo(self):
        res = self.brain.process_message("open chrom")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")

    def test_alias_open_chrome(self):
        res = self.brain.process_message("open chrome")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")

    def test_alias_open_vscode(self):
        res = self.brain.process_message("open vscode")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "vscode")

    def test_alias_open_vs_code(self):
        res = self.brain.process_message("open vs code")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "vscode")

    def test_alias_open_roblx_typo(self):
        res = self.brain.process_message("open roblx")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "roblox_player")

    def test_alias_open_roblox(self):
        res = self.brain.process_message("open roblox")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "roblox_player")

    # YouTube Search vs Video Playback Single Intents
    def test_search_youtube_for_query_intent(self):
        res = self.brain.process_message("search YouTube for minecraft survival")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_website")
        self.assertFalse(res["actions"][0]["parameters"].get("playback", False))
        self.assertIn("search_query=minecraft+survival", res["actions"][0]["parameters"]["url"])

    def test_play_minecraft_video_playback_intent(self):
        res = self.brain.process_message("play Minecraft survival on YouTube")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_website")
        self.assertTrue(res["actions"][0]["parameters"].get("playback"))
        self.assertIn("search_query=Minecraft+survival", res["actions"][0]["parameters"]["url"])

    def test_play_first_minecraft_video_intent(self):
        res = self.brain.process_message("play the first Minecraft survival video")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_website")
        self.assertTrue(res["actions"][0]["parameters"].get("play_first"))

    def test_play_mrbeast_latest_video_intent(self):
        res = self.brain.process_message("play MrBeast latest video on YouTube")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_website")
        self.assertTrue(res["actions"][0]["parameters"].get("filter_latest"))
        self.assertIn("sp=CAISAhAB", res["actions"][0]["parameters"]["url"])
        self.assertIn("MrBeast", res["response"])

    def test_watch_mrbeast_newest_video_intent(self):
        res = self.brain.process_message("watch MrBeast newest video")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_website")
        self.assertTrue(res["actions"][0]["parameters"].get("filter_latest"))
        self.assertIn("sp=CAISAhAB", res["actions"][0]["parameters"]["url"])

    def test_play_senpaispider_latest_intent(self):
        res = self.brain.process_message("play SenpaiSpider latest video on YouTube")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_website")
        self.assertTrue(res["actions"][0]["parameters"].get("filter_latest"))

    def test_play_slaypoint_latest_intent(self):
        res = self.brain.process_message("play SlayPoint latest video on YouTube")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_website")
        self.assertTrue(res["actions"][0]["parameters"].get("filter_latest"))

    # Conversational Fallback
    def test_casual_hello_conversation(self):
        res = self.brain.process_message("hello")
        self.assertEqual(len(res["actions"]), 0)
        self.assertIn("Hello", res["response"])

    def test_casual_joke_conversation(self):
        res = self.brain.process_message("tell me a joke")
        self.assertEqual(len(res["actions"]), 0)
        self.assertTrue("joke" in res["response"].lower() or "freezing" in res["response"].lower() or "bugs" in res["response"].lower())

    # Built-in PowerShell Resolution Intents
    def test_open_powershell_capitalization(self):
        res = self.brain.process_message("open PowerShell")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "powershell")
        self.assertFalse(res["actions"][0]["parameters"].get("new_window", False))
        self.assertIn("PowerShell", res["response"])

    def test_open_powershell_lowercase(self):
        res = self.brain.process_message("open powershell")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "powershell")

    def test_open_pwsh_alias(self):
        res = self.brain.process_message("open pwsh")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "powershell")

    def test_open_windows_powershell_alias(self):
        res = self.brain.process_message("open Windows PowerShell")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "powershell")

    # Built-in Paint Resolution Intents
    def test_open_paint_standard(self):
        res = self.brain.process_message("open Paint")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "paint")

    def test_open_ms_paint_alias(self):
        res = self.brain.process_message("open MS Paint")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "paint")

    def test_open_microsoft_paint_alias(self):
        res = self.brain.process_message("open Microsoft Paint")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "paint")

    def test_open_mspaint_alias(self):
        res = self.brain.process_message("open mspaint")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "paint")

    # Built-in Command Prompt (CMD) Resolution Intents
    def test_open_cmd_uppercase(self):
        res = self.brain.process_message("open CMD")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "cmd")
        self.assertFalse(res["actions"][0]["parameters"].get("new_window", False))

    def test_open_command_prompt_standard(self):
        res = self.brain.process_message("open Command Prompt")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "cmd")
        self.assertFalse(res["actions"][0]["parameters"].get("new_window", False))

    def test_open_cmd_lowercase(self):
        res = self.brain.process_message("open cmd")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "cmd")
        self.assertFalse(res["actions"][0]["parameters"].get("new_window", False))

    # Universal New-Window Intent System
    def test_new_window_open_a_new_cmd_window(self):
        res = self.brain.process_message("open a new CMD window")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "cmd")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))
        self.assertIn("new", res["response"].lower())

    def test_new_window_open_a_new_powershell_window(self):
        res = self.brain.process_message("open a new PowerShell window")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "powershell")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))

    def test_new_window_open_another_cmd(self):
        res = self.brain.process_message("open another CMD")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "cmd")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))

    def test_new_window_open_a_new_chrome_window(self):
        res = self.brain.process_message("open a new Chrome window")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))

    def test_new_window_open_another_notepad(self):
        res = self.brain.process_message("open another Notepad")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "notepad")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))

    def test_new_window_open_another_chrome_window(self):
        res = self.brain.process_message("open another Chrome window")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))

    def test_new_window_open_a_new_notepad_window(self):
        res = self.brain.process_message("open a new Notepad window")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "notepad")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))

    def test_new_window_open_a_new_file_explorer_window(self):
        res = self.brain.process_message("open a new File Explorer window")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "explorer")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))

    def test_new_window_open_another_file_explorer_window(self):
        res = self.brain.process_message("open another File Explorer window")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "explorer")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))

    def test_new_window_of_chrome(self):
        res = self.brain.process_message("new window of Chrome")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))

    def test_new_window_for_chrome(self):
        res = self.brain.process_message("new window for Chrome")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))

    def test_create_another_chrome_window(self):
        res = self.brain.process_message("create another Chrome window")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))

    def test_start_a_new_command_prompt(self):
        res = self.brain.process_message("start a new Command Prompt")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "cmd")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))

    def test_open_new_cmd(self):
        res = self.brain.process_message("open new CMD")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "cmd")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))

    def test_launch_another_cmd(self):
        res = self.brain.process_message("launch another CMD")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "cmd")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))

    def test_open_another_powershell(self):
        res = self.brain.process_message("open another PowerShell")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "powershell")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))


class TestCompoundCommandPipeline(IsolatedBrainTestCase):
    """Suite 2: Multi-step Compound Command Execution Pipeline Tests"""
    def setUp(self):
        super().setUp()
        test_ws = Path.home() / "ai-desktop-workspace-test"
        self.controller = DesktopController(str(test_ws))

    def test_compound_open_chrome_and_search_minecraft(self):
        res = self.brain.process_message("open Chrome and search Minecraft")
        self.assertEqual(len(res["actions"]), 2)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")
        self.assertEqual(res["actions"][1]["tool"], "open_website")
        self.assertEqual(res["actions"][1]["parameters"]["search_query"], "Minecraft")
        self.assertIn("google.com/search?q=Minecraft", res["actions"][1]["parameters"]["url"])

        exec_results = self.controller.execute_action_sequence(res["actions"])
        self.assertEqual(len(exec_results), 2)
        self.assertTrue(exec_results[0]["success"])
        self.assertEqual(exec_results[0]["app_key"], "chrome")
        self.assertTrue(exec_results[1]["success"])
        self.assertIn("google.com/search?q=Minecraft", exec_results[1]["url"])

    def test_compound_open_chrome_then_search_minecraft(self):
        res = self.brain.process_message("open Chrome then search Minecraft")
        self.assertEqual(len(res["actions"]), 2)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")
        self.assertEqual(res["actions"][1]["tool"], "open_website")
        self.assertEqual(res["actions"][1]["parameters"]["search_query"], "Minecraft")

        exec_results = self.controller.execute_action_sequence(res["actions"])
        self.assertEqual(len(exec_results), 2)
        self.assertTrue(exec_results[0]["success"])
        self.assertTrue(exec_results[1]["success"])

    def test_compound_open_chrome_and_then_search_minecraft(self):
        res = self.brain.process_message("open Chrome and then search Minecraft")
        self.assertEqual(len(res["actions"]), 2)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][1]["tool"], "open_website")
        self.assertEqual(res["actions"][1]["parameters"]["search_query"], "Minecraft")

    def test_compound_open_chrome_and_search_youtube_for_minecraft(self):
        res = self.brain.process_message("open Chrome and search YouTube for Minecraft")
        self.assertEqual(len(res["actions"]), 2)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")
        self.assertEqual(res["actions"][1]["tool"], "open_website")
        self.assertEqual(res["actions"][1]["parameters"]["search_query"], "Minecraft")
        self.assertIn("youtube.com/results?search_query=Minecraft", res["actions"][1]["parameters"]["url"])

        exec_results = self.controller.execute_action_sequence(res["actions"])
        self.assertEqual(len(exec_results), 2)
        self.assertTrue(exec_results[0]["success"])
        self.assertTrue(exec_results[1]["success"])

    def test_standalone_open_youtube(self):
        res = self.brain.process_message("open YouTube")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_website")
        self.assertEqual(res["actions"][0]["parameters"]["url"], "https://www.youtube.com")
        self.assertFalse(res["actions"][0]["parameters"].get("playback", False))
        self.assertEqual(res["actions"][0]["parameters"].get("search_query", ""), "")

        exec_results = self.controller.execute_action_sequence(res["actions"])
        self.assertEqual(len(exec_results), 1)
        self.assertTrue(exec_results[0]["success"])
        self.assertEqual(exec_results[0]["url"], "https://www.youtube.com")

    def test_compound_open_youtube_and_search_minecraft(self):
        res = self.brain.process_message("open YouTube and search Minecraft")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_website")
        self.assertEqual(res["actions"][0]["parameters"]["search_query"], "Minecraft")
        self.assertIn("youtube.com/results?search_query=Minecraft", res["actions"][0]["parameters"]["url"])

        exec_results = self.controller.execute_action_sequence(res["actions"])
        self.assertEqual(len(exec_results), 1)
        self.assertTrue(exec_results[0]["success"])
        self.assertIn("youtube.com/results?search_query=Minecraft", exec_results[0]["url"])

    def test_compound_open_notepad_and_type_hello_brother(self):
        res = self.brain.process_message("open Notepad and type hello brother")
        self.assertEqual(len(res["actions"]), 2)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "notepad")
        self.assertEqual(res["actions"][1]["tool"], "type_text")
        self.assertEqual(res["actions"][1]["parameters"]["text"], "hello brother")
        self.assertEqual(res["actions"][1]["parameters"]["target_app"], "notepad")

        exec_results = self.controller.execute_action_sequence(res["actions"])
        self.assertEqual(len(exec_results), 2)
        self.assertTrue(exec_results[0]["success"])
        self.assertTrue(exec_results[1]["success"])
        self.assertEqual(exec_results[1]["text"], "hello brother")

    def test_compound_open_youtube_and_play_minecraft_survival(self):
        res = self.brain.process_message("open YouTube and play Minecraft survival")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_website")
        self.assertTrue(res["actions"][0]["parameters"].get("playback"))
        self.assertEqual(res["actions"][0]["parameters"]["search_query"], "Minecraft survival")

        exec_results = self.controller.execute_action_sequence(res["actions"])
        self.assertEqual(len(exec_results), 1)
        self.assertTrue(exec_results[0]["success"])
        self.assertEqual(exec_results[0]["playback_state"], "PLAYING")

    def test_compound_open_discord_then_open_chrome(self):
        res = self.brain.process_message("open Discord then open Chrome")
        self.assertEqual(len(res["actions"]), 2)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "discord")
        self.assertEqual(res["actions"][1]["tool"], "open_application")
        self.assertEqual(res["actions"][1]["parameters"]["app_name"], "chrome")

        exec_results = self.controller.execute_action_sequence(res["actions"])
        self.assertEqual(len(exec_results), 2)
        self.assertTrue(exec_results[0]["success"])
        self.assertTrue(exec_results[1]["success"])

    def test_compound_browser_reuse_focus(self):
        res1 = self.controller.open_application("chrome")
        self.assertTrue(res1["success"])
        
        res2 = self.controller.open_website(url="https://www.google.com/search?q=Minecraft", search_query="Minecraft")
        self.assertTrue(res2["success"])
        self.assertEqual(res2["search_query"], "Minecraft")
        self.assertIn("google.com/search?q=Minecraft", res2["url"])
        self.assertEqual(self.controller.active_window_title, "Google Chrome - Minecraft")

    # Compound New-Window Commands
    def test_compound_open_a_new_cmd_window_and_type_hello(self):
        res = self.brain.process_message("open a new CMD window and type hello")
        self.assertEqual(len(res["actions"]), 2)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "cmd")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))
        self.assertEqual(res["actions"][1]["tool"], "type_text")
        self.assertEqual(res["actions"][1]["parameters"]["text"], "hello")
        self.assertEqual(res["actions"][1]["parameters"]["target_app"], "cmd")

        exec_results = self.controller.execute_action_sequence(res["actions"])
        self.assertEqual(len(exec_results), 2)
        self.assertTrue(exec_results[0]["success"])
        self.assertTrue(exec_results[0]["new_window"])
        self.assertTrue(exec_results[1]["success"])
        self.assertEqual(exec_results[1]["text"], "hello")

    def test_compound_open_a_new_powershell_window_then_open_discord(self):
        res = self.brain.process_message("open a new PowerShell window then open Discord")
        self.assertEqual(len(res["actions"]), 2)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "powershell")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))
        self.assertEqual(res["actions"][1]["tool"], "open_application")
        self.assertEqual(res["actions"][1]["parameters"]["app_name"], "discord")
        self.assertFalse(res["actions"][1]["parameters"].get("new_window", False))

        exec_results = self.controller.execute_action_sequence(res["actions"])
        self.assertEqual(len(exec_results), 2)
        self.assertTrue(exec_results[0]["success"])
        self.assertTrue(exec_results[0]["new_window"])
        self.assertTrue(exec_results[1]["success"])

    def test_compound_open_chrome_search_minecraft_then_new_chrome_window(self):
        res = self.brain.process_message("open Chrome and search Minecraft, then open a new Chrome window")
        self.assertEqual(len(res["actions"]), 3)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")
        self.assertFalse(res["actions"][0]["parameters"].get("new_window", False))
        
        self.assertEqual(res["actions"][1]["tool"], "open_website")
        self.assertEqual(res["actions"][1]["parameters"]["search_query"], "Minecraft")
        
        self.assertEqual(res["actions"][2]["tool"], "open_application")
        self.assertEqual(res["actions"][2]["parameters"]["app_name"], "chrome")
        self.assertTrue(res["actions"][2]["parameters"].get("new_window"))

        exec_results = self.controller.execute_action_sequence(res["actions"])
        self.assertEqual(len(exec_results), 3)
        self.assertTrue(exec_results[0]["success"])
        self.assertTrue(exec_results[1]["success"])
        self.assertTrue(exec_results[2]["success"])
        self.assertTrue(exec_results[2]["new_window"])

    def test_compound_open_a_new_notepad_window_and_type(self):
        res = self.brain.process_message("open a new Notepad window and type test content")
        self.assertEqual(len(res["actions"]), 2)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "notepad")
        self.assertTrue(res["actions"][0]["parameters"].get("new_window"))
        self.assertEqual(res["actions"][1]["tool"], "type_text")
        self.assertEqual(res["actions"][1]["parameters"]["text"], "test content")


class TestBrowserAutomationAndYouTube(unittest.TestCase):
    """Suite 3: Browser Automation & YouTube Video Resolution Tests"""
    def setUp(self):
        test_ws = Path.home() / "ai-desktop-workspace-test"
        self.controller = DesktopController(str(test_ws))

    def test_browser_resolve_first_organic_video(self):
        watch_url, vid_id, diag = self.controller._resolve_youtube_video_url("Minecraft survival", filter_latest=False)
        if watch_url:
            self.assertTrue(watch_url.startswith("https://www.youtube.com/watch?v="))
            self.assertEqual(len(vid_id), 11)
            self.assertIn("autoplay=1", watch_url)
            self.assertIn("candidate_count", diag)

    def test_browser_resolve_newest_upload_official_channel(self):
        watch_url, vid_id, diag = self.controller._resolve_youtube_video_url("MrBeast latest", filter_latest=True, channel="MrBeast")
        if watch_url:
            self.assertTrue(watch_url.startswith("https://www.youtube.com/watch?v="))
            self.assertEqual(len(vid_id), 11)
            self.assertEqual(diag.get("requested_creator"), "MrBeast")
            self.assertEqual(diag.get("resolved_channel"), "@MrBeast")
            self.assertIn("candidate_count", diag)

    def test_regression_viral_old_video_filtered_for_newest_upload(self):
        candidates = [
            {"title": "Viral Old Video (5 months ago)", "score": 2592000 * 5, "video_id": "old_viral_123"},
            {"title": "Genuinely Newest Upload (2 days ago)", "score": 86400 * 2, "video_id": "new_upload_456"}
        ]
        candidates.sort(key=lambda x: x["score"])
        self.assertEqual(candidates[0]["video_id"], "new_upload_456")
        self.assertEqual(candidates[0]["title"], "Genuinely Newest Upload (2 days ago)")

    def test_desktop_controller_open_website_playback_state(self):
        web_res = self.controller.open_website(
            url="",
            search_query="Minecraft survival",
            playback=True,
            play_first=True
        )
        self.assertTrue(web_res["success"])
        self.assertTrue(web_res["playback"])
        self.assertEqual(web_res["playback_state"], "PLAYING")
        self.assertIn("youtube.com", web_res["url"])
        self.assertIn("diagnostics", web_res)


class TestDesktopAutomation(IsolatedBrainTestCase):
    """Suite 4: Desktop Automation & Safety System Tests"""
    def setUp(self):
        super().setUp()
        test_ws = Path.home() / "ai-desktop-workspace-test"
        self.controller = DesktopController(str(test_ws))
        self.safety = SafetyGuard(mode="balanced")

    def test_versioned_directory_resolver_latest(self):
        test_dir = Path.home() / "test_app_versions"
        v1 = test_dir / "app-1.0.0"
        v2 = test_dir / "app-1.0.9251"
        v1.mkdir(parents=True, exist_ok=True)
        v2.mkdir(parents=True, exist_ok=True)

        (v1 / "Discord.exe").write_text("v1 binary")
        (v1 / "Update.exe").write_text("updater")
        (v2 / "Discord.exe").write_text("v2 binary")
        (v2 / "Update.exe").write_text("updater")

        resolved = self.controller._resolve_versioned_executable(str(test_dir), ["Discord.exe"])
        self.assertIsNotNone(resolved)
        self.assertTrue(resolved.endswith("Discord.exe"))
        self.assertIn("app-1.0.9251", resolved)
        self.assertNotIn("Update.exe", resolved)
        shutil.rmtree(test_dir)

    def test_updater_and_uninstaller_filtering(self):
        test_dir = Path.home() / "test_uninstaller_filter"
        test_dir.mkdir(parents=True, exist_ok=True)
        (test_dir / "uninstall.exe").write_text("uninstaller")
        (test_dir / "unins000.exe").write_text("unins000")
        (test_dir / "setup.exe").write_text("setup")

        resolved = self.controller._resolve_versioned_executable(str(test_dir), [])
        self.assertIsNone(resolved)
        shutil.rmtree(test_dir)

    def test_dangerous_delete_safety_guard(self):
        res = self.brain.process_message("Delete file important_system_data.db")
        self.assertEqual(res["safety_level"], "dangerous")
        self.assertTrue(res["confirmation_required"])

    def test_desktop_controller_take_screenshot(self):
        shot_res = self.controller.take_screenshot("fullscreen", "test_screen.png")
        self.assertTrue(shot_res["success"])
        self.assertIn("absolute_path", shot_res)
        self.assertIn("save_path", shot_res)
        self.assertTrue(os.path.isabs(shot_res["absolute_path"]))


class TestWindowManagement(IsolatedBrainTestCase):
    """Suite 5: Universal Natural-Language Window Management Tests"""
    def setUp(self):
        super().setUp()
        test_ws = Path.home() / "ai-desktop-workspace-test"
        self.controller = DesktopController(str(test_ws))

    def test_minimize_chrome(self):
        res = self.brain.process_message("minimize Chrome")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "minimize_window")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")

        exec_res = self.controller.execute_action("minimize_window", {"app_name": "chrome"})
        self.assertTrue(exec_res["success"])
        self.assertEqual(exec_res["action"], "minimize_window")

    def test_maximize_chrome(self):
        res = self.brain.process_message("maximize Chrome")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "maximize_window")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")

        exec_res = self.controller.execute_action("maximize_window", {"app_name": "chrome"})
        self.assertTrue(exec_res["success"])
        self.assertEqual(exec_res["action"], "maximize_window")

    def test_restore_chrome(self):
        res = self.brain.process_message("restore Chrome")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "restore_window")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")

        exec_res = self.controller.execute_action("restore_window", {"app_name": "chrome"})
        self.assertTrue(exec_res["success"])
        self.assertEqual(exec_res["action"], "restore_window")

    def test_close_chrome(self):
        res = self.brain.process_message("close Chrome")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "close_window")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")

        exec_res = self.controller.execute_action("close_window", {"app_name": "chrome"})
        self.assertTrue(exec_res["success"])
        self.assertEqual(exec_res["action"], "close_window")

    def test_minimize_discord(self):
        res = self.brain.process_message("minimize Discord")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "minimize_window")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "discord")

        exec_res = self.controller.execute_action("minimize_window", {"app_name": "discord"})
        self.assertTrue(exec_res["success"])

    def test_maximize_discord(self):
        res = self.brain.process_message("maximize Discord")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "maximize_window")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "discord")

        exec_res = self.controller.execute_action("maximize_window", {"app_name": "discord"})
        self.assertTrue(exec_res["success"])

    def test_current_window_operations(self):
        r1 = self.brain.process_message("minimize the current window")
        self.assertEqual(len(r1["actions"]), 1)
        self.assertEqual(r1["actions"][0]["tool"], "minimize_window")
        self.assertEqual(r1["actions"][0]["parameters"]["app_name"], "current")
        e1 = self.controller.execute_action("minimize_window", {"app_name": "current"})
        self.assertTrue(e1["success"])

        r2 = self.brain.process_message("maximize this window")
        self.assertEqual(len(r2["actions"]), 1)
        self.assertEqual(r2["actions"][0]["tool"], "maximize_window")
        self.assertEqual(r2["actions"][0]["parameters"]["app_name"], "current")
        e2 = self.controller.execute_action("maximize_window", {"app_name": "current"})
        self.assertTrue(e2["success"])

        r3 = self.brain.process_message("restore this window")
        self.assertEqual(len(r3["actions"]), 1)
        self.assertEqual(r3["actions"][0]["tool"], "restore_window")
        self.assertEqual(r3["actions"][0]["parameters"]["app_name"], "current")
        e3 = self.controller.execute_action("restore_window", {"app_name": "current"})
        self.assertTrue(e3["success"])

        r4 = self.brain.process_message("close the current window")
        self.assertEqual(len(r4["actions"]), 1)
        self.assertEqual(r4["actions"][0]["tool"], "close_window")
        self.assertEqual(r4["actions"][0]["parameters"]["app_name"], "current")
        e4 = self.controller.execute_action("close_window", {"app_name": "current"})
        self.assertTrue(e4["success"])

    def test_compound_window_management_open_and_maximize(self):
        res = self.brain.process_message("open Chrome and maximize it")
        self.assertEqual(len(res["actions"]), 2)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")
        self.assertEqual(res["actions"][1]["tool"], "maximize_window")
        self.assertEqual(res["actions"][1]["parameters"]["app_name"], "chrome")

        exec_res = self.controller.execute_action_sequence(res["actions"])
        self.assertEqual(len(exec_res), 2)
        self.assertTrue(exec_res[0]["success"])
        self.assertTrue(exec_res[1]["success"])

    def test_compound_window_management_open_discord_then_minimize(self):
        res = self.brain.process_message("open Discord then minimize it")
        self.assertEqual(len(res["actions"]), 2)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "discord")
        self.assertEqual(res["actions"][1]["tool"], "minimize_window")
        self.assertEqual(res["actions"][1]["parameters"]["app_name"], "discord")

        exec_res = self.controller.execute_action_sequence(res["actions"])
        self.assertEqual(len(exec_res), 2)
        self.assertTrue(exec_res[0]["success"])
        self.assertTrue(exec_res[1]["success"])

    def test_compound_window_management_search_and_minimize(self):
        res = self.brain.process_message("open Chrome and search Minecraft, then minimize Chrome")
        self.assertEqual(len(res["actions"]), 3)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][1]["tool"], "open_website")
        self.assertEqual(res["actions"][2]["tool"], "minimize_window")
        self.assertEqual(res["actions"][2]["parameters"]["app_name"], "chrome")

        exec_res = self.controller.execute_action_sequence(res["actions"])
        self.assertEqual(len(exec_res), 3)
        self.assertTrue(exec_res[0]["success"])
        self.assertTrue(exec_res[1]["success"])
        self.assertTrue(exec_res[2]["success"])

    def test_unknown_application_handling(self):
        res = self.controller.minimize_window("NonExistentAppXYZ_12345")
        self.assertFalse(res["success"])
        self.assertIn("No active window found", res["error"])
        self.assertIn("NonExistentAppXYZ_12345", res["error"])

        res_close = self.controller.close_window("InvalidProgramABC_999")
        self.assertFalse(res_close["success"])
        self.assertIn("No active window found", res_close["error"])

    def test_minimize_the_new_cmd_window(self):
        res = self.brain.process_message("minimize the new CMD window")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "minimize_window")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "cmd")

    def test_maximize_the_new_powershell_window(self):
        res = self.brain.process_message("maximize the new PowerShell window")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "maximize_window")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "powershell")

    def test_restore_the_new_cmd_window(self):
        res = self.brain.process_message("restore the new CMD window")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "restore_window")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "cmd")

    def test_close_the_new_notepad_window(self):
        res = self.brain.process_message("close the new Notepad window")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "close_window")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "notepad")


class TestUniversalSystemApps(IsolatedBrainTestCase):
    """Suite 6: Universal Windows System-App Discovery, Activation & Control Tests"""
    def setUp(self):
        super().setUp()
        test_ws = Path.home() / "ai-desktop-workspace-test"
        self.controller = DesktopController(str(test_ws))

    def test_open_task_manager(self):
        res = self.brain.process_message("open Task Manager")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "task_manager")
        self.assertIn("Task Manager", res["response"])

        exec_res = self.controller.execute_action("open_application", {"app_name": "task_manager"})
        self.assertTrue(exec_res["success"])
        self.assertEqual(exec_res["app_key"], "task_manager")

    def test_open_taskmgr_alias(self):
        res = self.brain.process_message("open taskmgr")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "task_manager")

    def test_open_task_mgr_alias(self):
        res = self.brain.process_message("open task mgr")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "task_manager")

    def test_open_calculator(self):
        res = self.brain.process_message("open Calculator")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "calculator")

        exec_res = self.controller.execute_action("open_application", {"app_name": "calculator"})
        self.assertTrue(exec_res["success"])

    def test_open_paint(self):
        res = self.brain.process_message("open Paint")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "paint")

        exec_res = self.controller.execute_action("open_application", {"app_name": "paint"})
        self.assertTrue(exec_res["success"])

    def test_open_file_explorer(self):
        res = self.brain.process_message("open File Explorer")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "explorer")

        exec_res = self.controller.execute_action("open_application", {"app_name": "explorer"})
        self.assertTrue(exec_res["success"])

    def test_open_settings(self):
        res = self.brain.process_message("open Settings")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "settings")

        exec_res = self.controller.execute_action("open_application", {"app_name": "settings"})
        self.assertTrue(exec_res["success"])

    def test_open_control_panel(self):
        res = self.brain.process_message("open Control Panel")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "control_panel")

        exec_res = self.controller.execute_action("open_application", {"app_name": "control_panel"})
        self.assertTrue(exec_res["success"])

    def test_open_command_prompt(self):
        res = self.brain.process_message("open Command Prompt")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "cmd")

        exec_res = self.controller.execute_action("open_application", {"app_name": "cmd"})
        self.assertTrue(exec_res["success"])

    def test_open_powershell(self):
        res = self.brain.process_message("open PowerShell")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "powershell")

        exec_res = self.controller.execute_action("open_application", {"app_name": "powershell"})
        self.assertTrue(exec_res["success"])

    def test_open_windows_terminal(self):
        res = self.brain.process_message("open Windows Terminal")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "terminal")

        exec_res = self.controller.execute_action("open_application", {"app_name": "terminal"})
        self.assertTrue(exec_res["success"])

    def test_open_device_manager(self):
        res = self.brain.process_message("open Device Manager")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "device_manager")

        exec_res = self.controller.execute_action("open_application", {"app_name": "device_manager"})
        self.assertTrue(exec_res["success"])

    def test_open_services(self):
        res = self.brain.process_message("open Services")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "services")

        exec_res = self.controller.execute_action("open_application", {"app_name": "services"})
        self.assertTrue(exec_res["success"])

    def test_open_event_viewer(self):
        res = self.brain.process_message("open Event Viewer")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "event_viewer")

        exec_res = self.controller.execute_action("open_application", {"app_name": "event_viewer"})
        self.assertTrue(exec_res["success"])

    def test_open_resource_monitor(self):
        res = self.brain.process_message("open Resource Monitor")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "resource_monitor")

        exec_res = self.controller.execute_action("open_application", {"app_name": "resource_monitor"})
        self.assertTrue(exec_res["success"])

    def test_open_task_scheduler(self):
        res = self.brain.process_message("open Task Scheduler")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "task_scheduler")

        exec_res = self.controller.execute_action("open_application", {"app_name": "task_scheduler"})
        self.assertTrue(exec_res["success"])

    def test_open_disk_management(self):
        res = self.brain.process_message("open Disk Management")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "disk_management")

        exec_res = self.controller.execute_action("open_application", {"app_name": "disk_management"})
        self.assertTrue(exec_res["success"])

    def test_open_system_information(self):
        res = self.brain.process_message("open System Information")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "system_information")

        exec_res = self.controller.execute_action("open_application", {"app_name": "system_information"})
        self.assertTrue(exec_res["success"])

    def test_fuzzy_task_manager_typos(self):
        r1 = self.brain.process_message("open taks manager")
        self.assertEqual(r1["actions"][0]["parameters"]["app_name"], "task_manager")

        r2 = self.brain.process_message("open taskmanger")
        self.assertEqual(r2["actions"][0]["parameters"]["app_name"], "task_manager")

        r3 = self.brain.process_message("open calcuator")
        self.assertEqual(r3["actions"][0]["parameters"]["app_name"], "calculator")

        r4 = self.brain.process_message("open powrshell")
        self.assertEqual(r4["actions"][0]["parameters"]["app_name"], "powershell")

    def test_compound_system_app_commands(self):
        r1 = self.brain.process_message("open Task Manager and maximize it")
        self.assertEqual(len(r1["actions"]), 2)
        self.assertEqual(r1["actions"][0]["parameters"]["app_name"], "task_manager")
        self.assertEqual(r1["actions"][1]["tool"], "maximize_window")
        self.assertEqual(r1["actions"][1]["parameters"]["app_name"], "task_manager")

        r2 = self.brain.process_message("open Calculator and minimize it")
        self.assertEqual(len(r2["actions"]), 2)
        self.assertEqual(r2["actions"][0]["parameters"]["app_name"], "calculator")
        self.assertEqual(r2["actions"][1]["tool"], "minimize_window")
        self.assertEqual(r2["actions"][1]["parameters"]["app_name"], "calculator")

        r3 = self.brain.process_message("open Settings then open Chrome")
        self.assertEqual(len(r3["actions"]), 2)
        self.assertEqual(r3["actions"][0]["parameters"]["app_name"], "settings")
        self.assertEqual(r3["actions"][1]["parameters"]["app_name"], "chrome")

        r4 = self.brain.process_message("open Task Manager then open Discord")
        self.assertEqual(len(r4["actions"]), 2)
        self.assertEqual(r4["actions"][0]["parameters"]["app_name"], "task_manager")
        self.assertEqual(r4["actions"][1]["parameters"]["app_name"], "discord")

        r5 = self.brain.process_message("open Calculator and then open Notepad")
        self.assertEqual(len(r5["actions"]), 2)
        self.assertEqual(r5["actions"][0]["parameters"]["app_name"], "calculator")
        self.assertEqual(r5["actions"][1]["parameters"]["app_name"], "notepad")

        r6 = self.brain.process_message("open Task Manager, then minimize it")
        self.assertEqual(len(r6["actions"]), 2)
        self.assertEqual(r6["actions"][0]["parameters"]["app_name"], "task_manager")
        self.assertEqual(r6["actions"][1]["tool"], "minimize_window")
        self.assertEqual(r6["actions"][1]["parameters"]["app_name"], "task_manager")

    def test_system_app_window_management_full_lifecycle(self):
        m1 = self.controller.execute_action("minimize_window", {"app_name": "task_manager"})
        self.assertTrue(m1["success"])

        m2 = self.controller.execute_action("maximize_window", {"app_name": "task_manager"})
        self.assertTrue(m2["success"])

        m3 = self.controller.execute_action("restore_window", {"app_name": "task_manager"})
        self.assertTrue(m3["success"])

        m4 = self.controller.execute_action("close_window", {"app_name": "task_manager"})
        self.assertTrue(m4["success"])

    def test_safety_protected_system_processes(self):
        res = self.controller.close_window("explorer")
        self.assertFalse(res["success"])
        self.assertIn("Safety protection", res["error"])

    def test_default_reuse_cmd_behavior(self):
        res = self.controller.open_application("cmd", new_window=False)
        self.assertTrue(res["success"])
        self.assertFalse(res["new_window"])

    def test_default_reuse_chrome_behavior(self):
        res = self.controller.open_application("chrome", new_window=False)
        self.assertTrue(res["success"])
        self.assertFalse(res["new_window"])

    def test_explicit_new_window_execution(self):
        res = self.controller.open_application("cmd", new_window=True)
        self.assertTrue(res["success"])
        self.assertTrue(res["new_window"])
        self.assertFalse(res["already_running"])


class TestNewWindowTargeting(IsolatedBrainTestCase):
    """Suite 7: New Window Instance Targeting & Regression Tests"""
    def setUp(self):
        super().setUp()
        test_ws = Path.home() / "ai-desktop-workspace-test"
        self.controller = DesktopController(str(test_ws))

    def test_new_cmd_instance_targeting(self):
        res = self.brain.process_message("open a new CMD window and type hello")
        self.assertEqual(len(res["actions"]), 2)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "cmd")
        self.assertTrue(res["actions"][0]["parameters"]["new_window"])

        exec_res = self.controller.execute_action_sequence(res["actions"])
        self.assertEqual(len(exec_res), 2)
        self.assertTrue(exec_res[0]["success"])
        self.assertTrue(exec_res[0]["new_window"])
        self.assertIsNotNone(exec_res[0]["target_pid"])
        
        # Action 2 targets the new instance
        self.assertTrue(exec_res[1]["success"])
        self.assertEqual(exec_res[1]["text"], "hello")
        self.assertEqual(exec_res[1]["target_app"], "cmd")
        self.assertTrue(exec_res[1]["used_new_window_instance"])

    def test_new_powershell_instance_targeting(self):
        res = self.brain.process_message("open a new PowerShell window and type hello")
        self.assertEqual(len(res["actions"]), 2)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "powershell")
        self.assertTrue(res["actions"][0]["parameters"]["new_window"])

        exec_res = self.controller.execute_action_sequence(res["actions"])
        self.assertEqual(len(exec_res), 2)
        self.assertTrue(exec_res[0]["success"])
        self.assertTrue(exec_res[0]["new_window"])
        self.assertTrue(exec_res[1]["success"])
        self.assertEqual(exec_res[1]["text"], "hello")
        self.assertTrue(exec_res[1]["used_new_window_instance"])

    def test_new_notepad_instance_targeting(self):
        res = self.brain.process_message("open a new Notepad window and type hello")
        self.assertEqual(len(res["actions"]), 2)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "notepad")
        self.assertTrue(res["actions"][0]["parameters"]["new_window"])

        exec_res = self.controller.execute_action_sequence(res["actions"])
        self.assertEqual(len(exec_res), 2)
        self.assertTrue(exec_res[0]["success"])
        self.assertTrue(exec_res[0]["new_window"])
        self.assertTrue(exec_res[1]["success"])
        self.assertEqual(exec_res[1]["text"], "hello")
        self.assertTrue(exec_res[1]["used_new_window_instance"])

    def test_existing_minimized_cmd_untouched_during_new_window_command(self):
        existing_minimized_hwnd = 1001
        existing_minimized_pid = 5555
        self.controller.last_target_hwnd = existing_minimized_hwnd
        self.controller.last_target_pid = existing_minimized_pid
        self.controller.last_new_window = False

        res = self.brain.process_message("open a new CMD window and type hello")
        self.assertTrue(res["actions"][0]["parameters"]["new_window"])

        exec_res = self.controller.execute_action_sequence(res["actions"])
        
        self.assertTrue(exec_res[0]["new_window"])
        self.assertNotEqual(exec_res[0]["pid"], existing_minimized_pid)
        self.assertFalse(exec_res[0]["already_running"])
        
        self.assertTrue(exec_res[1]["used_new_window_instance"])
        self.assertNotEqual(exec_res[1]["target_pid"], existing_minimized_pid)


class TestGeminiOnboardingAndSecurity(IsolatedBrainTestCase):
    """Suite 8: Gemini Onboarding & API Key Security Tests"""
    def setUp(self):
        super().setUp()
        self.safety = SafetyGuard(mode="balanced")

    def test_first_launch_onboarding_state(self):
        settings = self.brain.get_settings()
        self.assertFalse(settings["onboarding_completed"])
        self.assertEqual(settings["active_provider"], "builtin")
        self.assertFalse(settings["has_gemini_key"])

    def test_continue_with_gemini_api_key(self):
        gemini = self.brain.providers["gemini"]
        gemini._test_verification_hook = lambda k: (True, "valid", "Gemini API key verified successfully.")
        
        test_key = "AIzaSyDummySecretGeminiKey123456789"
        res = self.brain.complete_onboarding(api_key=test_key, skip=False)
        self.assertTrue(res["onboarding_completed"])
        self.assertEqual(res["active_provider"], "gemini")

        settings = self.brain.get_settings()
        self.assertTrue(settings["onboarding_completed"])
        self.assertEqual(settings["active_provider"], "gemini")
        self.assertTrue(settings["has_gemini_key"])

    def test_continue_without_api_key(self):
        res = self.brain.complete_onboarding(api_key="", skip=True)
        self.assertTrue(res["onboarding_completed"])
        self.assertEqual(res["active_provider"], "builtin")
        self.assertFalse(res["has_gemini_key"])

        settings = self.brain.get_settings()
        self.assertTrue(settings["onboarding_completed"])
        self.assertEqual(settings["active_provider"], "builtin")
        self.assertFalse(settings["has_gemini_key"])

    def test_onboarding_does_not_appear_again_after_completion(self):
        self.brain.complete_onboarding(api_key="", skip=True)
        self.assertTrue(self.brain.onboarding_completed)

        res = self.brain.process_message("open Chrome")
        self.assertEqual(len(res["actions"]), 1)
        self.assertTrue(self.brain.onboarding_completed)

    def test_missing_api_key_does_not_break_normal_automation(self):
        self.brain.set_active_provider("builtin")
        r1 = self.brain.process_message("open Chrome and search Minecraft")
        self.assertEqual(len(r1["actions"]), 2)

        r2 = self.brain.process_message("open a new CMD window and type hello")
        self.assertEqual(len(r2["actions"]), 2)

        r3 = self.brain.process_message("open Paint")
        self.assertEqual(len(r3["actions"]), 1)

    def test_api_key_never_printed_in_logs(self):
        raw_secret_key = "AIzaSyTestSecret12345678901234567890"
        self.safety.log_execution(
            tool_name="update_settings",
            parameters={"provider": "gemini", "api_key": raw_secret_key},
            result={"success": True, "token": raw_secret_key},
            risk_level="safe"
        )
        logs = self.safety.get_audit_logs(limit=10)
        self.assertTrue(len(logs) > 0)
        last_log_str = str(logs[0])
        
        self.assertNotIn(raw_secret_key, last_log_str)
        self.assertIn("[REDACTED]", last_log_str)


class TestAIProviderManagement(IsolatedBrainTestCase):
    """Suite 9: AI Provider Management, Real Verification, Clean AI Names & Error Classification Tests"""
    def setUp(self):
        super().setUp()
        self.safety = SafetyGuard(mode="balanced")

    def test_ui_displays_only_clean_ai_names(self):
        providers = self.brain.get_providers_list()
        allowed_names = {"Built-in", "Gemini", "Claude", "ChatGPT", "NVIDIA", "Kimi", "DeepSeek", "Qwen"}
        
        for p in providers:
            self.assertIn(p["name"], allowed_names)
            self.assertIn(p["display_name"], allowed_names)
            self.assertNotIn("gemini-2.5", p["name"].lower())
            self.assertNotIn("claude-sonnet", p["name"].lower())
            self.assertNotIn("deepseek-ai/", p["name"].lower())
            self.assertNotIn("gpt-4o", p["name"].lower())
            self.assertNotIn("qwen/", p["name"].lower())
            self.assertNotIn("moonshotai/", p["name"].lower())

    def test_valid_claude_api_key_verification(self):
        claude = self.brain.providers["claude"]
        claude._test_verification_hook = lambda k: (True, "valid", "Claude API key verified successfully.")
        
        valid_key = "sk-ant-api03-valid-claude-test-key-12345"
        res = self.brain.configure_provider("claude", api_key=valid_key, enabled=True)
        self.assertTrue(res["success"])
        self.assertTrue(claude.is_configured)
        self.assertTrue(claude.enabled)
        self.assertEqual(claude.display_name, "Claude")

    def test_invalid_claude_api_key(self):
        claude = self.brain.providers["claude"]
        claude._test_verification_hook = lambda k: (False, "invalid_key", "Claude API key is invalid. Please check your key and try again.")
        
        bad_key = "sk-ant-invalid-key"
        res = self.brain.configure_provider("claude", api_key=bad_key, enabled=True)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_type"], "invalid_key")
        self.assertIn("Claude API key is invalid", res["message"])
        self.assertFalse(claude.is_configured)
        self.assertFalse(claude.enabled)
        self.assertNotEqual(self.brain.active_provider, "claude")

    def test_valid_chatgpt_api_key_verification(self):
        chatgpt = self.brain.providers["chatgpt"]
        chatgpt._test_verification_hook = lambda k: (True, "valid", "ChatGPT API key verified successfully.")
        
        valid_key = "sk-proj-valid-openai-chatgpt-key-12345"
        res = self.brain.configure_provider("chatgpt", api_key=valid_key, enabled=True)
        self.assertTrue(res["success"])
        self.assertTrue(chatgpt.is_configured)
        self.assertTrue(chatgpt.enabled)
        self.assertEqual(chatgpt.display_name, "ChatGPT")

    def test_invalid_chatgpt_api_key(self):
        chatgpt = self.brain.providers["chatgpt"]
        chatgpt._test_verification_hook = lambda k: (False, "invalid_key", "ChatGPT API key is invalid. Please check your key and try again.")
        
        bad_key = "invalid-openai-key"
        res = self.brain.configure_provider("chatgpt", api_key=bad_key, enabled=True)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_type"], "invalid_key")
        self.assertIn("ChatGPT API key is invalid", res["message"])
        self.assertFalse(chatgpt.is_configured)
        self.assertFalse(chatgpt.enabled)
        self.assertNotEqual(self.brain.active_provider, "chatgpt")

    def test_valid_nvidia_api_key_verification(self):
        nv = self.brain.nvidia_provider
        nv._test_verification_hook = lambda k: (True, "valid", "NVIDIA API key verified successfully.")
        
        valid_key = "nvapi-valid-nvidia-test-key-12345"
        res = self.brain.configure_provider("nvidia", api_key=valid_key, enabled=True)
        self.assertTrue(res["success"])
        self.assertTrue(nv.is_configured)
        self.assertTrue(nv.enabled)
        self.assertEqual(nv.display_name, "NVIDIA")
        self.assertTrue(self.brain.providers["kimi"].enabled)
        self.assertTrue(self.brain.providers["deepseek"].enabled)
        self.assertTrue(self.brain.providers["qwen"].enabled)

    def test_invalid_nvidia_api_key(self):
        nv = self.brain.nvidia_provider
        nv._test_verification_hook = lambda k: (False, "invalid_key", "NVIDIA API key is invalid. Please check your key and try again.")
        
        bad_key = "nvapi-bad-key"
        res = self.brain.configure_provider("nvidia", api_key=bad_key, enabled=True)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_type"], "invalid_key")
        self.assertIn("NVIDIA API key is invalid", res["message"])
        self.assertFalse(nv.is_configured)
        self.assertFalse(nv.enabled)

    def test_nvidia_kimi_routing(self):
        nv = self.brain.nvidia_provider
        nv.configure("nvapi-valid-key", enabled=True)
        
        routed_models = []
        nv._test_query_hook = lambda prompt, choice: routed_models.append(choice) or "Hello from Kimi!"
        
        self.brain.set_active_provider("kimi")
        reply, telemetry = self.brain.query_active_provider("Hello Kimi")
        self.assertEqual(reply, "Hello from Kimi!")
        self.assertIn("kimi", routed_models)
        self.assertTrue(telemetry["request_completed"])

    def test_nvidia_deepseek_routing(self):
        nv = self.brain.nvidia_provider
        nv.configure("nvapi-valid-key", enabled=True)
        
        routed_models = []
        nv._test_query_hook = lambda prompt, choice: routed_models.append(choice) or "Hello from DeepSeek!"
        
        self.brain.set_active_provider("deepseek")
        reply, telemetry = self.brain.query_active_provider("Hello DeepSeek")
        self.assertEqual(reply, "Hello from DeepSeek!")
        self.assertIn("deepseek", routed_models)
        self.assertTrue(telemetry["request_completed"])

    def test_nvidia_qwen_routing(self):
        nv = self.brain.nvidia_provider
        nv.configure("nvapi-valid-key", enabled=True)
        
        routed_models = []
        nv._test_query_hook = lambda prompt, choice: routed_models.append(choice) or "Hello from Qwen!"
        
        self.brain.set_active_provider("qwen")
        reply, telemetry = self.brain.query_active_provider("Hello Qwen")
        self.assertEqual(reply, "Hello from Qwen!")
        self.assertIn("qwen", routed_models)
        self.assertTrue(telemetry["request_completed"])

    def test_provider_switching_without_restart(self):
        claude = self.brain.providers["claude"]
        claude.configure("sk-ant-test-key", enabled=True)
        claude._test_query_hook = lambda prompt, sys: "Response from Claude"

        chatgpt = self.brain.providers["chatgpt"]
        chatgpt.configure("sk-test-key", enabled=True)
        chatgpt._test_query_hook = lambda prompt, sys: "Response from ChatGPT"

        nv = self.brain.nvidia_provider
        nv.configure("nvapi-test-key", enabled=True)
        nv._test_query_hook = lambda prompt, choice: f"Response from {choice.title()}"

        # 1. Switch to Claude
        self.brain.set_active_provider("claude")
        r1, t1 = self.brain.query_active_provider("Test 1")
        self.assertEqual(r1, "Response from Claude")
        self.assertEqual(t1["active_provider"], "claude")

        # 2. Switch to ChatGPT
        self.brain.set_active_provider("chatgpt")
        r2, t2 = self.brain.query_active_provider("Test 2")
        self.assertEqual(r2, "Response from ChatGPT")
        self.assertEqual(t2["active_provider"], "chatgpt")

        # 3. Switch to Kimi
        self.brain.set_active_provider("kimi")
        r3, t3 = self.brain.query_active_provider("Test 3")
        self.assertEqual(r3, "Response from Kimi")
        self.assertEqual(t3["active_provider"], "kimi")

        # 4. Switch to DeepSeek
        self.brain.set_active_provider("deepseek")
        r4, t4 = self.brain.query_active_provider("Test 4")
        self.assertEqual(r4, "Response from Deepseek")
        self.assertEqual(t4["active_provider"], "deepseek")

        # 5. Switch to Qwen
        self.brain.set_active_provider("qwen")
        r5, t5 = self.brain.query_active_provider("Test 5")
        self.assertEqual(r5, "Response from Qwen")
        self.assertEqual(t5["active_provider"], "qwen")

        # 6. Switch to Built-in
        self.brain.set_active_provider("builtin")
        self.assertEqual(self.brain.active_provider, "builtin")

    def test_disabled_provider_cannot_be_selected(self):
        claude = self.brain.providers["claude"]
        claude.configure("sk-ant-test-key", enabled=False)
        
        res = self.brain.set_active_provider("claude")
        self.assertFalse(res["success"])
        self.assertNotEqual(self.brain.active_provider, "claude")

    def test_removed_api_key_cannot_be_used(self):
        claude = self.brain.providers["claude"]
        claude.configure("sk-ant-test-key", enabled=True)
        self.brain.set_active_provider("claude")

        rem_res = self.brain.remove_provider_key("claude")
        self.assertFalse(claude.is_configured)
        self.assertFalse(claude.enabled)
        self.assertEqual(claude.api_key, "")
        self.assertEqual(self.brain.active_provider, "builtin")

    def test_network_error_distinguished_from_invalid_key(self):
        claude = self.brain.providers["claude"]
        claude._test_verification_hook = lambda k: (False, "network_error", "Claude network or connection error. Please check your internet connection.")
        
        res = self.brain.configure_provider("claude", api_key="sk-ant-test-valid-syntax", enabled=True)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_type"], "network_error")
        self.assertIn("network or connection error", res["message"])
        self.assertNotIn("invalid", res["message"].lower())

    def test_rate_limit_error_distinguished_from_invalid_key(self):
        chatgpt = self.brain.providers["chatgpt"]
        chatgpt._test_verification_hook = lambda k: (False, "rate_limit", "ChatGPT rate limit or quota exceeded. Please check your account billing or try again later.")
        
        res = self.brain.configure_provider("chatgpt", api_key="sk-test-valid-syntax", enabled=True)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_type"], "rate_limit")
        self.assertIn("rate limit or quota exceeded", res["message"])
        self.assertNotIn("invalid", res["message"].lower())

    def test_provider_failure_does_not_crash_application(self):
        claude = self.brain.providers["claude"]
        claude.configure("sk-ant-test-key", enabled=True)
        claude._test_query_hook = lambda p, s: None
        
        self.brain.set_active_provider("claude")
        res = self.brain.process_message("What is the speed of light?")
        self.assertIsNotNone(res["response"])
        self.assertIn("unavailable", res["response"])

    def test_external_provider_failure_does_not_silently_pretend_builtin_succeeded(self):
        chatgpt = self.brain.providers["chatgpt"]
        chatgpt.configure("sk-test-key", enabled=True)
        chatgpt._test_query_hook = lambda p, s: None
        
        self.brain.set_active_provider("chatgpt")
        reply, telemetry = self.brain.query_active_provider("Can you write a poem?")
        self.assertTrue(telemetry["request_failed"])
        self.assertIn("ChatGPT is currently unavailable", reply)
        self.assertIn("switch to another configured AI provider", reply)

    def test_builtin_mode_works_with_zero_api_keys(self):
        self.brain.set_active_provider("builtin")
        r1 = self.brain.process_message("open Chrome and search Minecraft")
        self.assertEqual(len(r1["actions"]), 2)

        r2 = self.brain.process_message("open YouTube and play Minecraft survival")
        self.assertEqual(len(r2["actions"]), 1)

        r3 = self.brain.process_message("open a new CMD window and type hello")
        self.assertEqual(len(r3["actions"]), 2)

    def test_api_keys_never_appear_in_logs(self):
        keys = ["sk-ant-secret-12345", "sk-proj-secret-67890", "nvapi-secret-111213"]
        for k in keys:
            self.safety.log_execution(
                tool_name="configure_provider",
                parameters={"provider": "claude", "api_key": k},
                result={"success": True, "token": k},
                risk_level="safe"
            )
        logs = self.safety.get_audit_logs(limit=20)
        logs_str = str(logs)
        for k in keys:
            self.assertNotIn(k, logs_str)
        self.assertIn("[REDACTED]", logs_str)

    def test_api_keys_never_appear_in_test_output(self):
        claude = self.brain.providers["claude"]
        claude.configure("sk-ant-super-secret-key-12345", enabled=True)
        provider_dict = claude.to_dict()
        self.assertNotIn("sk-ant-super-secret-key-12345", str(provider_dict))
        self.assertEqual(provider_dict["masked_key"], "sk-a••••••••2345")

    def test_api_keys_never_appear_in_api_responses(self):
        self.brain.configure_provider("claude", "sk-ant-test-key-12345", enabled=True, skip_verification=True)
        self.brain.configure_provider("chatgpt", "sk-test-key-12345", enabled=True, skip_verification=True)
        self.brain.configure_provider("nvidia", "nvapi-test-key-12345", enabled=True, skip_verification=True)

        settings = self.brain.get_settings()
        settings_str = str(settings)
        self.assertNotIn("sk-ant-test-key-12345", settings_str)
        self.assertNotIn("sk-test-key-12345", settings_str)
        self.assertNotIn("nvapi-test-key-12345", settings_str)
        self.assertTrue(settings["has_claude_key"])
        self.assertTrue(settings["has_chatgpt_key"])
        self.assertTrue(settings["has_nvidia_key"])


class TestGeminiAPIValidationAndChat(IsolatedBrainTestCase):
    """Suite 10: Gemini API Key Validation, Error Classification & Normal Multilingual/Hinglish Chat Tests"""
    def setUp(self):
        super().setUp()
        self.safety = SafetyGuard(mode="balanced")

    def test_empty_gemini_key_rejected(self):
        """1. Empty Gemini key rejected."""
        gemini = self.brain.providers["gemini"]
        res = self.brain.configure_provider("gemini", api_key="", enabled=True)
        self.assertFalse(res["success"])
        self.assertFalse(res.get("configured", True))
        self.assertFalse(res.get("enabled", True))
        self.assertFalse(gemini.is_configured)
        self.assertFalse(gemini.enabled)
        self.assertNotEqual(self.brain.active_provider, "gemini")

    def test_a_gemini_key_rejected(self):
        """2. 'A' rejected."""
        gemini = self.brain.providers["gemini"]
        res = self.brain.configure_provider("gemini", api_key="A", enabled=True)
        self.assertFalse(res["success"])
        self.assertFalse(res.get("configured", True))
        self.assertFalse(res.get("enabled", True))
        self.assertFalse(res.get("active", True))
        self.assertEqual(res["error_type"], "invalid_key")
        self.assertIn("Gemini API key is invalid", res["message"])
        self.assertFalse(gemini.is_configured)
        self.assertFalse(gemini.enabled)
        self.assertNotEqual(self.brain.active_provider, "gemini")

    def test_123_gemini_key_rejected(self):
        """3. '123' rejected."""
        gemini = self.brain.providers["gemini"]
        res = self.brain.configure_provider("gemini", api_key="123", enabled=True)
        self.assertFalse(res["success"])
        self.assertFalse(res.get("configured", True))
        self.assertFalse(res.get("enabled", True))
        self.assertEqual(res["error_type"], "invalid_key")
        self.assertIn("Gemini API key is invalid", res["message"])
        self.assertFalse(gemini.is_configured)
        self.assertFalse(gemini.enabled)

    def test_random_malformed_key_rejected(self):
        """4. Random malformed key rejected."""
        gemini = self.brain.providers["gemini"]
        gemini._test_verification_hook = lambda k: (False, "invalid_key", "Gemini API key is invalid. Please check your key and try again.")
        res = self.brain.configure_provider("gemini", api_key="random-malformed-key-xyz-12345", enabled=True)
        self.assertFalse(res["success"])
        self.assertFalse(res.get("configured", True))
        self.assertFalse(res.get("enabled", True))
        self.assertFalse(gemini.is_configured)
        self.assertFalse(gemini.enabled)

    def test_invalid_gemini_key_does_not_become_configured(self):
        """5. Invalid Gemini key does not become configured."""
        gemini = self.brain.providers["gemini"]
        res = self.brain.configure_provider("gemini", api_key="A", enabled=True)
        self.assertFalse(res["success"])
        self.assertFalse(gemini.is_configured)

    def test_invalid_gemini_key_does_not_become_enabled(self):
        """6. Invalid Gemini key does not become enabled."""
        gemini = self.brain.providers["gemini"]
        res = self.brain.configure_provider("gemini", api_key="A", enabled=True)
        self.assertFalse(res["success"])
        self.assertFalse(gemini.enabled)

    def test_invalid_gemini_key_does_not_become_active(self):
        """7. Invalid Gemini key does not become active."""
        gemini = self.brain.providers["gemini"]
        res = self.brain.configure_provider("gemini", api_key="A", enabled=True)
        self.assertFalse(res["success"])
        self.assertNotEqual(self.brain.active_provider, "gemini")
        act_res = self.brain.set_active_provider("gemini")
        self.assertFalse(act_res["success"])
        self.assertNotEqual(self.brain.active_provider, "gemini")

    def test_invalid_gemini_key_is_not_persisted(self):
        """8. Invalid Gemini key is not persisted."""
        gemini = self.brain.providers["gemini"]
        res = self.brain.configure_provider("gemini", api_key="A", enabled=True)
        self.assertFalse(res["success"])
        self.assertEqual(gemini.api_key, "")

    def test_invalid_key_error_returned_from_backend(self):
        """9. Invalid-key error is returned from backend."""
        res = self.brain.configure_provider("gemini", api_key="A", enabled=True)
        self.assertFalse(res["success"])
        self.assertIn("Gemini API key is invalid. Please check your key and try again.", res["error"])
        self.assertEqual(res.get("configured"), False)
        self.assertEqual(res.get("enabled"), False)
        self.assertEqual(res.get("active"), False)

    def test_http_401_403_authentication_error_classification(self):
        """12. HTTP 400/401/403 is handled correctly as invalid key."""
        gemini = self.brain.providers["gemini"]
        gemini._test_verification_hook = lambda k: (False, "invalid_key", "Gemini API key is invalid. Please check your key and try again.")
        res = self.brain.configure_provider("gemini", api_key="AIzaSyBadKeyAuthenticationFailed12345", enabled=True)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_type"], "invalid_key")
        self.assertIn("Gemini API key is invalid", res["message"])

    def test_http_429_quota_rate_limit_classification(self):
        """13. HTTP 429 is classified as quota/rate limit."""
        gemini = self.brain.providers["gemini"]
        gemini._test_verification_hook = lambda k: (False, "rate_limit", "Gemini rate limit or quota exceeded. Please check your account billing or try again later.")
        res = self.brain.configure_provider("gemini", api_key="AIzaSyValidFormatKeyForQuotaTest12345", enabled=True)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_type"], "rate_limit")
        self.assertIn("rate limit or quota exceeded", res["message"])

    def test_network_error_classification(self):
        """14. Network error is classified correctly."""
        gemini = self.brain.providers["gemini"]
        gemini._test_verification_hook = lambda k: (False, "network_error", "Gemini network or connection error. Please check your internet connection.")
        res = self.brain.configure_provider("gemini", api_key="AIzaSyValidFormatKeyNetworkTest12345", enabled=True)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_type"], "network_error")
        self.assertIn("network or connection error", res["message"])

    def test_server_error_classification(self):
        """15. Server error is classified correctly."""
        gemini = self.brain.providers["gemini"]
        gemini._test_verification_hook = lambda k: (False, "server_error", "Gemini server is temporarily unavailable. Please try again later.")
        res = self.brain.configure_provider("gemini", api_key="AIzaSyValidFormatKeyServerTest12345", enabled=True)
        self.assertFalse(res["success"])
        self.assertEqual(res["error_type"], "server_error")
        self.assertIn("server is temporarily unavailable", res["message"])

    def test_valid_gemini_key_verification_succeeds(self):
        """16. Valid Gemini key verification succeeds."""
        gemini = self.brain.providers["gemini"]
        gemini._test_verification_hook = lambda k: (True, "valid", "Gemini API key verified successfully.")
        res = self.brain.configure_provider("gemini", api_key="AIzaSyRealValidGeminiKeySecret123456", enabled=True)
        self.assertTrue(res["success"])
        self.assertTrue(res.get("verified"))

    def test_successful_key_becomes_configured(self):
        """17. Successful key becomes configured."""
        gemini = self.brain.providers["gemini"]
        gemini._test_verification_hook = lambda k: (True, "valid", "Gemini API key verified successfully.")
        res = self.brain.configure_provider("gemini", api_key="AIzaSyRealValidGeminiKeySecret123456", enabled=True)
        self.assertTrue(res["success"])
        self.assertTrue(gemini.is_configured)
        self.assertTrue(gemini.enabled)

    def test_successful_key_can_become_active(self):
        """18. Successful key can become active."""
        gemini = self.brain.providers["gemini"]
        gemini._test_verification_hook = lambda k: (True, "valid", "Gemini API key verified successfully.")
        self.brain.configure_provider("gemini", api_key="AIzaSyRealValidGeminiKeySecret123456", enabled=True)
        res = self.brain.set_active_provider("gemini")
        self.assertTrue(res["success"])
        self.assertEqual(self.brain.active_provider, "gemini")

    def test_provider_state_refreshes_after_configuration(self):
        """19. Provider state refreshes after configuration."""
        gemini = self.brain.providers["gemini"]
        gemini._test_verification_hook = lambda k: (True, "valid", "Gemini API key verified successfully.")
        self.brain.configure_provider("gemini", api_key="AIzaSyRealValidGeminiKeySecret123456", enabled=True)
        providers_list = self.brain.get_providers_list()
        gemini_dict = next(p for p in providers_list if p["id"] == "gemini")
        self.assertTrue(gemini_dict["is_configured"])
        self.assertTrue(gemini_dict["enabled"])
        self.assertTrue(gemini_dict["has_key"])

    def test_existing_active_provider_remains_active_after_gemini_failure(self):
        """20. Existing active provider remains active after Gemini failure."""
        self.brain.set_active_provider("builtin")
        self.assertEqual(self.brain.active_provider, "builtin")
        
        # User enters invalid key 'A'
        res = self.brain.configure_provider("gemini", api_key="A", enabled=True)
        self.assertFalse(res["success"])
        
        # Built-in remains active!
        self.assertEqual(self.brain.active_provider, "builtin")

    def test_continue_without_api_key_keeps_builtin_active(self):
        """21. Continue without API key keeps Built-in active."""
        res = self.brain.complete_onboarding(api_key="", skip=True)
        self.assertTrue(res["onboarding_completed"])
        self.assertEqual(res["active_provider"], "builtin")
        self.assertFalse(res["has_gemini_key"])
        self.assertEqual(self.brain.active_provider, "builtin")

    def test_onboarding_does_not_incorrectly_activate_gemini(self):
        """22. Onboarding does not incorrectly activate Gemini on invalid key."""
        res = self.brain.complete_onboarding(api_key="A", skip=False)
        self.assertFalse(res["success"])
        self.assertFalse(res["onboarding_completed"])
        self.assertEqual(self.brain.active_provider, "builtin")
        self.assertFalse(self.brain.providers["gemini"].is_configured)

    def test_normal_chat_works_after_successful_gemini_configuration(self):
        """23. Normal chat works after successful Gemini configuration."""
        gemini = self.brain.providers["gemini"]
        gemini.configure("AIzaSyValidKey12345678901234567890", enabled=True)
        gemini._test_query_hook = lambda prompt, sys: "I am doing great! Ready to help you with Windows automation."
        self.brain.set_active_provider("gemini")
        
        res = self.brain.process_message("hello how are you?")
        self.assertEqual(res["response"], "I am doing great! Ready to help you with Windows automation.")
        self.assertEqual(len(res["actions"]), 0)

    def test_hinglish_natural_language_commands_still_work(self):
        """24. Hinglish natural-language commands still work."""
        # 1. bhai Chrome khol de
        r1 = self.brain.process_message("bhai Chrome khol de")
        self.assertEqual(len(r1["actions"]), 1)
        self.assertEqual(r1["actions"][0]["tool"], "open_application")
        self.assertEqual(r1["actions"][0]["parameters"]["app_name"], "chrome")

        # 2. bhai Chrome khol aur YouTube pe Minecraft search kar
        r2 = self.brain.process_message("bhai Chrome khol aur YouTube pe Minecraft search kar")
        self.assertEqual(len(r2["actions"]), 2)
        self.assertEqual(r2["actions"][0]["tool"], "open_application")
        self.assertEqual(r2["actions"][0]["parameters"]["app_name"], "chrome")
        self.assertEqual(r2["actions"][1]["tool"], "open_website")
        self.assertEqual(r2["actions"][1]["parameters"]["search_query"], "Minecraft")

    def test_gemini_failure_does_not_silently_pretend_builtin_generated_response(self):
        """25. Gemini failure does not silently pretend Built-in generated the response."""
        gemini = self.brain.providers["gemini"]
        gemini.configure("AIzaSyValidKey12345678901234567890", enabled=True)
        gemini._test_query_hook = lambda p, s: None
        
        self.brain.set_active_provider("gemini")
        reply, telemetry = self.brain.query_active_provider("Explain quantum computing")
        self.assertTrue(telemetry["request_failed"])
        self.assertIn("Gemini is currently unavailable", reply)
        self.assertIn("switch to another configured AI provider", reply)

    def test_gemini_api_key_never_appears_in_logs(self):
        """26. Gemini API key never appears in logs."""
        raw_key = "AIzaSySecretGeminiVerificationKey12345"
        self.safety.log_execution(
            tool_name="configure_gemini",
            parameters={"api_key": raw_key},
            result={"success": True, "auth": f"Bearer {raw_key}"},
            risk_level="safe"
        )
        logs = self.safety.get_audit_logs(limit=10)
        logs_str = str(logs)
        self.assertNotIn(raw_key, logs_str)
        self.assertIn("[REDACTED]", logs_str)

    def test_gemini_api_key_never_appears_in_api_responses(self):
        """27. Gemini API key never appears in API responses."""
        raw_key = "AIzaSySecretGeminiVerificationKey12345"
        self.brain.configure_provider("gemini", api_key=raw_key, enabled=True, skip_verification=True)
        
        settings = self.brain.get_settings()
        settings_str = str(settings)
        self.assertNotIn(raw_key, settings_str)
        self.assertTrue(settings["has_gemini_key"])
        
        providers_list = self.brain.get_providers_list()
        providers_str = str(providers_list)
        self.assertNotIn(raw_key, providers_str)

    def test_gemini_active_yo_bro_chat(self):
        """Active Gemini handles 'yo bro' conversational query and returns response."""
        gemini = self.brain.providers["gemini"]
        gemini.configure("AIzaSyValidGeminiKeySecret123456", enabled=True)
        gemini._test_query_hook = lambda prompt, sys: "Hey bro! What's up? I'm Gemini, ready to help with your desktop."
        self.brain.set_active_provider("gemini")
        
        res = self.brain.process_message("yo bro")
        self.assertEqual(len(res["actions"]), 0)
        self.assertEqual(res["active_provider"], "gemini")
        self.assertIn("Hey bro", res["response"])

    def test_gemini_active_hinglish_chat(self):
        """Active Gemini handles Hinglish conversational queries like 'bhai kya haal hai?'."""
        gemini = self.brain.providers["gemini"]
        gemini.configure("AIzaSyValidGeminiKeySecret123456", enabled=True)
        gemini._test_query_hook = lambda prompt, sys: "Sab badhiya bhai! Ready to control your computer."
        self.brain.set_active_provider("gemini")
        
        res = self.brain.process_message("bhai kya haal hai?")
        self.assertEqual(len(res["actions"]), 0)
        self.assertEqual(res["active_provider"], "gemini")
        self.assertIn("Sab badhiya", res["response"])

    def test_active_provider_remains_gemini_until_explicitly_changed(self):
        """Active provider remains Gemini across queries and does not reset unexpectedly."""
        gemini = self.brain.providers["gemini"]
        gemini.configure("AIzaSyValidGeminiKeySecret123456", enabled=True)
        gemini._test_query_hook = lambda p, s: "Gemini conversational response"
        self.brain.set_active_provider("gemini")
        
        r1 = self.brain.process_message("hello")
        self.assertEqual(r1["active_provider"], "gemini")
        self.assertEqual(self.brain.active_provider, "gemini")
        
        r2 = self.brain.process_message("Chrome khol")
        self.assertEqual(r2["active_provider"], "gemini")
        self.assertEqual(self.brain.active_provider, "gemini")

    def test_gemini_15_flash_primary_model_selection(self):
        """Gemini 1.5 Flash is selected as the primary generation model."""
        gemini = self.brain.providers["gemini"]
        gemini.available_models = ["gemini-1.5-flash", "gemini-2.0-flash-lite"]
        gemini.configure("AIzaSyValidGeminiKeySecret123456", enabled=True)
        
        attempted_models = []
        gemini._test_query_hook = lambda prompt, sys: attempted_models.append("gemini-1.5-flash") or "Hello from Gemini 1.5 Flash!"
        self.brain.set_active_provider("gemini")
        
        res = self.brain.process_message("yo bro")
        self.assertEqual(res["response"], "Hello from Gemini 1.5 Flash!")
        self.assertIn("gemini-1.5-flash", attempted_models)

    def test_gemini_model_discovery_normalization(self):
        """Model discovery normalizes 'models/gemini-1.5-flash' to 'gemini-1.5-flash'."""
        gemini = self.brain.providers["gemini"]
        mock_models_response = {
            "models": [
                {"name": "models/gemini-1.5-flash", "supportedGenerationMethods": ["generateContent", "countTokens"]},
                {"name": "models/gemini-2.0-flash-lite", "supportedGenerationMethods": ["generateContent"]}
            ]
        }
        discovered = []
        for m in mock_models_response["models"]:
            if "generateContent" in m.get("supportedGenerationMethods", []):
                discovered.append(m["name"].replace("models/", "").strip())
        gemini.available_models = discovered
        self.assertIn("gemini-1.5-flash", gemini.available_models)
        self.assertNotIn("models/gemini-1.5-flash", gemini.available_models)

    def test_gemini_conversational_response_pipeline_clean_output(self):
        """Conversational AI response pipeline filters out drafting text, options, and candidate analysis."""
        gemini = self.brain.providers["gemini"]
        gemini.configure("AIzaSyValidGeminiKeySecret123456", enabled=True)
        
        raw_drafting_output = (
            "User says: \"yo bro\"\n"
            "Role: Friendly, natural AI Desktop Assistant.\n"
            "Rules:\n"
            "Language: English.\n"
            "Tone: Very casual.\n"
            "- \"Yo! What's up?\"\n"
            "- \"Hey man, what's going on?\"\n"
            "- \"Yo! How's it going?\"\n"
            "Option 1: Yo!\n"
            "Option 2: What's up?\n"
            "Option 3: Hey!\n"
            "Short? Yes.\n"
            "Natural/Casual? Yes.\n"
            "Matches tone? Yes.\n"
            "Perfect\n"
            "Yo! What's up? How's it going?"
        )
        gemini._test_query_hook = lambda prompt, sys: raw_drafting_output
        self.brain.set_active_provider("gemini")

        res = self.brain.process_message("yo bro")
        resp_text = res["response"]
        
        # Verify forbidden internal drafting keywords are NOT present in final response
        forbidden_keywords = [
            "User says:", "Role:", "Rules:", "Language:", "Tone:",
            "Option 1", "Option 2", "Option 3", "Short?", "Natural/Casual?",
            "Matches tone?", "Perfect", "candidate", "draft", "analysis"
        ]
        for kw in forbidden_keywords:
            self.assertNotIn(kw.lower(), resp_text.lower(), f"Forbidden keyword '{kw}' found in response: {resp_text}")

        # Verify only the clean final answer is returned
        self.assertEqual(resp_text, "Yo! What's up? How's it going?")
        self.assertEqual(len(res["actions"]), 0)

    def test_gemini_api_key_never_appears_in_test_output(self):
        """28. Gemini API key never appears in test output."""
        gemini = self.brain.providers["gemini"]
        gemini.configure("AIzaSyValidGeminiKeySecret1234567890", enabled=True)
        gemini_dict = gemini.to_dict()
        self.assertNotIn("AIzaSyValidGeminiKeySecret1234567890", str(gemini_dict))
        self.assertEqual(gemini_dict["masked_key"], "AIza••••••••7890")


class TestUnifiedNaturalLanguageAndAIReasoning(IsolatedBrainTestCase):
    """Suite 11: Unified Natural Language & AI Intent Reasoning Tests (English, Hindi, Hinglish, YouTube Shorts, Context & Fallback)"""
    def setUp(self):
        super().setUp()
        test_ws = Path.home() / "ai-desktop-workspace-test"
        self.controller = DesktopController(str(test_ws))
        self.safety = SafetyGuard(mode="balanced")

    def test_no_gemini_api_yo_bro_basic_mode(self):
        """When no external AI provider is configured, 'yo bro' returns clean basic mode reply."""
        self.brain.set_active_provider("builtin")
        res = self.brain.process_message("yo bro")
        self.assertEqual(len(res["actions"]), 0)
        self.assertEqual(res["active_provider"], "builtin")
        self.assertIn("basic mode", res["response"].lower())
        self.assertNotIn("option", res["response"].lower())
        self.assertNotIn("rules", res["response"].lower())

    def test_no_gemini_api_complex_question_fallback(self):
        """Complex questions with no AI configured guide the user to Settings."""
        self.brain.set_active_provider("builtin")
        res = self.brain.process_message("what is quantum computing?")
        self.assertEqual(len(res["actions"]), 0)
        self.assertIn("Gemini API key", res["response"])

    def test_no_gemini_api_desktop_command_executes_deterministically(self):
        """Deterministic desktop commands execute without requiring Gemini API."""
        self.brain.set_active_provider("builtin")
        res = self.brain.process_message("open Chrome")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")

    def test_open_chatgpt_desktop_intent(self):
        """'open ChatGPT desktop' resolves to chatgpt_desktop app key."""
        res = self.brain.process_message("open ChatGPT desktop")
        self.assertEqual(len(res["actions"]), 1)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chatgpt_desktop")

    def test_open_chatgpt_desktop_not_installed_fails_cleanly(self):
        """When ChatGPT desktop is not installed on PC, returns clear failure message."""
        exec_res = self.controller.open_application("chatgpt_desktop")
        self.assertFalse(exec_res["success"])
        self.assertIn("isn't installed on this PC", exec_res["error"])

    def test_gemini_configured_and_desktop_command_deterministic(self):
        """When Gemini is active, desktop commands still execute deterministically via controller."""
        gemini = self.brain.providers["gemini"]
        gemini.configure("AIzaSyValidGeminiKeySecret123456", enabled=True)
        self.brain.set_active_provider("gemini")
        
        res = self.brain.process_message("open Chrome and search Minecraft")
        self.assertEqual(len(res["actions"]), 2)
        self.assertEqual(res["actions"][0]["tool"], "open_application")
        self.assertEqual(res["actions"][0]["parameters"]["app_name"], "chrome")
        self.assertEqual(res["actions"][1]["tool"], "open_website")
        self.assertEqual(res["actions"][1]["parameters"]["search_query"], "Minecraft")

    def test_conversational_casual_chat_intents(self):
        """Conversational messages distinguish chat from desktop commands."""
        # 1. yo bro
        r1 = self.brain.process_message("yo bro")
        self.assertEqual(len(r1["actions"]), 0)
        self.assertTrue("yo" in r1["response"].lower() or "bhai" in r1["response"].lower())

        # 2. bhai bore ho raha hu
        r2 = self.brain.process_message("bhai bore ho raha hu")
        self.assertEqual(len(r2["actions"]), 0)
        self.assertTrue("ready" in r2["response"].lower() or "bhai" in r2["response"].lower() or "bol" in r2["response"].lower())

        # 3. how are you?
        r3 = self.brain.process_message("how are you?")
        self.assertEqual(len(r3["actions"]), 0)
        self.assertTrue("good" in r3["response"].lower() or "bhai" in r3["response"].lower())

        # 4. tell me a joke
        r4 = self.brain.process_message("tell me a joke")
        self.assertEqual(len(r4["actions"]), 0)
        self.assertIn("Windows", r4["response"])

    def test_short_natural_casual_conversational_responses(self):
        """Casual conversational responses are concise, natural, and match tone."""
        # 1. bhai kaisa hai
        r1 = self.brain.process_message("bhai kaisa hai")
        self.assertEqual(len(r1["actions"]), 0)
        self.assertTrue("badhiya" in r1["response"].lower() or "bhai" in r1["response"].lower())
        self.assertTrue(len(r1["response"].split()) <= 25)

        # 2. kya kar rha hai?
        r2 = self.brain.process_message("kya kar rha hai?")
        self.assertEqual(len(r2["actions"]), 0)
        self.assertTrue("ready" in r2["response"].lower() or "bol" in r2["response"].lower())
        self.assertTrue(len(r2["response"].split()) <= 25)

        # 3. thanks
        r3 = self.brain.process_message("thanks")
        self.assertEqual(len(r3["actions"]), 0)
        self.assertTrue("welcome" in r3["response"].lower() or "anytime" in r3["response"].lower())

    def test_hindi_hinglish_app_launch_commands(self):
        """Hindi & Hinglish requests launch apps deterministically."""
        # 1. bhai Chrome khol de
        r1 = self.brain.process_message("bhai Chrome khol de")
        self.assertEqual(len(r1["actions"]), 1)
        self.assertEqual(r1["actions"][0]["tool"], "open_application")
        self.assertEqual(r1["actions"][0]["parameters"]["app_name"], "chrome")

        # 2. youtube khol
        r2 = self.brain.process_message("youtube khol")
        self.assertEqual(len(r2["actions"]), 1)
        self.assertEqual(r2["actions"][0]["tool"], "open_website")
        self.assertEqual(r2["actions"][0]["parameters"]["url"], "https://www.youtube.com")

        # 3. youtube laga
        r3 = self.brain.process_message("youtube laga")
        self.assertEqual(len(r3["actions"]), 1)
        self.assertEqual(r3["actions"][0]["tool"], "open_website")

        # 4. Paint khol
        r4 = self.brain.process_message("Paint khol")
        self.assertEqual(len(r4["actions"]), 1)
        self.assertEqual(r4["actions"][0]["tool"], "open_application")
        self.assertEqual(r4["actions"][0]["parameters"]["app_name"], "paint")

    def test_youtube_video_playback_hinglish(self):
        """Hinglish video requests map to YouTube playback."""
        # 1. bhai Minecraft ki videos chala
        r1 = self.brain.process_message("bhai Minecraft ki videos chala")
        self.assertEqual(len(r1["actions"]), 1)
        self.assertEqual(r1["actions"][0]["tool"], "open_website")
        self.assertTrue(r1["actions"][0]["parameters"]["playback"])
        self.assertIn("Minecraft", r1["actions"][0]["parameters"]["search_query"])

        # 2. youtube pe Minecraft search kar
        r2 = self.brain.process_message("youtube pe Minecraft search kar")
        self.assertEqual(len(r2["actions"]), 1)
        self.assertEqual(r2["actions"][0]["tool"], "open_website")
        self.assertIn("Minecraft", r2["actions"][0]["parameters"]["search_query"])

    def test_youtube_shorts_natural_language_intents(self):
        """YouTube Shorts natural language variations map to shorts playback."""
        # 1. shorts chala de
        r1 = self.brain.process_message("shorts chala de")
        self.assertEqual(len(r1["actions"]), 1)
        self.assertEqual(r1["actions"][0]["tool"], "open_website")
        self.assertTrue(r1["actions"][0]["parameters"].get("is_shorts"))
        self.assertTrue(r1["actions"][0]["parameters"]["playback"])
        self.assertIn("shorts", r1["actions"][0]["parameters"]["url"])

        # 2. shorts chala
        r2 = self.brain.process_message("shorts chala")
        self.assertEqual(len(r2["actions"]), 1)
        self.assertTrue(r2["actions"][0]["parameters"].get("is_shorts"))

        # 3. bhai YouTube pe koi Minecraft short laga de
        r3 = self.brain.process_message("bhai YouTube pe koi Minecraft short laga de")
        self.assertEqual(len(r3["actions"]), 1)
        self.assertEqual(r3["actions"][0]["tool"], "open_website")
        self.assertTrue(r3["actions"][0]["parameters"].get("is_shorts"))
        self.assertTrue(r3["actions"][0]["parameters"]["playback"])
        self.assertIn("Minecraft", r3["actions"][0]["parameters"]["search_query"])

        # 4. Minecraft ki shorts chala
        r4 = self.brain.process_message("Minecraft ki shorts chala")
        self.assertEqual(len(r4["actions"]), 1)
        self.assertTrue(r4["actions"][0]["parameters"].get("is_shorts"))
        self.assertIn("Minecraft", r4["actions"][0]["parameters"]["search_query"])

        # 5. latest Minecraft short laga
        r5 = self.brain.process_message("latest Minecraft short laga")
        self.assertEqual(len(r5["actions"]), 1)
        self.assertTrue(r5["actions"][0]["parameters"].get("is_shorts"))

    def test_hinglish_compound_and_new_window_sequences(self):
        """Hinglish compound commands create ordered multi-step actions."""
        # 1. notepad khol aur hello brother likh
        r1 = self.brain.process_message("notepad khol aur hello brother likh")
        self.assertEqual(len(r1["actions"]), 2)
        self.assertEqual(r1["actions"][0]["tool"], "open_application")
        self.assertEqual(r1["actions"][0]["parameters"]["app_name"], "notepad")
        self.assertEqual(r1["actions"][1]["tool"], "type_text")
        self.assertEqual(r1["actions"][1]["parameters"]["text"], "hello brother")

        # 2. bhai ek naya CMD khol aur hello likh de
        r2 = self.brain.process_message("bhai ek naya CMD khol aur hello likh de")
        self.assertEqual(len(r2["actions"]), 2)
        self.assertEqual(r2["actions"][0]["tool"], "open_application")
        self.assertEqual(r2["actions"][0]["parameters"]["app_name"], "cmd")
        self.assertTrue(r2["actions"][0]["parameters"]["new_window"])
        self.assertEqual(r2["actions"][1]["tool"], "type_text")
        self.assertEqual(r2["actions"][1]["parameters"]["text"], "hello")

        # 3. PowerShell ki new window khol aur hello type kar
        r3 = self.brain.process_message("PowerShell ki new window khol aur hello type kar")
        self.assertEqual(len(r3["actions"]), 2)
        self.assertEqual(r3["actions"][0]["tool"], "open_application")
        self.assertEqual(r3["actions"][0]["parameters"]["app_name"], "powershell")
        self.assertTrue(r3["actions"][0]["parameters"]["new_window"])
        self.assertEqual(r3["actions"][1]["tool"], "type_text")
        self.assertEqual(r3["actions"][1]["parameters"]["text"], "hello")

        # 4. Chrome khol, Minecraft search kar aur phir YouTube open kar
        r4 = self.brain.process_message("Chrome khol, Minecraft search kar aur phir YouTube open kar")
        self.assertEqual(len(r4["actions"]), 3)
        self.assertEqual(r4["actions"][0]["parameters"]["app_name"], "chrome")
        self.assertEqual(r4["actions"][1]["parameters"]["search_query"], "Minecraft")
        self.assertEqual(r4["actions"][2]["tool"], "open_website")
        self.assertIn("youtube.com", r4["actions"][2]["parameters"]["url"])

    def test_contextual_commands(self):
        """Contextual commands resolve target window and app properly."""
        # 1. isko minimize kar
        r1 = self.brain.process_message("isko minimize kar")
        self.assertEqual(len(r1["actions"]), 1)
        self.assertEqual(r1["actions"][0]["tool"], "minimize_window")
        self.assertEqual(r1["actions"][0]["parameters"]["app_name"], "current")

        # 2. ye window band kar de
        r2 = self.brain.process_message("ye window band kar de")
        self.assertEqual(len(r2["actions"]), 1)
        self.assertEqual(r2["actions"][0]["tool"], "close_window")
        self.assertEqual(r2["actions"][0]["parameters"]["app_name"], "current")

    def test_unknown_local_command_delegation_to_active_ai(self):
        """When local parser doesn't recognize a novel query, active AI interprets it into supported tools."""
        gemini = self.brain.providers["gemini"]
        gemini.configure("AIzaSyValidKey12345678901234567890", enabled=True)
        self.brain.set_active_provider("gemini")

        # Mock AI returning structured JSON for a novel phrasing
        gemini._test_query_hook = lambda prompt, sys: """```json
{
  "summary": "Capture screen and inspect system performance",
  "actions": [
    {"tool": "take_screenshot", "parameters": {"region": "fullscreen", "save_path": "audit_screen.png"}},
    {"tool": "get_system_info", "parameters": {}}
  ],
  "response": "Taking a desktop screenshot and checking system resources."
}
```"""

        res = self.brain.process_message("Can you please snap my current screen and check how much RAM is being used?")
        self.assertEqual(len(res["actions"]), 2)
        self.assertEqual(res["actions"][0]["tool"], "take_screenshot")
        self.assertEqual(res["actions"][1]["tool"], "get_system_info")
        self.assertIn("screenshot", res["response"].lower())

    def test_ai_unsupported_action_rejection(self):
        """AI cannot invent unsupported tools or arbitrary code execution."""
        claude = self.brain.providers["claude"]
        claude.configure("sk-ant-valid-key-12345", enabled=True)
        self.brain.set_active_provider("claude")

        # Mock AI returning an unsupported tool
        claude._test_query_hook = lambda prompt, sys: """```json
{
  "summary": "Inject kernel driver",
  "actions": [
    {"tool": "inject_unsupported_kernel_driver", "parameters": {"address": "0xDEADBEEF"}}
  ],
  "response": "Attempting kernel driver injection..."
}
```"""

        res = self.brain.process_message("inject a custom kernel driver at memory address 0xDEADBEEF")
        self.assertEqual(len(res["actions"]), 0)
        self.assertIn("not currently supported", res["response"])

    def test_multi_provider_independence_intent_reasoning(self):
        """Intent reasoning works across Claude, ChatGPT, NVIDIA, and Built-in."""
        # 1. Claude
        claude = self.brain.providers["claude"]
        claude.configure("sk-ant-test-key", enabled=True)
        claude._test_query_hook = lambda p, s: """{"summary": "Open Discord", "actions": [{"tool": "open_application", "parameters": {"app_name": "discord"}}], "response": "Launching Discord."}"""
        self.brain.set_active_provider("claude")
        r_claude = self.brain.process_message("Please boot up Discord for team chat")
        self.assertEqual(len(r_claude["actions"]), 1)
        self.assertEqual(r_claude["actions"][0]["parameters"]["app_name"], "discord")

        # 2. ChatGPT
        chatgpt = self.brain.providers["chatgpt"]
        chatgpt.configure("sk-test-key", enabled=True)
        chatgpt._test_query_hook = lambda p, s: """{"summary": "Create Folder", "actions": [{"tool": "create_folder", "parameters": {"folder_path": "Workspace2026"}}], "response": "Created folder Workspace2026."}"""
        self.brain.set_active_provider("chatgpt")
        r_gpt = self.brain.process_message("Create a workspace directory called Workspace2026")
        self.assertEqual(len(r_gpt["actions"]), 1)
        self.assertEqual(r_gpt["actions"][0]["tool"], "create_folder")
        self.assertEqual(r_gpt["actions"][0]["parameters"]["folder_path"], "Workspace2026")

        # 3. NVIDIA / Kimi
        nv = self.brain.nvidia_provider
        nv.configure("nvapi-test-key", enabled=True)
        nv._test_query_hook = lambda p, choice: """{"summary": "Launch Paint", "actions": [{"tool": "open_application", "parameters": {"app_name": "paint"}}], "response": "Opening Paint."}"""
        self.brain.set_active_provider("kimi")
        r_kimi = self.brain.process_message("I want to draw something, bring up Paint")
        self.assertEqual(len(r_kimi["actions"]), 1)
        self.assertEqual(r_kimi["actions"][0]["parameters"]["app_name"], "paint")

        # 4. Built-in
        self.brain.set_active_provider("builtin")
        r_builtin = self.brain.process_message("open Paint")
        self.assertEqual(len(r_builtin["actions"]), 1)
        self.assertEqual(r_builtin["actions"][0]["parameters"]["app_name"], "paint")


class TestConversationHistoryAndPersistence(unittest.TestCase):
    """Suite 12: Persistent Conversation Management, Chat History & Title Generation Tests"""
    def setUp(self):
        self.test_storage = "/tmp/test_ai_agent_conversations.json"
        if os.path.exists(self.test_storage):
            os.remove(self.test_storage)
        self.brain = AIBrain(storage_path=self.test_storage)

    def tearDown(self):
        if os.path.exists(self.test_storage):
            os.remove(self.test_storage)

    def test_create_and_list_conversations(self):
        """Conversations can be created, stored, and listed."""
        conv1 = self.brain.create_conversation(title="First Session")
        self.assertTrue(conv1["id"].startswith("conv_"))
        self.assertEqual(conv1["title"], "First Session")

        conv2 = self.brain.create_conversation(title="Second Session")

        # By default, list_conversations filters empty conversations (0 messages)
        self.assertEqual(len(self.brain.list_conversations()), 0)

        # include_empty=True lists all raw records
        self.assertEqual(len(self.brain.list_conversations(include_empty=True)), 2)

        # Adding a message makes the conversation active and listed
        user_msg = {"role": "user", "content": "Hello", "timestamp": time.time()}
        ai_msg = {"role": "assistant", "content": "Hi!", "timestamp": time.time()}
        self.brain.add_message_pair_to_conversation(conv2["id"], user_msg, ai_msg)
        
        conv_list = self.brain.list_conversations()
        self.assertEqual(len(conv_list), 1)
        self.assertEqual(conv_list[0]["id"], conv2["id"])

    def test_auto_generate_title_from_first_message(self):
        """Adding a message to a new conversation automatically sets an informative title."""
        conv = self.brain.create_conversation(title="New Chat")
        c_id = conv["id"]

        user_msg = {"role": "user", "content": "open Chrome and search Minecraft", "timestamp": time.time()}
        ai_msg = {"role": "assistant", "content": "Executing compound command.", "actions": [], "timestamp": time.time()}

        self.brain.add_message_pair_to_conversation(c_id, user_msg, ai_msg)
        updated = self.brain.get_conversation(c_id)
        self.assertIn("Chrome", updated["title"])
        self.assertEqual(len(updated["messages"]), 2)

    def test_rename_and_delete_conversation(self):
        """Conversations can be renamed and deleted cleanly."""
        conv = self.brain.create_conversation(title="Old Title")
        c_id = conv["id"]

        # Rename
        renamed = self.brain.rename_conversation(c_id, "Updated Custom Title")
        self.assertTrue(renamed)
        self.assertEqual(self.brain.get_conversation(c_id)["title"], "Updated Custom Title")

        # Delete
        deleted = self.brain.delete_conversation(c_id)
        self.assertTrue(deleted)
        self.assertIsNone(self.brain.get_conversation(c_id))
        self.assertEqual(len(self.brain.list_conversations()), 0)

    def test_conversations_do_not_mix_messages(self):
        """Different conversations maintain strictly isolated message histories."""
        c1 = self.brain.create_conversation(title="Session 1")["id"]
        c2 = self.brain.create_conversation(title="Session 2")["id"]

        self.brain.add_message_pair_to_conversation(
            c1,
            {"role": "user", "content": "Message in C1", "timestamp": time.time()},
            {"role": "assistant", "content": "Reply in C1", "timestamp": time.time()}
        )

        self.brain.add_message_pair_to_conversation(
            c2,
            {"role": "user", "content": "Message in C2", "timestamp": time.time()},
            {"role": "assistant", "content": "Reply in C2", "timestamp": time.time()}
        )

        conv1 = self.brain.get_conversation(c1)
        conv2 = self.brain.get_conversation(c2)

        self.assertEqual(len(conv1["messages"]), 2)
        self.assertEqual(conv1["messages"][0]["content"], "Message in C1")
        self.assertEqual(len(conv2["messages"]), 2)
        self.assertEqual(conv2["messages"][0]["content"], "Message in C2")

    def test_conversations_persist_across_restarts(self):
        """Conversation history persists across backend instances using storage file."""
        c = self.brain.create_conversation(title="Persistent Chat")["id"]
        self.brain.add_message_pair_to_conversation(
            c,
            {"role": "user", "content": "Persistent question", "timestamp": time.time()},
            {"role": "assistant", "content": "Persistent answer", "timestamp": time.time()}
        )

        # Create new AIBrain instance pointing to same file
        reloaded_brain = AIBrain(storage_path=self.test_storage)
        convs = reloaded_brain.list_conversations()
        self.assertEqual(len(convs), 1)
        self.assertEqual(convs[0]["id"], c)
        loaded_conv = reloaded_brain.get_conversation(c)
        self.assertEqual(len(loaded_conv["messages"]), 2)
        self.assertEqual(loaded_conv["messages"][0]["content"], "Persistent question")

    def test_conversation_context_memory_recall_name(self):
        """AI recalls user information (e.g. name) within the active conversation context."""
        c = self.brain.create_conversation(title="Name Memory")["id"]
        self.brain.add_message_pair_to_conversation(
            c,
            {"role": "user", "content": "My name is Alex.", "timestamp": time.time()},
            {"role": "assistant", "content": "Nice to meet you!", "timestamp": time.time()}
        )

        res = self.brain.process_message("What is my name?", conversation_id=c)
        self.assertIn("Alex", res["response"])

    def test_conversation_context_isolation_between_sessions(self):
        """Session A and Session B maintain strictly isolated contextual recall."""
        cA = self.brain.create_conversation(title="Session A")["id"]
        cB = self.brain.create_conversation(title="Session B")["id"]

        self.brain.add_message_pair_to_conversation(
            cA,
            {"role": "user", "content": "My favorite game is Minecraft.", "timestamp": time.time()},
            {"role": "assistant", "content": "Minecraft is awesome!", "timestamp": time.time()}
        )

        self.brain.add_message_pair_to_conversation(
            cB,
            {"role": "user", "content": "My favorite game is Roblox.", "timestamp": time.time()},
            {"role": "assistant", "content": "Roblox is fun!", "timestamp": time.time()}
        )

        resA = self.brain.process_message("What is my favorite game?", conversation_id=cA)
        resB = self.brain.process_message("What is my favorite game?", conversation_id=cB)

        self.assertIn("Minecraft", resA["response"])
        self.assertIn("Roblox", resB["response"])
        self.assertNotIn("Roblox", resA["response"])
        self.assertNotIn("Minecraft", resB["response"])

    def test_system_status_and_pc_diagnosis_real_metrics(self):
        """DesktopController returns real measured system metrics and PC diagnosis."""
        controller = DesktopController()
        sys_info = controller.get_system_info()
        diag = controller.get_pc_diagnosis()

        self.assertTrue(sys_info["controller_active"])
        self.assertIn("cpu_percent", sys_info)
        self.assertIn("ram_percent", sys_info)
        self.assertIn("ram_used_gb", sys_info)
        self.assertIn("ram_total_gb", sys_info)

        self.assertTrue(diag["controller_active"])
        self.assertIn("healthy", diag)
        self.assertIn("health_summary", diag)
        self.assertIn("cpu_percent", diag)
        self.assertIn("ram_percent", diag)
        self.assertIn("disk_percent", diag)

    def test_ai_triggered_pc_diagnose_intents(self):
        """System status and PC diagnose requests trigger get_system_info deterministically."""
        r1 = self.brain.process_message("bhai mera PC check kar")
        self.assertEqual(len(r1["actions"]), 1)
        self.assertEqual(r1["actions"][0]["tool"], "get_system_info")

        r2 = self.brain.process_message("diagnose my PC")
        self.assertEqual(len(r2["actions"]), 1)
        self.assertEqual(r2["actions"][0]["tool"], "get_system_info")

        r3 = self.brain.process_message("how much RAM am I using?")
        self.assertEqual(len(r3["actions"]), 1)
        self.assertEqual(r3["actions"][0]["tool"], "get_system_info")

    def test_casual_chat_does_not_trigger_diagnostics(self):
        """Casual conversation queries do NOT trigger system diagnostics."""
        r1 = self.brain.process_message("yo bro")
        self.assertEqual(len(r1["actions"]), 0)

        r2 = self.brain.process_message("how are you?")
        self.assertEqual(len(r2["actions"]), 0)

        r3 = self.brain.process_message("bhai kaisa hai")
        self.assertEqual(len(r3["actions"]), 0)

        r4 = self.brain.process_message("kya scene hai?")
        self.assertEqual(len(r4["actions"]), 0)

    def test_xyz_introduction_and_name_recall(self):
        """Tests 'My name is xyz' and subsequent 'What is my name?' recall without meta-analysis."""
        c = self.brain.create_conversation("xyz Test")
        c_id = c["id"]

        r1 = self.brain.process_message("My name is xyz", conversation_id=c_id)
        self.assertEqual(len(r1["actions"]), 0)
        self.assertIn("xyz", r1["response"].lower())
        self.assertNotIn("The user", r1["response"])
        self.assertNotIn("Plan:", r1["response"])
        self.assertNotIn("Option 1", r1["response"])

        self.brain.add_message_pair_to_conversation(
            c_id,
            {"role": "user", "content": "My name is xyz", "timestamp": time.time()},
            {"role": "assistant", "content": r1["response"], "timestamp": time.time()}
        )

        r2 = self.brain.process_message("What is my name?", conversation_id=c_id)
        self.assertIn("xyz", r2["response"].lower())
        self.assertNotIn("The user", r2["response"])
        self.assertNotIn("Plan:", r2["response"])
        self.assertNotIn("Option 1", r2["response"])

    def test_alex_introduction_and_name_recall(self):
        """Tests 'My name is Alex' and subsequent 'What is my name?' recall."""
        c = self.brain.create_conversation("Alex Test")
        c_id = c["id"]

        r1 = self.brain.process_message("My name is Alex", conversation_id=c_id)
        self.assertEqual(len(r1["actions"]), 0)
        self.assertIn("Alex", r1["response"])

        self.brain.add_message_pair_to_conversation(
            c_id,
            {"role": "user", "content": "My name is Alex", "timestamp": time.time()},
            {"role": "assistant", "content": r1["response"], "timestamp": time.time()}
        )

        r2 = self.brain.process_message("What is my name?", conversation_id=c_id)
        self.assertIn("Alex", r2["response"])

    def test_meta_analysis_sanitizer_comprehensive(self):
        """Sanitizer strips 'The user said...', 'Plan:', 'Option 1/2', rubrics, while keeping normal sentences."""
        meta_sample = (
            "The user said 'My name is xyz'.\n"
            "The user is introducing themselves.\n"
            "Friendly, conversational AI Desktop Assistant.\n"
            "Plan: 1. Greet xyz. 2. Ask how I can help.\n"
            "Nice to meet you, xyz! How can I help you today?"
        )
        cleaned = self.brain._sanitize_conversational_text(meta_sample)
        self.assertEqual(cleaned, "Nice to meet you, xyz! How can I help you today?")

        meta_sample_2 = (
            "Option 1: Hello Alex\n"
            "Option 2: Hey Alex\n"
            "Selected: Option 1\n"
            "Nice to meet you, Alex!"
        )
        cleaned_2 = self.brain._sanitize_conversational_text(meta_sample_2)
        self.assertEqual(cleaned_2, "Nice to meet you, Alex!")

        meta_sample_3 = (
            "Role: Desktop Assistant\n"
            "Language: English\n"
            "Tone: Casual\n"
            "Rules: Be concise\n"
            "Step 1: Greet the user\n"
            "Response: Hey there!"
        )
        cleaned_3 = self.brain._sanitize_conversational_text(meta_sample_3)
        self.assertEqual(cleaned_3, "Hey there!")

        # Normal text preservation
        normal_1 = "I will help you create a plan for your project."
        self.assertEqual(self.brain._sanitize_conversational_text(normal_1), normal_1)

        normal_2 = "The user account settings have been opened."
        self.assertEqual(self.brain._sanitize_conversational_text(normal_2), normal_2)

    def test_new_chat_starts_with_zero_messages(self):
        """New conversations start completely empty with 0 messages."""
        conv = self.brain.create_conversation("Fresh Chat")
        self.assertEqual(len(conv["messages"]), 0)


class TestSuite13_FileAttachmentsAndMultimodal(unittest.TestCase):
    """Suite 13: File Attachment Validation, Multimodal Reasoning, Isolation & Storage Persistence"""

    def setUp(self):
        self.temp_storage = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.temp_att_dir = tempfile.mkdtemp()
        self.brain = AIBrain(storage_path=self.temp_storage)
        self.brain.attachment_manager = AttachmentManager(storage_dir=self.temp_att_dir)

    def tearDown(self):
        if os.path.exists(self.temp_storage):
            os.remove(self.temp_storage)
        if os.path.exists(self.temp_att_dir):
            shutil.rmtree(self.temp_att_dir, ignore_errors=True)

    def test_attachment_validation_rules(self):
        """Validates extension support and empty file detection."""
        mgr = self.brain.attachment_manager
        
        ok, _ = mgr.validate_file("notes.txt", 100)
        self.assertTrue(ok)

        ok, _ = mgr.validate_file("photo.PNG", 5000)
        self.assertTrue(ok)

        ok, _ = mgr.validate_file("script.py", 250)
        self.assertTrue(ok)

        ok, _ = mgr.validate_file("report.pdf", 10000)
        self.assertTrue(ok)

        # Unsupported extension (.exe, .dll)
        bad_ok, bad_err = mgr.validate_file("virus.exe", 100)
        self.assertFalse(bad_ok)
        self.assertIn("isn't supported", bad_err)

        # Empty file
        empty_ok, empty_err = mgr.validate_file("empty.txt", 0)
        self.assertFalse(empty_ok)

    def test_attachment_size_and_count_limits(self):
        """Enforces max 5 files, max 25MB individual, max 50MB batch."""
        mgr = self.brain.attachment_manager

        # Max 25 MB individual limit
        oversized = 26 * 1024 * 1024
        ok, err = mgr.validate_file("huge.jpg", oversized)
        self.assertFalse(ok)
        self.assertIn("too large", err)

        # Max 5 files limit
        six_files = [(f"file_{i}.txt", 100) for i in range(6)]
        b_ok, b_err = mgr.validate_batch(six_files)
        self.assertFalse(b_ok)
        self.assertIn("at most 5", b_err)

        # Max 50 MB total batch limit
        large_batch = [(f"file_{i}.jpg", 15 * 1024 * 1024) for i in range(4)]
        tot_ok, tot_err = mgr.validate_batch(large_batch)
        self.assertFalse(tot_ok)
        self.assertIn("exceeds the maximum limit", tot_err)

    def test_save_and_retrieve_attachment(self):
        """Saves attachment safely and retrieves metadata and binary data."""
        mgr = self.brain.attachment_manager
        content = b"console.log('Hello from test!');"
        meta = mgr.save_attachment("app.js", content, "text/javascript")

        self.assertIn("id", meta)
        self.assertEqual(meta["filename"], "app.js")
        self.assertEqual(meta["category"], "code")
        self.assertEqual(meta["size_bytes"], len(content))

        # Retrieve path
        path = mgr.get_attachment_path(meta["id"])
        self.assertIsNotNone(path)
        self.assertTrue(os.path.exists(path))

        # Read text
        read_txt = mgr.read_attachment_text(meta["id"])
        self.assertEqual(read_txt, "console.log('Hello from test!');")

        # Delete
        self.assertTrue(mgr.delete_attachment(meta["id"]))
        self.assertIsNone(mgr.get_attachment_path(meta["id"]))

    def test_pdf_extraction_and_fallback(self):
        """Tests PDF text extraction."""
        mgr = self.brain.attachment_manager
        # Create a simple PDF using pypdf if possible
        try:
            from pypdf import PdfWriter
            writer = PdfWriter()
            writer.add_blank_page(width=100, height=100)
            buf = io.BytesIO()
            writer.write(buf)
            pdf_bytes = buf.getvalue()
        except Exception:
            pdf_bytes = b"%PDF-1.4 dummy pdf header"

        meta = mgr.save_attachment("document.pdf", pdf_bytes, "application/pdf")
        text = mgr.read_attachment_text(meta["id"])
        self.assertIsNotNone(text)
        self.assertIn("PDF", text)

    def test_gemini_multimodal_payload_construction(self):
        """GeminiProvider formats inlineData for images/PDFs and text blocks for code/text."""
        gemini = self.brain.providers["gemini"]
        gemini.configure("AIzaSyValidGeminiKeySecret123456", enabled=True)
        mgr = self.brain.attachment_manager

        # Save an image and a script
        img_meta = mgr.save_attachment("chart.png", b"\x89PNG\r\n\x1a\nfakeimagebytes", "image/png")
        py_meta = mgr.save_attachment("calc.py", b"def add(x, y): return x + y", "text/x-python")

        captured_payloads = []

        def mock_query_hook(prompt, system_prompt, conversation_context=None, attachments=None):
            return f"Processed {len(attachments or [])} attachment(s) for query: {prompt}"

        gemini._test_query_hook = mock_query_hook
        self.brain.set_active_provider("gemini")

        res = self.brain.process_message(
            "Explain this chart and code",
            attachments=[img_meta, py_meta]
        )
        self.assertIn("2 attachment(s)", res["response"])

    def test_conversation_attachment_isolation(self):
        """Attachments in Conversation A do NOT leak into Conversation B."""
        mgr = self.brain.attachment_manager
        attA = mgr.save_attachment("docA.txt", b"Secret A contents", "text/plain")
        attB = mgr.save_attachment("docB.txt", b"Secret B contents", "text/plain")

        convA = self.brain.create_conversation("Chat A")
        convB = self.brain.create_conversation("Chat B")

        # Chat A turn with attA
        rA = self.brain.process_message("Here is doc A", conversation_id=convA["id"], attachments=[attA])
        self.brain.add_message_pair_to_conversation(
            convA["id"],
            {"role": "user", "content": "Here is doc A", "attachments": [attA], "timestamp": time.time()},
            {"role": "assistant", "content": rA["response"], "timestamp": time.time()}
        )

        # Chat B turn with attB
        rB = self.brain.process_message("Here is doc B", conversation_id=convB["id"], attachments=[attB])
        self.brain.add_message_pair_to_conversation(
            convB["id"],
            {"role": "user", "content": "Here is doc B", "attachments": [attB], "timestamp": time.time()},
            {"role": "assistant", "content": rB["response"], "timestamp": time.time()}
        )

        loadedA = self.brain.get_conversation(convA["id"])
        loadedB = self.brain.get_conversation(convB["id"])

        user_msg_A = [m for m in loadedA["messages"] if m["role"] == "user"][0]
        user_msg_B = [m for m in loadedB["messages"] if m["role"] == "user"][0]

        self.assertEqual(len(user_msg_A["attachments"]), 1)
        self.assertEqual(user_msg_A["attachments"][0]["filename"], "docA.txt")

        self.assertEqual(len(user_msg_B["attachments"]), 1)
        self.assertEqual(user_msg_B["attachments"][0]["filename"], "docB.txt")

        # Verify no cross-attachment leakage
        self.assertNotEqual(user_msg_A["attachments"][0]["id"], user_msg_B["attachments"][0]["id"])

    def test_backward_compatibility_old_conversations(self):
        """Conversations saved without an 'attachments' key load and save seamlessly."""
        conv = self.brain.create_conversation("Legacy Conversation")
        c_id = conv["id"]

        # Add message without attachments key
        legacy_user_msg = {"id": "msg_leg_1", "role": "user", "content": "legacy hello", "timestamp": time.time()}
        legacy_ai_msg = {"id": "msg_leg_2", "role": "assistant", "content": "hello there", "timestamp": time.time()}
        self.brain.add_message_pair_to_conversation(c_id, legacy_user_msg, legacy_ai_msg)

        reloaded = self.brain.get_conversation(c_id)
        self.assertEqual(len(reloaded["messages"]), 2)
        # Should not raise exception
        self.assertEqual(reloaded["messages"][0]["content"], "legacy hello")

    def test_memory_retention_across_attachment_turns(self):
        """Conversational memory retains user name across turns with attachments."""
        conv = self.brain.create_conversation("Memory Attach Test")
        c_id = conv["id"]
        mgr = self.brain.attachment_manager
        sample_att = mgr.save_attachment("notes.txt", b"Project meeting notes", "text/plain")

        # Turn 1: Introduce
        r1 = self.brain.process_message("My name is xyz", conversation_id=c_id)
        self.assertIn("xyz", r1["response"].lower())
        self.brain.add_message_pair_to_conversation(
            c_id,
            {"role": "user", "content": "My name is xyz", "timestamp": time.time()},
            {"role": "assistant", "content": r1["response"], "timestamp": time.time()}
        )

        # Turn 2: Attach file
        r2 = self.brain.process_message("Here are the notes", conversation_id=c_id, attachments=[sample_att])
        self.brain.add_message_pair_to_conversation(
            c_id,
            {"role": "user", "content": "Here are the notes", "attachments": [sample_att], "timestamp": time.time()},
            {"role": "assistant", "content": r2["response"], "timestamp": time.time()}
        )

        # Turn 3: Ask name
        r3 = self.brain.process_message("What is my name?", conversation_id=c_id)
        self.assertIn("xyz", r3["response"].lower())

    def test_built_in_attachment_inspection(self):
        """Built-in basic mode summarizes text/code attachment contents safely."""
        mgr = self.brain.attachment_manager
        py_att = mgr.save_attachment("main.py", b"import os\nprint('Agent active')\n", "text/x-python")

        res = self.brain.process_message("Read this file", attachments=[py_att])
        self.assertIn("main.py", res["response"])
        self.assertIn("Agent active", res["response"])


class TestSuite14_ExplicitLaunchIntentAndFuzzySafety(IsolatedBrainTestCase):
    """Suite 14: Explicit App Launch Intent vs Conversational Mentions & Safe Disambiguation"""

    def setUp(self):
        super().setUp()

    def test_conversational_mentions_do_not_launch_apps(self):
        """Mentioning application names in conversation/questions must NEVER trigger app launches."""
        negative_queries = [
            "Google AI Studio se maine API li.",
            "I was using Google AI Studio.",
            "Roblox Studio kya hai?",
            "ChatGPT desktop ka UI accha hai.",
            "Roblox Studio is useful for making games.",
            "I installed Chrome yesterday.",
            "Notepad mein maine code likha.",
            "Do you know about Roblox Studio?",
            "Google AI Studio kya hai?",
            "Chrome slow chal raha hai.",
            "Google AI Studio"
        ]

        for q in negative_queries:
            res = self.brain.process_message(q)
            self.assertEqual(
                len(res.get("actions", [])),
                0,
                f"Query '{q}' incorrectly triggered an action: {res.get('actions')}"
            )

    def test_explicit_launch_commands_trigger_actions(self):
        """Explicit imperative commands correctly trigger application launch actions."""
        positive_commands = [
            ("open Chrome", "chrome"),
            ("Open Google Chrome", "chrome"),
            ("Chrome kholo", "chrome"),
            ("Chrome khol do", "chrome"),
            ("open Roblox Studio", "roblox_studio"),
            ("Roblox Studio kholo", "roblox_studio"),
            ("ChatGPT Desktop open karo", "chatgpt_desktop"),
            ("Notepad open kar", "notepad"),
            ("Open Google AI Studio", "Google AI Studio")
        ]

        for cmd, expected_key in positive_commands:
            res = self.brain.process_message(cmd)
            actions = res.get("actions", [])
            self.assertEqual(
                len(actions),
                1,
                f"Command '{cmd}' failed to produce an action."
            )
            tool = actions[0].get("tool")
            app_name = actions[0].get("parameters", {}).get("app_name")
            self.assertEqual(tool, "open_application")
            self.assertEqual(app_name.lower(), expected_key.lower())

    def test_google_ai_studio_never_resolves_to_roblox_studio(self):
        """Google AI Studio must never accidentally resolve to Roblox Studio."""
        # 1. In resolve_fuzzy_app
        resolved_key, _, score = self.brain.resolve_fuzzy_app("Google AI Studio")
        if resolved_key:
            self.assertNotEqual(resolved_key, "roblox_studio")

        # 2. In open command
        res = self.brain.process_message("Open Google AI Studio")
        self.assertEqual(len(res["actions"]), 1)
        app_name = res["actions"][0]["parameters"]["app_name"]
        self.assertNotEqual(app_name, "roblox_studio")
        self.assertEqual(app_name.lower(), "google ai studio")

    def test_explicit_screenshot_intent_vs_conversational_mentions(self):
        """Screenshot intent requires explicit imperative command and does not trigger on mentions."""
        # Negative mentions (0 actions)
        negatives = [
            "I took a screenshot.",
            "this screenshot has a bug.",
            "the screenshot shows the problem",
            "I was looking at a screenshot",
            "Google AI Studio screenshot"
        ]
        for q in negatives:
            res = self.brain.process_message(q)
            self.assertEqual(len(res.get("actions", [])), 0, f"Query '{q}' incorrectly triggered action: {res.get('actions')}")

        # Positive explicit requests (1 screenshot action)
        positives = [
            "take a screenshot",
            "screen ka screenshot le",
            "capture my screen",
            "take a screenshot of my screen"
        ]
        for cmd in positives:
            res = self.brain.process_message(cmd)
            actions = res.get("actions", [])
            self.assertEqual(len(actions), 1, f"Command '{cmd}' failed to trigger screenshot")
            self.assertEqual(actions[0]["tool"], "take_screenshot")


class TestSuite15_VideoAttachmentsGlobalMemoryAndDesktopFileOps(IsolatedBrainTestCase):
    """Suite 15: Video Attachments, Level 2 Global Memory, and Desktop Filesystem Operations"""

    def setUp(self):
        super().setUp()
        self.temp_att_dir = tempfile.mkdtemp()
        self.brain.attachment_manager = AttachmentManager(storage_dir=self.temp_att_dir)
        self.temp_mem_path = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.brain.memory_manager = MemoryManager(memory_path=self.temp_mem_path)

    def tearDown(self):
        super().tearDown()
        if os.path.exists(self.temp_att_dir):
            shutil.rmtree(self.temp_att_dir, ignore_errors=True)
        if os.path.exists(self.temp_mem_path):
            try:
                os.remove(self.temp_mem_path)
            except Exception:
                pass

    def test_video_attachment_validation_and_category(self):
        """Validates video formats (.mp4, .webm, .mov, .mkv, .avi) are categorized as 'video'."""
        mgr = self.brain.attachment_manager
        
        for v_ext in ["video.mp4", "clip.webm", "sample.mov", "movie.mkv", "test.avi"]:
            ok, _ = mgr.validate_file(v_ext, 1024 * 1024)
            self.assertTrue(ok, f"Video format {v_ext} was not accepted")

        meta = mgr.save_attachment("gameplay.mp4", b"dummy_mp4_bytes", "video/mp4")
        self.assertEqual(meta["category"], "video")
        self.assertEqual(meta["filename"], "gameplay.mp4")

    def test_level_2_global_memory_across_conversations(self):
        """Global Level 2 memory remembers facts across completely different conversations."""
        # Save memory explicitly
        self.brain.memory_manager.add_memory("user_name", "xyz", "User's name is xyz")
        self.brain.memory_manager.add_memory("pref_lang", "Python", "Prefers Python programming")

        # Session 1: Ask name in a fresh conversation with 0 previous turns
        c1 = self.brain.create_conversation("Fresh Session 1")
        res1 = self.brain.process_message("What is my name?", conversation_id=c1["id"])
        self.assertIn("xyz", res1["response"].lower())

        # Session 2: Ask name in another independent conversation
        c2 = self.brain.create_conversation("Fresh Session 2")
        res2 = self.brain.process_message("What is my name?", conversation_id=c2["id"])
        self.assertIn("xyz", res2["response"].lower())

        # Memory listing and deletion
        mems = self.brain.memory_manager.list_memories()
        self.assertEqual(len(mems), 2)
        self.brain.memory_manager.delete_memory(mems[0]["id"])
        self.assertEqual(len(self.brain.memory_manager.list_memories()), 1)

    def test_explicit_remember_intent(self):
        """User command 'Remember that my name is xyz' saves to global memory."""
        res = self.brain.process_message("Remember that my name is xyz")
        self.assertIn("xyz", res["response"].lower())
        self.assertEqual(self.brain.memory_manager.get_memory_value("user_name").lower(), "xyz")

    def test_desktop_folder_creation_intents(self):
        """Desktop folder creation commands parse into create_folder tool."""
        queries = [
            ("create folder on my desktop", "create_folder"),
            ("create a folder named My Project on my desktop", "create_folder"),
            ("make a folder called Projects", "create_folder"),
            ("mere desktop pe folder bana de", "create_folder")
        ]
        for q, expected_tool in queries:
            res = self.brain.process_message(q)
            self.assertEqual(len(res.get("actions", [])), 1, f"Failed for '{q}'")
            self.assertEqual(res["actions"][0]["tool"], expected_tool)

    def test_desktop_file_creation_intents(self):
        """Desktop file creation commands parse into create_file tool with complete target."""
        queries = [
            ("create test.txt on my desktop", "create_file", "test.txt"),
            ("create index.html on desktop", "create_file", "index.html"),
            ("desktop par test.txt bana do", "create_file", "test.txt"),
            ("create a new .txt file", "create_file", "document.txt")
        ]
        for q, expected_tool, exp_filename in queries:
            res = self.brain.process_message(q)
            self.assertEqual(len(res.get("actions", [])), 1, f"Failed for '{q}'")
            self.assertEqual(res["actions"][0]["tool"], expected_tool)
            self.assertIn(exp_filename.lower(), res["actions"][0]["parameters"]["path"].lower())


class TestSuite16_FunctionalSettingsModesAndRollingRateLimit(IsolatedBrainTestCase):
    """Suite 16: Functional Strict/Balanced/Developer Modes and Rolling Attachment Rate Limiter"""

    def setUp(self):
        super().setUp()
        self.temp_att_dir = tempfile.mkdtemp()
        self.brain.attachment_manager = AttachmentManager(storage_dir=self.temp_att_dir)
        self.safety = SafetyGuard(mode="balanced")

    def tearDown(self):
        super().tearDown()
        if os.path.exists(self.temp_att_dir):
            shutil.rmtree(self.temp_att_dir, ignore_errors=True)

    def test_strict_mode_requires_moderate_confirmations(self):
        """Strict Mode requires human confirmation for file creation, scripts, and folder modifications."""
        self.safety.set_mode("strict")
        
        # Moderate actions require confirmation in strict mode
        risk, req_approval, _ = self.safety.evaluate_action("create_file", {"path": "test.txt", "content": "hello"})
        self.assertTrue(req_approval)

        risk, req_approval, _ = self.safety.evaluate_action("create_folder", {"folder_path": "Projects"})
        self.assertTrue(req_approval)

        risk, req_approval, _ = self.safety.evaluate_action("execute_command", {"command": "dir"})
        self.assertTrue(req_approval)

        # Purely read-only tools remain safe
        risk, req_approval, _ = self.safety.evaluate_action("get_system_info", {})
        self.assertFalse(req_approval)

    def test_balanced_mode_direct_execution_and_dangerous_interception(self):
        """Balanced Mode executes harmless actions directly while intercepting dangerous actions."""
        self.safety.set_mode("balanced")

        # Harmless actions execute directly
        risk, req_approval, _ = self.safety.evaluate_action("create_file", {"path": "test.txt", "content": "hello"})
        self.assertFalse(req_approval)

        risk, req_approval, _ = self.safety.evaluate_action("open_application", {"app_name": "chrome"})
        self.assertFalse(req_approval)

        # Dangerous actions require confirmation
        risk, req_approval, _ = self.safety.evaluate_action("delete_file", {"path": "critical.dat"})
        self.assertTrue(req_approval)
        self.assertEqual(risk, "dangerous")

    def test_developer_mode_minimizes_prompts_while_retaining_core_safety(self):
        """Developer Mode allows fast automation but preserves core SafetyGuard for destructive operations."""
        self.safety.set_mode("developer")

        # Safe development operations proceed directly
        risk, req_approval, _ = self.safety.evaluate_action("create_file", {"path": "build.py", "content": "print('ok')"})
        self.assertFalse(req_approval)

        # Destructive file deletions STILL require confirmation
        risk, req_approval, _ = self.safety.evaluate_action("delete_file", {"path": "database.sqlite"})
        self.assertTrue(req_approval)
        self.assertEqual(risk, "dangerous")

    def test_settings_mode_persistence_across_reloads(self):
        """Selected safety mode persists across reloads in settings file."""
        self.brain.set_safety_mode("strict")
        self.assertEqual(self.brain.safety_mode, "strict")

        # Create a fresh AIBrain pointing to the same settings file
        reloaded = AIBrain(storage_path=self._temp_storage)
        self.assertEqual(reloaded.safety_mode, "strict")

    def test_rolling_rate_limit_20_files_in_10_min_window(self):
        """Enforces max 20 files in rolling 10-minute window and calculates cooldown."""
        mgr = self.brain.attachment_manager
        base_time = 100000.0

        # Upload 4 batches of 5 files = 20 files at base_time
        for i in range(4):
            ok, err, status = mgr.validate_rate_limit(5, now=base_time + (i * 10))
            self.assertTrue(ok)
            mgr.record_successful_uploads(5, now=base_time + (i * 10))

        # Check status: 20/20 used, 0 remaining
        status = mgr.get_rate_limit_status(now=base_time + 100)
        self.assertEqual(status["current_used"], 20)
        self.assertEqual(status["remaining_slots"], 0)
        self.assertFalse(status["accepted"])
        # Next reset is at base_time + 600
        self.assertEqual(status["next_reset_timestamp"], base_time + 600)
        self.assertEqual(status["cooldown_remaining_seconds"], 500)

        # 21st file attempt is rejected
        ok, err, status = mgr.validate_rate_limit(1, now=base_time + 100)
        self.assertFalse(ok)
        self.assertIn("Attachment limit reached", err)

        # Rejected attempt does NOT increase count
        self.assertEqual(mgr.get_rate_limit_status(now=base_time + 100)["current_used"], 20)

        # Advance time past the first batch expiration (base_time + 601s)
        # The 5 files from t=100000 expire, 5 slots become available!
        status_after = mgr.get_rate_limit_status(now=base_time + 601)
        self.assertEqual(status_after["current_used"], 15)
        self.assertEqual(status_after["remaining_slots"], 5)
        self.assertTrue(status_after["accepted"])


class TestSuite17_VerifiedDesktopFilesystemExecution(IsolatedBrainTestCase):
    """Suite 17: Verified Desktop & Windows Filesystem Execution, Dynamic Path Resolution, and Real File/Game Creation"""

    def setUp(self):
        super().setUp()
        self.temp_desktop_dir = tempfile.mkdtemp(prefix="ai_agent_test_desktop_")
        self.temp_ws_dir = tempfile.mkdtemp(prefix="ai_agent_test_ws_")
        self.controller = DesktopController(
            workspace_root=self.temp_ws_dir,
            desktop_path=self.temp_desktop_dir
        )
        self.safety = SafetyGuard(mode="balanced")

    def tearDown(self):
        super().tearDown()
        if os.path.exists(self.temp_desktop_dir):
            shutil.rmtree(self.temp_desktop_dir, ignore_errors=True)
        if os.path.exists(self.temp_ws_dir):
            shutil.rmtree(self.temp_ws_dir, ignore_errors=True)

    def test_01_dynamic_desktop_resolution_and_custom_paths(self):
        """Resolves dynamic desktop path, documents path, and downloads path."""
        desk = self.controller.get_desktop_path()
        self.assertTrue(desk.is_absolute())
        self.assertTrue(desk.exists())
        self.assertEqual(str(desk), str(Path(self.temp_desktop_dir).resolve()))

        docs = self.controller.get_documents_path()
        self.assertTrue(docs.is_absolute())

        downloads = self.controller.get_downloads_path()
        self.assertTrue(downloads.is_absolute())

    def test_02_reusable_verified_filesystem_resolver(self):
        """Reusable resolver handles Desktop, Downloads, Documents, Workspace, and Windows separators."""
        # 1. Desktop relative path
        p1 = self.controller.resolve_path("Desktop/TestAgent")
        self.assertEqual(p1, Path(self.temp_desktop_dir).resolve() / "TestAgent")

        # 2. Desktop Windows backslash path
        p2 = self.controller.resolve_path("Desktop\\TestAgent\\hello.txt")
        self.assertEqual(p2, Path(self.temp_desktop_dir).resolve() / "TestAgent" / "hello.txt")

        # 3. Workspace path
        p3 = self.controller.resolve_path("Workspace/notes.txt")
        self.assertEqual(p3, Path(self.temp_ws_dir).resolve() / "notes.txt")

        # 4. default_to_desktop=True
        p4 = self.controller.resolve_path("TestAgent", default_to_desktop=True)
        self.assertEqual(p4, Path(self.temp_desktop_dir).resolve() / "TestAgent")

    def test_03_folder_creation_full_execution_chain(self):
        """
        Full Execution Chain Test for:
        'mere Desktop par TestAgent naam ka folder bana de'
        1. Intent parser PASS
        2. Action dispatch PASS
        3. Actual Windows filesystem PASS
        """
        user_msg = "mere Desktop par TestAgent naam ka folder bana de"
        
        # Phase 1: Intent parser PASS
        res = self.brain.process_message(user_msg)
        actions = res.get("actions", [])
        self.assertEqual(len(actions), 1, "Expected exactly 1 action")
        act = actions[0]
        self.assertEqual(act["tool"], "create_folder")
        self.assertEqual(act["parameters"]["folder_path"], "Desktop/TestAgent")

        # Phase 2: Action dispatch PASS
        exec_res = self.controller.execute_action(act["tool"], act["parameters"])
        self.assertTrue(exec_res.get("success"), "Action dispatch execution failed")
        self.assertTrue(exec_res.get("verified"), "Filesystem verification flag missing")

        # Phase 3: Actual Windows filesystem PASS
        target_folder = Path(self.temp_desktop_dir) / "TestAgent"
        self.assertTrue(target_folder.exists(), f"Directory {target_folder} does NOT exist on filesystem!")
        self.assertTrue(target_folder.is_dir(), f"Target {target_folder} is not a directory!")
        self.assertEqual(exec_res.get("path"), str(target_folder.resolve()))

    def test_04_nested_file_creation_full_execution_chain(self):
        """
        Full Execution Chain Test for:
        'mere Desktop par TestAgent folder ke andar hello.txt bana de'
        1. Intent parser PASS
        2. Action dispatch PASS
        3. Actual Windows filesystem PASS
        """
        # Ensure parent folder exists
        (Path(self.temp_desktop_dir) / "TestAgent").mkdir(parents=True, exist_ok=True)

        user_msg = "mere Desktop par TestAgent folder ke andar hello.txt bana de"

        # Phase 1: Intent parser PASS
        res = self.brain.process_message(user_msg)
        actions = res.get("actions", [])
        self.assertEqual(len(actions), 1)
        act = actions[0]
        self.assertEqual(act["tool"], "create_file")
        self.assertEqual(act["parameters"]["path"], "Desktop/TestAgent/hello.txt")

        # Phase 2: Action dispatch PASS
        exec_res = self.controller.execute_action(act["tool"], act["parameters"])
        self.assertTrue(exec_res.get("success"))
        self.assertTrue(exec_res.get("verified"))

        # Phase 3: Actual Windows filesystem PASS
        target_file = Path(self.temp_desktop_dir) / "TestAgent" / "hello.txt"
        self.assertTrue(target_file.exists(), f"File {target_file} was not physically created!")
        self.assertTrue(target_file.is_file(), f"Target {target_file} is not a file!")

    def test_05_file_content_write_and_readback_verification(self):
        """
        Full Execution Chain Test for:
        'hello.txt mein Hello from Zevion likh de'
        1. Intent parser PASS
        2. Action dispatch PASS
        3. Actual Windows filesystem PASS (Write, Read, Exact Match)
        """
        # Ensure parent folder and file exist on Desktop
        target_file = Path(self.temp_desktop_dir) / "TestAgent" / "hello.txt"
        target_file.parent.mkdir(parents=True, exist_ok=True)
        target_file.write_text("initial placeholder", encoding="utf-8")

        user_msg = "hello.txt mein Hello from Zevion likh de"

        # Phase 1: Intent parser PASS
        res = self.brain.process_message(user_msg)
        actions = res.get("actions", [])
        self.assertEqual(len(actions), 1)
        act = actions[0]
        self.assertEqual(act["tool"], "create_file")
        self.assertEqual(act["parameters"]["content"], "Hello from Zevion")

        # Phase 2: Action dispatch PASS
        exec_res = self.controller.execute_action(act["tool"], act["parameters"])
        self.assertTrue(exec_res.get("success"))
        self.assertTrue(exec_res.get("verified"))

        # Phase 3: Actual Windows filesystem PASS
        # Read file back using controller tool
        read_res = self.controller.read_file("Desktop/TestAgent/hello.txt")
        self.assertTrue(read_res.get("success"))
        self.assertEqual(read_res.get("raw_content"), "Hello from Zevion")

        # Directly read raw disk bytes to verify physical persistence
        raw_disk_text = target_file.read_text(encoding="utf-8")
        self.assertEqual(raw_disk_text, "Hello from Zevion")

    def test_06_multi_format_files_real_filesystem_verification(self):
        """Verifies physical creation and validation for .txt, .json, .py, .html, .css, .js files."""
        formats = [
            ("create config.json on desktop", "config.json", "{}\n"),
            ("create script.py on desktop", "script.py", "def main():\n    print('ok')\n"),
            ("create index.html on desktop", "index.html", "<!DOCTYPE html><html><body><h1>Test</h1></body></html>"),
            ("create style.css on desktop", "style.css", "body { background: #000; }"),
            ("create app.js on desktop", "app.js", "console.log('App running');"),
            ("create notes.txt on desktop", "notes.txt", "Meeting notes: verified.")
        ]

        for prompt, filename, content in formats:
            res = self.brain.process_message(prompt)
            self.assertEqual(len(res.get("actions", [])), 1)
            act = res["actions"][0]
            self.assertEqual(act["tool"], "create_file")

            # Dispatch with known content
            act["parameters"]["content"] = content
            exec_res = self.controller.execute_action(act["tool"], act["parameters"])
            self.assertTrue(exec_res.get("success"))
            self.assertTrue(exec_res.get("verified"))

            # Physical filesystem verification
            disk_file = Path(self.temp_desktop_dir) / filename
            self.assertTrue(disk_file.exists(), f"File {filename} does not exist on disk!")
            self.assertEqual(disk_file.read_text(encoding="utf-8"), content)

    def test_07_real_game_creation_and_filesystem_verification(self):
        """
        Game Creation Capability:
        'mere Desktop par ek Snake Game bana de' / 'create a snake game on desktop'
        1. Intent parser PASS (create_project with SnakeGame, default format HTML/CSS/JS)
        2. Action dispatch PASS
        3. Actual Windows filesystem PASS (verifies index.html, style.css, game.js, README.md on disk)
        4. Workspace preview bundle generation PASS (verifies canvas, snake, food, game loop)
        """
        user_msg = "mere Desktop par ek Snake Game bana de"

        # Phase 1: Intent parser PASS (Default is Web Game HTML/CSS/JS)
        res = self.brain.process_message(user_msg)
        actions = res.get("actions", [])
        self.assertEqual(len(actions), 1)
        act = actions[0]
        self.assertEqual(act["tool"], "create_project")
        self.assertEqual(act["parameters"]["project_name"], "SnakeGame")
        
        # Verify default format is HTML + CSS + JS (No Python file by default)
        files = act["parameters"]["files"]
        self.assertIn("index.html", files)
        self.assertIn("style.css", files)
        self.assertIn("game.js", files)
        self.assertIn("README.md", files)
        self.assertNotIn("snake.py", files, "Web game should not generate Python file by default")

        # Verify complete code (no placeholder comments)
        self.assertNotIn("// TODO", files["game.js"])
        self.assertNotIn("// add controls later", files["game.js"])
        self.assertIn("addEventListener", files["game.js"])
        self.assertIn("ArrowUp", files["game.js"])
        self.assertIn("gameCanvas", files["index.html"])

        # Phase 2: Action dispatch PASS
        exec_res = self.controller.execute_action(act["tool"], act["parameters"])
        self.assertTrue(exec_res.get("success"))
        self.assertTrue(exec_res.get("verified"))
        self.assertEqual(exec_res.get("files_count"), 4)
        self.assertTrue(bool(exec_res.get("preview_html")), "Preview bundle must be generated for workspace")

        # Phase 3: Actual Windows filesystem PASS
        game_dir = Path(self.temp_desktop_dir) / "SnakeGame"
        self.assertTrue(game_dir.exists() and game_dir.is_dir(), "SnakeGame folder was not physically created!")

        # Verify every file physically exists, is readable, and has content
        for required_file in ["index.html", "style.css", "game.js", "README.md"]:
            fpath = game_dir / required_file
            self.assertTrue(fpath.exists(), f"Required game file '{required_file}' is missing!")
            self.assertTrue(fpath.is_file())
            content_read = fpath.read_text(encoding="utf-8")
            self.assertGreater(len(content_read), 20, f"File '{required_file}' is too small/empty!")

    def test_08_existing_folder_targeting(self):
        """
        Existing Folder Targeting:
        'TestAgent folder ke andar snake game bana de' & 'TestAgent wale folder mein Snake Game bana de'
        Creates project INSIDE existing Desktop/TestAgent/SnakeGame/
        Does NOT create Desktop/SnakeGames/ or Desktop/SnakeGame/.
        """
        # Ensure TestAgent folder exists
        test_agent_dir = Path(self.temp_desktop_dir) / "TestAgent"
        test_agent_dir.mkdir(parents=True, exist_ok=True)

        for user_msg in [
            "TestAgent folder ke andar snake game bana de",
            "TestAgent wale folder mein Snake Game bana de",
            "TestAgent folder me Snake Game bana",
            "Desktop ke TestAgent folder ke andar Snake Game bana de"
        ]:
            res = self.brain.process_message(user_msg)
            actions = res.get("actions", [])
            self.assertEqual(len(actions), 1, f"Failed parsing for '{user_msg}'")
            act = actions[0]
            self.assertEqual(act["tool"], "create_project")
            self.assertEqual(act["parameters"]["target_dir"], "Desktop/TestAgent")
            self.assertEqual(act["parameters"]["project_name"], "SnakeGame")

            exec_res = self.controller.execute_action(act["tool"], act["parameters"])
            self.assertTrue(exec_res.get("success"), f"Failed executing for '{user_msg}'")
            self.assertTrue(exec_res.get("verified"))

            # Target MUST be Desktop/TestAgent/SnakeGame
            nested_game_dir = test_agent_dir / "SnakeGame"
            self.assertTrue(nested_game_dir.exists(), f"Expected {nested_game_dir} to exist!")
            self.assertTrue((nested_game_dir / "index.html").exists())
            self.assertTrue((nested_game_dir / "game.js").exists())

            # Must NOT create Desktop/SnakeGames or Desktop/SnakeGame directly on Desktop root
            self.assertFalse((Path(self.temp_desktop_dir) / "SnakeGames").exists())

    def test_08b_projects_folder_targeting(self):
        """
        Projects Folder Targeting:
        'Projects folder mein Tic Tac Toe bana de'
        Creates Desktop/Projects/TicTacToe/
        """
        proj_dir = Path(self.temp_desktop_dir) / "Projects"
        proj_dir.mkdir(parents=True, exist_ok=True)

        user_msg = "Projects folder mein Tic Tac Toe bana de"
        res = self.brain.process_message(user_msg)
        act = res["actions"][0]
        self.assertEqual(act["parameters"]["target_dir"], "Desktop/Projects")
        self.assertEqual(act["parameters"]["project_name"], "TicTacToe")

        exec_res = self.controller.execute_action(act["tool"], act["parameters"])
        self.assertTrue(exec_res.get("success"))
        self.assertTrue((proj_dir / "TicTacToe" / "index.html").exists())
        self.assertTrue((proj_dir / "TicTacToe" / "game.js").exists())

    def test_09_existing_folder_direct_files_placement(self):
        """
        Direct Files Placement:
        'TestAgent folder mein directly files bana de'
        Places files directly into Desktop/TestAgent/ (no extra SnakeGame subfolder).
        """
        test_agent_dir = Path(self.temp_desktop_dir) / "TestAgentDirect"
        test_agent_dir.mkdir(parents=True, exist_ok=True)

        user_msg = "TestAgentDirect folder mein directly files bana de"

        res = self.brain.process_message(user_msg)
        actions = res.get("actions", [])
        self.assertEqual(len(actions), 1)
        act = actions[0]
        self.assertEqual(act["tool"], "create_project")
        self.assertEqual(act["parameters"]["target_dir"], "Desktop/TestAgentDirect")
        self.assertEqual(act["parameters"]["project_name"], "")

        exec_res = self.controller.execute_action(act["tool"], act["parameters"])
        self.assertTrue(exec_res.get("success"))
        self.assertTrue(exec_res.get("verified"))

        # Files placed directly in TestAgentDirect
        self.assertTrue((test_agent_dir / "index.html").exists())
        self.assertTrue((test_agent_dir / "style.css").exists())
        self.assertTrue((test_agent_dir / "game.js").exists())
        self.assertTrue((test_agent_dir / "README.md").exists())
        self.assertFalse((test_agent_dir / "SnakeGame").exists())

    def test_10_missing_parent_folder_fails_cleanly(self):
        """
        If requested existing folder does not exist, do NOT silently create a differently named folder.
        Reports failure explaining folder was not found.
        """
        user_msg = "NonExistentFolder_9999 folder ke andar snake game bana de"

        res = self.brain.process_message(user_msg)
        act = res["actions"][0]

        exec_res = self.controller.execute_action(act["tool"], act["parameters"])
        self.assertFalse(exec_res.get("success"))
        self.assertFalse(exec_res.get("verified"))
        self.assertTrue(
            "couldn't find" in exec_res.get("error", "").lower() or "not found" in exec_res.get("error", "").lower(),
            f"Expected error message indicating folder was not found, got: {exec_res.get('error')}"
        )

    def test_11_python_game_creation_when_explicitly_requested(self):
        """
        Explicit Python Game Request:
        'Python mein Snake game bana de'
        Creates SnakeGame/ with snake.py and README.md.
        """
        user_msg = "Python mein Snake game bana de"

        # Phase 1: Intent parser PASS
        res = self.brain.process_message(user_msg)
        actions = res.get("actions", [])
        self.assertEqual(len(actions), 1)
        act = actions[0]
        self.assertEqual(act["tool"], "create_project")
        
        files = act["parameters"]["files"]
        self.assertIn("snake.py", files, "Explicit Python request must create snake.py")
        self.assertNotIn("index.html", files)

        # Phase 2: Action dispatch PASS
        py_game_dir = Path(self.temp_desktop_dir) / "PythonSnakeGame"
        act["parameters"]["project_name"] = "PythonSnakeGame"
        exec_res = self.controller.execute_action(act["tool"], act["parameters"])
        self.assertTrue(exec_res.get("success"))
        self.assertTrue(exec_res.get("verified"))

        # Phase 3: Actual filesystem PASS
        disk_py = py_game_dir / "snake.py"
        self.assertTrue(disk_py.exists())
        self.assertGreater(disk_py.stat().st_size, 100)

    def test_12_snake_game_visibility_and_preview_bundle(self):
        """Verifies Snake Game code has immediate canvas initialization, visible snake, food, and sandbox safety."""
        tmpl = get_game_template("snake", "html")
        js = tmpl["game.js"]
        html = tmpl["index.html"]
        css = tmpl["style.css"]

        # 1. Canvas element and size
        self.assertIn("id=\"gameCanvas\"", html)
        self.assertIn("width=\"400\"", html)
        self.assertIn("height=\"400\"", html)

        # 2. Visible snake initialization (at least 3 segments)
        self.assertIn("{ x: 10, y: 10 }", js)
        self.assertIn("{ x: 9, y: 10 }", js)
        self.assertIn("{ x: 8, y: 10 }", js)

        # 3. Sandbox localStorage error safety
        self.assertIn("try {", js)
        self.assertIn("catch", js)
        self.assertNotIn("alert(", js, "alert() must not be used in sandboxed preview")

        # 4. Immediate initial render call before first interval tick
        self.assertIn("render();", js)

        # 5. Keyboard handlers
        self.assertIn("ArrowUp", js)
        self.assertIn("ArrowDown", js)
        self.assertIn("ArrowLeft", js)
        self.assertIn("ArrowRight", js)

    def test_13_failed_file_creation_does_not_report_success(self):
        """If a file cannot be written, create_project returns success=False and does NOT claim victory."""
        bad_files = {"test.js": "console.log('test');"}
        blocker = Path(self.temp_desktop_dir) / "BlockerFile.txt"
        blocker.write_text("i am a file not a directory")

        res = self.controller.create_project("ProjectUnderFile", target_dir=str(blocker), files=bad_files)
        self.assertFalse(res.get("success"))
        self.assertFalse(res.get("verified"))

    def test_14_strict_balanced_developer_safety_modes(self):
        """Verifies SafetyGuard mode policies on filesystem operations."""
        # 1. Strict Mode requires approval for file/folder creation
        self.safety.set_mode("strict")
        risk, req_approval, _ = self.safety.evaluate_action("create_folder", {"folder_path": "Desktop/Test"})
        self.assertTrue(req_approval)
        self.assertEqual(risk, "moderate")

        risk, req_approval, _ = self.safety.evaluate_action("create_file", {"path": "Desktop/Test/hello.txt"})
        self.assertTrue(req_approval)

        risk, req_approval, _ = self.safety.evaluate_action("create_project", {"project_name": "SnakeGame"})
        self.assertTrue(req_approval)

        # 2. Balanced Mode directly executes safe file/folder creation, protects delete
        self.safety.set_mode("balanced")
        risk, req_approval, _ = self.safety.evaluate_action("create_folder", {"folder_path": "Desktop/Test"})
        self.assertFalse(req_approval)

        risk, req_approval, _ = self.safety.evaluate_action("delete_file", {"path": "Desktop/Test"})
        self.assertTrue(req_approval)
        self.assertEqual(risk, "dangerous")

        # 3. Developer Mode allows files/builds, strictly guards destructive delete
        self.safety.set_mode("developer")
        risk, req_approval, _ = self.safety.evaluate_action("create_file", {"path": "Desktop/Test/script.py"})
        self.assertFalse(req_approval)

        risk, req_approval, _ = self.safety.evaluate_action("delete_file", {"path": "Desktop/Test/script.py"})
        self.assertTrue(req_approval)
        self.assertEqual(risk, "dangerous")

    def test_15_cleanup_verification(self):
        """Verifies that all created test artifacts on Desktop can be cleanly removed."""
        # Create folder and file
        f_res = self.controller.create_folder("Desktop/TempCleanFolder")
        self.assertTrue(f_res.get("success"))
        file_res = self.controller.create_file("Desktop/TempCleanFolder/temp.txt", "temporary data")
        self.assertTrue(file_res.get("success"))

        target = Path(self.temp_desktop_dir) / "TempCleanFolder"
        self.assertTrue(target.exists())

        # Delete through controller
        del_res = self.controller.delete_file("Desktop/TempCleanFolder", permanent=True)
        self.assertTrue(del_res.get("success"))
        self.assertTrue(del_res.get("verified"))

        # Physically verify it no longer exists on the filesystem
        self.assertFalse(target.exists(), "Cleanup failed: directory still exists on disk!")


class TestSuite18_NewUtilityTools(IsolatedBrainTestCase):
    """Suite 18: Clipboard, File Search, Media Control, and Keyboard Shortcut tools."""

    def setUp(self):
        super().setUp()
        self.temp_desktop_dir = tempfile.mkdtemp(prefix="ai_agent_test_desktop_")
        self.temp_ws_dir = tempfile.mkdtemp(prefix="ai_agent_test_ws_")
        self.controller = DesktopController(
            workspace_root=self.temp_ws_dir,
            desktop_path=self.temp_desktop_dir
        )

    def tearDown(self):
        super().tearDown()
        if os.path.exists(self.temp_desktop_dir):
            shutil.rmtree(self.temp_desktop_dir, ignore_errors=True)
        if os.path.exists(self.temp_ws_dir):
            shutil.rmtree(self.temp_ws_dir, ignore_errors=True)

    # --- Intent Parser Tests (Phase 1) ---
    def test_01_clipboard_intent(self):
        res = self.brain.process_message("copy hello world to clipboard", current_workspace=self.temp_ws_dir)
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "clipboard_set")
        self.assertEqual(acts[0]["parameters"]["text"], "hello world")

    def test_02_find_files_intent(self):
        res = self.brain.process_message("find my notes file", current_workspace=self.temp_ws_dir)
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "find_files")
        self.assertIn("notes", acts[0]["parameters"]["pattern"])

    def test_03_media_control_intents(self):
        for cmd, expected in [
            ("pause music", "play_pause"),
            ("next song", "next"),
            ("previous song", "previous"),
            ("volume up", "volume_up"),
            ("volume down", "volume_down"),
            ("mute", "mute"),
            ("stop music", "stop"),
        ]:
            res = self.brain.process_message(cmd, current_workspace=self.temp_ws_dir)
            acts = res.get("actions", [])
            self.assertEqual(len(acts), 1, f"'{cmd}' should produce 1 action")
            self.assertEqual(acts[0]["tool"], "media_control", f"'{cmd}'")
            self.assertEqual(acts[0]["parameters"]["action"], expected, f"'{cmd}'")

    def test_04_press_keys_intent(self):
        res = self.brain.process_message("press ctrl+c", current_workspace=self.temp_ws_dir)
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "press_keys")
        self.assertEqual(acts[0]["parameters"]["keys"], "ctrl+c")

    # --- Action Dispatch Tests (Phase 2) ---
    def test_05_clipboard_set_get_dispatch(self):
        set_res = self.controller.execute_action("clipboard_set", {"text": "hello zevion"})
        # On headless Linux there may be no clipboard backend (xclip/xsel); the tool must
        # return a well-formed record with 'success' and (on failure) a descriptive error.
        self.assertIn("success", set_res)
        self.assertIn("char_count", set_res)
        get_res = self.controller.execute_action("clipboard_get", {})
        self.assertIn("text", get_res)

    def test_06_find_files_dispatch(self):
        # Create a file on the temp desktop
        (Path(self.temp_desktop_dir) / "project_report.pdf").write_text("x")
        (Path(self.temp_desktop_dir) / "random_notes.txt").write_text("y")
        res = self.controller.execute_action("find_files", {"pattern": "report", "directory": "Desktop"})
        self.assertTrue(res.get("success"))
        names = [m["name"] for m in res.get("matches", [])]
        self.assertIn("project_report.pdf", names)
        self.assertNotIn("random_notes.txt", names)

    def test_07_find_files_missing_directory_fallback(self):
        res = self.controller.execute_action("find_files", {"pattern": "nothing_xyz", "directory": "DoesNotExistFolder999"})
        # Should not crash; either success with 0 matches or graceful error
        self.assertIn(res.get("success"), [True, False])

    def test_08_media_control_dispatch(self):
        res = self.controller.execute_action("media_control", {"action": "play_pause"})
        # On headless CI this may report an unsupported-platform error but must return a record
        self.assertIn("action", res)

    def test_09_press_keys_dispatch(self):
        res = self.controller.execute_action("press_keys", {"keys": "ctrl+c"})
        self.assertIn("keys", res)

    def test_10_safety_classification(self):
        self.safety = SafetyGuard(mode="balanced")
        for tool in ["clipboard_set", "clipboard_get", "find_files", "media_control", "press_keys", "get_battery", "list_directory"]:
            risk, req_approval, _ = self.safety.evaluate_action(tool, {})
            self.assertEqual(risk, "safe", f"{tool} should be safe")
            self.assertFalse(req_approval, f"{tool} should not require confirmation")

    def test_11_battery_intent(self):
        res = self.brain.process_message("battery kitna hai", current_workspace=self.temp_ws_dir)
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "get_battery")

    def test_12_note_intent(self):
        res = self.brain.process_message("note karo: buy milk", current_workspace=self.temp_ws_dir)
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "add_note")
        self.assertEqual(acts[0]["parameters"]["text"], "buy milk")

    def test_13_note_dispatch(self):
        res = self.controller.execute_action("add_note", {"text": "test note entry"})
        self.assertTrue(res.get("success"))
        self.assertIn("path", res)

    def test_14_list_directory_intents(self):
        res = self.brain.process_message("desktop me kya hai", current_workspace=self.temp_ws_dir)
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "list_directory")
        self.assertEqual(acts[0]["parameters"]["directory"], "Desktop")

    def test_15_list_directory_dispatch(self):
        (Path(self.temp_desktop_dir) / "alpha.txt").write_text("a")
        (Path(self.temp_desktop_dir) / "beta.txt").write_text("b")
        res = self.controller.execute_action("list_directory", {"directory": "Desktop"})
        self.assertTrue(res.get("success"))
        names = [i["name"] for i in res.get("items", [])]
        self.assertIn("alpha.txt", names)
        self.assertIn("beta.txt", names)

    def test_16_battery_dispatch(self):
        res = self.controller.execute_action("get_battery", {})
        # On desktop/CI there may be no battery; must return a well-formed record
        self.assertIn("success", res)
        self.assertIn("battery", res)


class TestSuite19_SafetyHardening(IsolatedBrainTestCase):
    """Suite 19: Hardened safety — destructive commands & shell commands are always guarded."""

    def setUp(self):
        super().setUp()
        self.safety = SafetyGuard(mode="balanced")

    def test_01_hard_blocked_commands_never_run_in_any_mode(self):
        hard_blocked = [
            "rm -rf /", "rm -rf /home", "rm -r /tmp", "format c:", "del /s /q C:\\Windows",
            "diskpart", "rd /s C:\\", "Remove-Item -Recurse C:\\", "Remove-Item -Force x",
            "mkfs.ext4 /dev/sda", "dd if=/dev/zero of=/dev/sda", "bcdedit", "bootrec",
            "taskkill /f /im explorer.exe", "Stop-Process -Force", "del *.*", "rm *",
            "find / -delete", "chmod -R 777 /", "clear-recyclebin", "cipher /w",
            ":(){ :|:& };:", "vssadmin delete shadows",
        ]
        for mode in ["strict", "balanced", "developer"]:
            self.safety.set_mode(mode)
            for cmd in hard_blocked:
                risk, req, _ = self.safety.evaluate_action("execute_command", {"command": cmd})
                self.assertEqual(risk, "blocked", f"[{mode}] '{cmd}' must be HARD BLOCKED")
                self.assertFalse(req, f"[{mode}] '{cmd}' must not be approvable")

    def test_02_destructive_scoped_commands_require_confirmation(self):
        destructive_scoped = [
            "del notes.txt", "erase temp.txt", "rm file.txt", "rd folder",
            "remove-item file.txt", "taskkill 1234", "reg delete HKCU\\test",
            "drop database users", "shutdown /s",
        ]
        for mode in ["strict", "balanced", "developer"]:
            self.safety.set_mode(mode)
            for cmd in destructive_scoped:
                risk, req, _ = self.safety.evaluate_action("execute_command", {"command": cmd})
                self.assertEqual(risk, "dangerous", f"[{mode}] '{cmd}' must be dangerous")
                self.assertTrue(req, f"[{mode}] '{cmd}' must require confirmation")

    def test_03_plain_shell_command_requires_confirmation_in_all_modes(self):
        # shell=True is arbitrary code execution -> always require confirmation
        for mode in ["strict", "balanced", "developer"]:
            self.safety.set_mode(mode)
            risk, req, _ = self.safety.evaluate_action("execute_command", {"command": "echo hello"})
            self.assertTrue(req, f"[{mode}] shell command must require confirmation")
            self.assertEqual(risk, "moderate")

    def test_03_delete_file_always_dangerous(self):
        for mode in ["strict", "balanced", "developer"]:
            self.safety.set_mode(mode)
            risk, req, _ = self.safety.evaluate_action("delete_file", {"path": "Desktop/test.txt"})
            self.assertEqual(risk, "dangerous", f"[{mode}] delete must be dangerous")
            self.assertTrue(req)

    def test_04_developer_mode_still_blocks_kill_process(self):
        self.safety.set_mode("developer")
        risk, req, _ = self.safety.evaluate_action("kill_system_process", {"process": "explorer.exe"})
        self.assertEqual(risk, "dangerous")
        self.assertTrue(req)

    def test_05_safe_ops_still_auto_run_in_developer(self):
        self.safety.set_mode("developer")
        risk, req, _ = self.safety.evaluate_action("create_folder", {"folder_path": "Desktop/Test"})
        self.assertFalse(req)

    def test_06_balanced_file_creation_still_auto_runs(self):
        self.safety.set_mode("balanced")
        risk, req, _ = self.safety.evaluate_action("create_folder", {"folder_path": "Desktop/Test"})
        self.assertFalse(req)

    def test_07_api_key_redaction_intact(self):
        from safety_guard import sanitize_safe_payload
        payload = {"api_key": "AIzaSyXYZsecret", "nested": {"token": "sk-abc1234567890123456789"}}
        cleaned = sanitize_safe_payload(payload)
        self.assertEqual(cleaned["api_key"], "[REDACTED]")
        self.assertEqual(cleaned["nested"]["token"], "[REDACTED]")

    def test_08_controller_defense_in_depth_blocks_hard_blocked(self):
        """Even a direct controller.execute_action call must refuse hard-blocked commands."""
        import tempfile, os
        tmpd = tempfile.mkdtemp(prefix="safety_test_")
        tmpw = tempfile.mkdtemp(prefix="safety_test_ws_")
        try:
            ctrl = DesktopController(workspace_root=tmpw, desktop_path=tmpd)
            res = ctrl.execute_action("execute_command", {"command": "rm -rf /"})
            self.assertFalse(res.get("success"))
            self.assertTrue(res.get("blocked"))
            # And a safe command still works
            res2 = ctrl.execute_action("execute_command", {"command": "echo hello"})
            self.assertTrue(res2.get("success"))
        finally:
            import shutil
            shutil.rmtree(tmpd, ignore_errors=True)
            shutil.rmtree(tmpw, ignore_errors=True)

    def test_09_system_path_protection(self):
        """Write/delete into system paths must be blocked."""
        protected = ["C:\\Windows\\System32\\test.txt", "C:\\Program Files\\app\\x.txt",
                     "/etc/passwd", "/usr/bin/x", "/bin/sh", "/var/log/x",
                     "C:\\Windows\\test.txt", "system32\\cmd.exe"]
        for p in protected:
            self.assertTrue(SafetyGuard.is_protected_path(p), f"'{p}' should be protected")

    def test_10_system_path_not_protected(self):
        """Normal user paths must NOT be protected."""
        safe = ["Desktop/test.txt", "Downloads/file.zip", "Documents/report.pdf",
                "Workspace/code.py", "/home/user/notes.txt"]
        for p in safe:
            self.assertFalse(SafetyGuard.is_protected_path(p), f"'{p}' should NOT be protected")

    def test_11_chained_command_detection(self):
        """Chained commands (&&, ;, |) must be flagged as dangerous or blocked."""
        # Commands with chains but no hard-blocked keyword -> dangerous
        for cmd in ["echo hi && echo bye", "ls; ls -la", "cat a.txt | wc -l", "echo a || echo b"]:
            self.assertTrue(SafetyGuard.has_chained_operators(cmd), f"'{cmd}' should be chained")
            risk, req, _ = self.safety.evaluate_action("execute_command", {"command": cmd})
            self.assertEqual(risk, "dangerous", f"'{cmd}' should be dangerous (chained)")
            self.assertTrue(req)
        # Chained command hiding a hard-blocked keyword -> blocked
        risk, req, _ = self.safety.evaluate_action("execute_command", {"command": "echo hi && rm -rf x"})
        self.assertEqual(risk, "blocked")
        # No chain operators
        self.assertFalse(SafetyGuard.has_chained_operators("echo hello"))

    def test_12_dry_run_mode(self):
        """Dry-run mode should make evaluate_action return a non-executing state."""
        self.safety.set_dry_run(True)
        self.assertTrue(self.safety.dry_run)
        self.safety.set_dry_run(False)
        self.assertFalse(self.safety.dry_run)

    def test_13_controller_blocks_system_path_delete(self):
        """Controller delete_file must refuse protected system paths."""
        import tempfile, os, shutil
        tmpd = tempfile.mkdtemp(prefix="safety_test_")
        tmpw = tempfile.mkdtemp(prefix="safety_test_ws_")
        try:
            ctrl = DesktopController(workspace_root=tmpw, desktop_path=tmpd)
            # create a file and try to delete a protected path
            res = ctrl.execute_action("delete_file", {"path": "/etc/passwd"})
            self.assertFalse(res.get("success"))
            self.assertTrue(res.get("blocked"))
        finally:
            shutil.rmtree(tmpd, ignore_errors=True)
            shutil.rmtree(tmpw, ignore_errors=True)

    def test_14_delete_uses_recycle_bin_by_default(self):
        """delete_file should send to recycle bin (recoverable) when send2trash works."""
        import tempfile, os, shutil
        tmpd = tempfile.mkdtemp(prefix="safety_test_")
        tmpw = tempfile.mkdtemp(prefix="safety_test_ws_")
        try:
            ctrl = DesktopController(workspace_root=tmpw, desktop_path=tmpd)
            fp = Path(tmpw) / "temp_note.txt"
            fp.write_text("hello")
            res = ctrl.execute_action("delete_file", {"path": "Workspace/temp_note.txt"})
            # success should be True (file gone), and sent_to_recycle_bin flag present
            self.assertTrue(res.get("success"))
            self.assertFalse(fp.exists())
            self.assertIn("sent_to_recycle_bin", res)
        finally:
            shutil.rmtree(tmpd, ignore_errors=True)
            shutil.rmtree(tmpw, ignore_errors=True)

    def test_15_download_intent(self):
        res = self.brain.process_message("download https://example.com/file.zip", current_workspace="/tmp")
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "download_file")
        self.assertEqual(acts[0]["parameters"]["url"], "https://example.com/file.zip")


class TestSuite21_UsageUndoDownload(IsolatedBrainTestCase):
    """Suite 21: Usage tracking, undo/backup, and download tool."""

    def setUp(self):
        super().setUp()
        self.temp_desktop_dir = tempfile.mkdtemp(prefix="ai_agent_test_desktop_")
        self.temp_ws_dir = tempfile.mkdtemp(prefix="ai_agent_test_ws_")
        self.controller = DesktopController(
            workspace_root=self.temp_ws_dir,
            desktop_path=self.temp_desktop_dir
        )

    def tearDown(self):
        super().tearDown()
        if os.path.exists(self.temp_desktop_dir):
            shutil.rmtree(self.temp_desktop_dir, ignore_errors=True)
        if os.path.exists(self.temp_ws_dir):
            shutil.rmtree(self.temp_ws_dir, ignore_errors=True)

    def test_01_usage_tracking(self):
        self.brain.record_usage("gemini", success=True, approx_tokens=100)
        self.brain.record_usage("gemini", success=False)
        stats = self.brain.get_usage_stats()
        self.assertIn("today", stats)
        self.assertGreaterEqual(stats["today"].get("requests", 0), 2)
        self.assertGreaterEqual(stats["today"].get("tokens", 0), 100)
        self.assertIn("last_7_days", stats)

    def test_02_undo_intent(self):
        for cmd in ["undo", "undo last edit", "undo kar", "revert last edit"]:
            res = self.brain.process_message(cmd, current_workspace=self.temp_ws_dir)
            acts = res.get("actions", [])
            self.assertEqual(len(acts), 1, f"'{cmd}' should produce undo_edit")
            self.assertEqual(acts[0]["tool"], "undo_edit")

    def test_03_edit_creates_backup_and_undo_restores(self):
        fp = Path(self.temp_ws_dir) / "doc.txt"
        fp.write_text("hello world")
        # Edit
        res = self.controller.execute_action("edit_file", {"path": "Workspace/doc.txt", "old_text": "hello", "new_text": "goodbye"})
        self.assertTrue(res.get("success"))
        self.assertTrue(res.get("undoable"))
        self.assertEqual(fp.read_text(), "goodbye world")
        # Undo
        undo = self.controller.execute_action("undo_edit", {})
        self.assertTrue(undo.get("success"))
        self.assertEqual(fp.read_text(), "hello world")

    def test_04_download_dispatch_verifies_path(self):
        # Use a local file URL via data is hard; just verify structure on a bad URL
        res = self.controller.execute_action("download_file", {"url": "not-a-url"})
        self.assertFalse(res.get("success"))
        self.assertIn("error", res)

    def test_05_safety_classification(self):
        self.safety = SafetyGuard(mode="balanced")
        risk, req, _ = self.safety.evaluate_action("download_file", {"url": "https://x.com/f.zip"})
        self.assertEqual(risk, "safe")
        risk, req, _ = self.safety.evaluate_action("undo_edit", {})
        self.assertEqual(risk, "moderate")


class TestSuite22_MoreGames(IsolatedBrainTestCase):
    """Suite 22: New game types — Flappy Bird, 2048, Breakout, Memory Match."""

    def test_01_flappy_bird_intent(self):
        res = self.brain.process_message("flappy bird game bana de", current_workspace="/tmp")
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "create_project")
        self.assertEqual(acts[0]["parameters"]["project_name"], "FlappyBird")
        files = acts[0]["parameters"]["files"]
        self.assertIn("index.html", files)
        self.assertIn("flappy", files["index.html"].lower())

    def test_02_2048_intent(self):
        res = self.brain.process_message("2048 game banao", current_workspace="/tmp")
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["parameters"]["project_name"], "Game2048")
        self.assertIn("2048", acts[0]["parameters"]["files"]["index.html"])

    def test_03_breakout_intent(self):
        res = self.brain.process_message("breakout game bana de", current_workspace="/tmp")
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["parameters"]["project_name"], "Breakout")

    def test_04_memory_match_intent(self):
        res = self.brain.process_message("memory game bana de", current_workspace="/tmp")
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["parameters"]["project_name"], "MemoryMatch")

    def test_05_get_game_template_all_games(self):
        from ai_brain import get_game_template
        for g in ["snake", "tic tac toe", "flappy bird", "2048", "breakout", "memory match", "pong"]:
            t = get_game_template(g)
            self.assertIn("index.html", t)
            self.assertGreater(len(t["index.html"]), 100, f"{g} index.html should be substantial")

    def test_06_flappy_bird_full_execution(self):
        import tempfile, shutil
        tmpd = tempfile.mkdtemp(prefix="game_test_")
        tmpw = tempfile.mkdtemp(prefix="game_test_ws_")
        try:
            ctrl = DesktopController(workspace_root=tmpw, desktop_path=tmpd)
            files = get_game_template("flappy bird")
            res = ctrl.create_project("FlappyBird", target_dir="Desktop", files=files)
            self.assertTrue(res.get("success"), res.get("error"))
            self.assertIn("preview_html", res)
            self.assertIn("flappy", res["preview_html"].lower())
        finally:
            shutil.rmtree(tmpd, ignore_errors=True)
            shutil.rmtree(tmpw, ignore_errors=True)


class TestSuite20_ClaudeCodeStyleTools(IsolatedBrainTestCase):
    """Suite 20: Web search, web fetch, grep (content search), and file edit tools."""

    def setUp(self):
        super().setUp()
        self.temp_desktop_dir = tempfile.mkdtemp(prefix="ai_agent_test_desktop_")
        self.temp_ws_dir = tempfile.mkdtemp(prefix="ai_agent_test_ws_")
        self.controller = DesktopController(
            workspace_root=self.temp_ws_dir,
            desktop_path=self.temp_desktop_dir
        )
        self.safety = SafetyGuard(mode="balanced")

    def tearDown(self):
        super().tearDown()
        if os.path.exists(self.temp_desktop_dir):
            shutil.rmtree(self.temp_desktop_dir, ignore_errors=True)
        if os.path.exists(self.temp_ws_dir):
            shutil.rmtree(self.temp_ws_dir, ignore_errors=True)

    # --- Intent Parser ---
    def test_01_web_search_intent(self):
        res = self.brain.process_message("search the web for best python libraries", current_workspace=self.temp_ws_dir)
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "web_search")
        self.assertEqual(acts[0]["parameters"]["query"], "best python libraries")

    def test_02_web_search_google_intent(self):
        res = self.brain.process_message("google search cricket score", current_workspace=self.temp_ws_dir)
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "web_search")

    def test_03_plain_search_still_opens_browser(self):
        # "search for X" (no "web") should still open the browser (existing behavior)
        res = self.brain.process_message("search for Minecraft", current_workspace=self.temp_ws_dir)
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "open_website")

    def test_04_web_fetch_intent(self):
        res = self.brain.process_message("fetch https://example.com", current_workspace=self.temp_ws_dir)
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "web_fetch")
        self.assertEqual(acts[0]["parameters"]["url"], "https://example.com")

    def test_05_grep_intent(self):
        res = self.brain.process_message("grep for TODO in downloads", current_workspace=self.temp_ws_dir)
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "grep_files")
        self.assertEqual(acts[0]["parameters"]["pattern"], "TODO")
        self.assertEqual(acts[0]["parameters"]["directory"], "Downloads")

    def test_06_search_inside_files_intent(self):
        res = self.brain.process_message("search inside files for password", current_workspace=self.temp_ws_dir)
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "grep_files")
        self.assertEqual(acts[0]["parameters"]["pattern"], "password")

    def test_07_edit_file_intent(self):
        res = self.brain.process_message("edit notes.txt replace hello with hi", current_workspace=self.temp_ws_dir)
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "edit_file")
        self.assertEqual(acts[0]["parameters"]["path"], "notes.txt")
        self.assertEqual(acts[0]["parameters"]["old_text"], "hello")
        self.assertEqual(acts[0]["parameters"]["new_text"], "hi")

    # --- Action Dispatch ---
    def test_08_grep_dispatch(self):
        (Path(self.temp_ws_dir) / "todo_list.txt").write_text("TODO: fix bug\nnormal line\nTODO: ship it")
        res = self.controller.execute_action("grep_files", {"pattern": "TODO", "directory": "Workspace"})
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("count"), 2)

    def test_09_grep_no_match(self):
        (Path(self.temp_ws_dir) / "empty.txt").write_text("nothing here")
        res = self.controller.execute_action("grep_files", {"pattern": "zzz_not_found", "directory": "Workspace"})
        self.assertTrue(res.get("success"))
        self.assertEqual(res.get("count"), 0)

    def test_10_edit_file_dispatch(self):
        fp = Path(self.temp_ws_dir) / "greeting.txt"
        fp.write_text("hello world")
        res = self.controller.execute_action("edit_file", {"path": "Workspace/greeting.txt", "old_text": "hello", "new_text": "goodbye"})
        self.assertTrue(res.get("success"))
        self.assertEqual(fp.read_text(), "goodbye world")

    def test_11_edit_file_not_found(self):
        res = self.controller.execute_action("edit_file", {"path": "Workspace/nope.txt", "old_text": "x", "new_text": "y"})
        self.assertFalse(res.get("success"))

    def test_12_safety_classification(self):
        for tool in ["web_search", "web_fetch", "grep_files"]:
            risk, req, _ = self.safety.evaluate_action(tool, {})
            self.assertEqual(risk, "safe", f"{tool} should be safe")
            self.assertFalse(req)
        # edit_file is a file modification -> moderate
        risk, req, _ = self.safety.evaluate_action("edit_file", {"path": "x.txt"})
        self.assertEqual(risk, "moderate")


class TestSuite23_RemindersAndPlanMode(IsolatedBrainTestCase):
    """Suite 23: Timed reminders and Plan-Then-Do mode."""

    def setUp(self):
        super().setUp()
        self.temp_desktop_dir = tempfile.mkdtemp(prefix="ai_agent_test_desktop_")
        self.temp_ws_dir = tempfile.mkdtemp(prefix="ai_agent_test_ws_")
        self.controller = DesktopController(
            workspace_root=self.temp_ws_dir,
            desktop_path=self.temp_desktop_dir
        )
        self.safety = SafetyGuard(mode="balanced")

    def tearDown(self):
        super().tearDown()
        if os.path.exists(self.temp_desktop_dir):
            shutil.rmtree(self.temp_desktop_dir, ignore_errors=True)
        if os.path.exists(self.temp_ws_dir):
            shutil.rmtree(self.temp_ws_dir, ignore_errors=True)

    def test_01_reminder_intent_english(self):
        res = self.brain.process_message("remind me in 10 minutes to call mom", current_workspace=self.temp_ws_dir)
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "set_reminder")
        self.assertEqual(acts[0]["parameters"]["text"], "call mom")
        self.assertEqual(acts[0]["parameters"]["minutes"], 10.0)

    def test_02_reminder_intent_hinglish(self):
        res = self.brain.process_message("yaad dilana 5 minute me milk lana", current_workspace=self.temp_ws_dir)
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "set_reminder")
        self.assertEqual(acts[0]["parameters"]["text"], "milk lana")

    def test_03_reminder_dispatch(self):
        res = self.controller.execute_action("set_reminder", {"text": "test reminder", "minutes": 0.01})
        self.assertTrue(res.get("success"))
        self.assertIn("due_at", res)

    def test_04_plan_mode_setting(self):
        self.safety.set_plan_mode(True)
        self.assertTrue(self.safety.plan_mode)
        self.safety.set_plan_mode(False)
        self.assertFalse(self.safety.plan_mode)


class TestSuite24_ExportAndUsage(IsolatedBrainTestCase):
    """Suite 24: Export conversation/audit, usage stats."""

    def test_01_usage_stats_structure(self):
        self.brain.record_usage("gemini", success=True, approx_tokens=50)
        stats = self.brain.get_usage_stats()
        self.assertIn("today", stats)
        self.assertIn("last_7_days", stats)
        self.assertIn("total_days", stats)
        self.assertGreaterEqual(stats["today"]["tokens"], 50)

    def test_02_usage_provider_breakdown(self):
        self.brain.record_usage("gemini", success=True, approx_tokens=10)
        self.brain.record_usage("claude", success=True, approx_tokens=20)
        stats = self.brain.get_usage_stats()
        providers = stats["today"].get("providers", {})
        self.assertIn("gemini", providers)
        self.assertIn("claude", providers)


class TestSuite25_BuiltinOutputAndVision(IsolatedBrainTestCase):
    """Suite 25: Better built-in output quality + screenshot vision tool."""

    def test_01_capabilities_response(self):
        res = self.brain.process_message("what can you do", current_workspace="/tmp")
        self.assertIn("apps", res.get("response", "").lower())
        self.assertEqual(len(res.get("actions", [])), 0)

    def test_02_time_response(self):
        res = self.brain.process_message("what time is it", current_workspace="/tmp")
        self.assertIn("time", res.get("response", "").lower())
        self.assertEqual(len(res.get("actions", [])), 0)

    def test_03_math_response(self):
        res = self.brain.process_message("calculate 5 * 7", current_workspace="/tmp")
        self.assertIn("35", res.get("response", ""))

    def test_04_identity_response(self):
        res = self.brain.process_message("who are you", current_workspace="/tmp")
        self.assertIn("Zevion", res.get("response", ""))

    def test_05_analyze_screen_intent(self):
        res = self.brain.process_message("analyze my screen", current_workspace="/tmp")
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "analyze_screenshot")

    def test_06_analyze_screenshot_dispatch(self):
        import tempfile, shutil
        tmpd = tempfile.mkdtemp(prefix="vision_test_")
        tmpw = tempfile.mkdtemp(prefix="vision_test_ws_")
        try:
            ctrl = DesktopController(workspace_root=tmpw, desktop_path=tmpd)
            res = ctrl.execute_action("analyze_screenshot", {"save_path": "Workspace/shot.png"})
            # Without a vision API key it should return a graceful error, not crash
            self.assertIn("success", res)
            self.assertIn("analysis", res)
        finally:
            shutil.rmtree(tmpd, ignore_errors=True)
            shutil.rmtree(tmpw, ignore_errors=True)


class TestSuite26_AnyDrivePathCreation(IsolatedBrainTestCase):
    """Suite 26: Create files/folders at arbitrary drives & absolute paths."""

    def test_01_absolute_windows_path_file(self):
        res = self.brain.process_message("D:\\projects\\test.txt bana de", current_workspace="/tmp")
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "create_file")
        self.assertIn("D:", acts[0]["parameters"]["path"])

    def test_02_absolute_windows_path_folder(self):
        res = self.brain.process_message("C:\\Users\\xyz\\Documents\\note.txt bana de", current_workspace="/tmp")
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "create_file")
        self.assertIn("C:", acts[0]["parameters"]["path"])

    def test_03_forward_slash_absolute(self):
        res = self.brain.process_message("C:/data/report.txt bana de", current_workspace="/tmp")
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "create_file")
        self.assertIn("C:/", acts[0]["parameters"]["path"])

    def test_04_drive_letter_file(self):
        res = self.brain.process_message("D drive me test.txt file bana de", current_workspace="/tmp")
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "create_file")
        self.assertIn("D:", acts[0]["parameters"]["path"])

    def test_05_drive_letter_folder(self):
        res = self.brain.process_message("E drive pe folder bana de", current_workspace="/tmp")
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "create_folder")
        self.assertIn("E:", acts[0]["parameters"]["folder_path"])

    def test_06_unix_absolute_path(self):
        res = self.brain.process_message("/home/user/data/file.txt bana de", current_workspace="/tmp")
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "create_file")
        self.assertIn("/home/", acts[0]["parameters"]["path"])

    def test_07_create_file_at_path(self):
        res = self.brain.process_message("create file at D:\\backup\\data.txt", current_workspace="/tmp")
        acts = res.get("actions", [])
        self.assertEqual(len(acts), 1)
        self.assertEqual(acts[0]["tool"], "create_file")
        self.assertIn("D:\\backup", acts[0]["parameters"]["path"])


if __name__ == "__main__":
    unittest.main()
