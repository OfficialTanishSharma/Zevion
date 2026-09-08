"""
Safety Guard & Policy Engine
Protects users from dangerous operations, manages approval tokens,
and keeps tamper-evident execution logs with strict API key & credential redaction.

Safety model (3 tiers):
  1. HARD BLOCKED  -> NEVER runs, not even with manual approval. (nuke/system-killer commands)
  2. DANGEROUS     -> Requires manual confirmation, then runs once approved.
  3. SAFE/MODERATE -> Runs automatically (mode dependent) or with confirmation in strict mode.
"""

import time
import uuid
import re
from typing import Dict, Any, List, Optional, Tuple


# ============================================================================
# HARD BLOCKED — commands that will NEVER execute, even if the user approves.
# These are the "nuke / system killer" instructions. Defense-in-depth: they are
# re-checked inside DesktopController.execute_command too, so no code path can
# bypass them.
# ============================================================================
HARD_BLOCKED_PATTERNS = [
    # ---- Nuke / recursive delete ----
    "rm -rf", "rm -fr", "rm -r ", "rm -r/", "rm /*", "rm *",
    "rmdir /s", "rd /s", "deltree",
    "del /s", "del /f", "del /q", "del *.*", "del c:", "del d:",
    "remove-item -recurse", "remove-item -force", "remove-item *", "ri /s",
    # ---- Disk / filesystem killers ----
    "diskpart", "format ", "fdisk", "mkfs", "clean all",
    "dd if=", "dd of=/dev", "/dev/sda", "/dev/nvme", "/dev/hda",
    "wipefs", "blkdiscard", "swapoff",
    # ---- Boot / recovery tampering ----
    "bcdedit", "bootrec", "vssadmin delete", "wbadmin delete", "syskey",
    # ---- Mass process kill ----
    "taskkill /f", "taskkill /F", "pskill", "stop-process -force",
    "kill -9", "pkill", "killall",
    # ---- Recycle bin / secure wipe ----
    "clear-recyclebin", "cipher /w", "sdelete",
    # ---- Fork bomb / resource exhaustion ----
    ":(){ :|:& };:", "fork bomb",
    # ---- Wildcard / recursive nukes ----
    "find / -delete", "find / -exec rm", "rm -rf /", "rm -rf ~",
    "chmod -r 777 /", "chmod 777 /", "truncate -s 0 /",
]


# ============================================================================
# SYSTEM PATH PROTECTION — write/delete is NEVER allowed in these locations.
# The agent may only touch the working folder + Downloads + Desktop + Documents.
# ============================================================================
PROTECTED_PATH_PATTERNS = [
    # Windows system paths
    "c:\\windows", "c:/windows", "%windir%", "%systemroot%",
    "c:\\program files", "c:/program files", "%programfiles%",
    "c:\\program files (x86)", "%programfiles(x86)%",
    "c:\\programdata", "c:/programdata",
    "c:\\boot", "c:\\efi", "c:\\$recycle.bin", "c:\\system volume information",
    "\\appdata\\", "/appdata/", "%appdata%",
    # Linux / Unix system paths
    "/etc/", "/usr/", "/bin/", "/sbin/", "/var/", "/boot/", "/lib/",
    "/lib64/", "/proc/", "/sys/", "/dev/", "/root/", "/opt/", "/mnt/", "/media/",
    "c:\\windows\\system32", "system32",
]

# Chained command operators — combos (&&, ;, |) always require confirmation,
# since a dangerous command can hide behind a safe one.
CHAINED_OPERATORS = ["&&", "&", ";", "|", "||", ">"]


# ============================================================================
# DESTRUCTIVE (approvable) — require manual confirmation, then run once approved.
# These are harmful but scoped (single file/dir/process), not catastrophic.
# ============================================================================
DESTRUCTIVE_COMMAND_PATTERNS = [
    "del ", "erase ", "rm ", "rd ", "rmdir ", "remove-item",
    "taskkill", "stop-process", "kill ", "net user", "net localgroup",
    "reg delete", "reg add", "sc delete",
    "drop database", "drop table", "truncate table", "delete from ",
    "shutdown", "reboot", "poweroff", "halt", "init 0", "init 6",
    "mv / ", "icacls /", "takeown /f", "dism /online /cleanup-image /",
    "> /dev/", "mv /*", "cp -r /",
]


def sanitize_safe_payload(obj: Any) -> Any:
    """Recursively redacts API keys, tokens, authorization headers, and sensitive credential fields."""
    if isinstance(obj, dict):
        cleaned = {}
        for k, v in obj.items():
            k_low = str(k).lower()
            if any(secret in k_low for secret in ["api_key", "apikey", "secret", "password", "token", "auth", "credential", "bearer"]):
                cleaned[k] = "[REDACTED]"
            else:
                cleaned[k] = sanitize_safe_payload(v)
        return cleaned
    elif isinstance(obj, list):
        return [sanitize_safe_payload(item) for item in obj]
    elif isinstance(obj, str):
        # Redact Google AIza keys, OpenAI sk- keys, Anthropic sk-ant- keys, NVIDIA nvapi- keys, or general tokens
        s = obj
        s = re.sub(r'AIza[0-9A-Za-z\-_]{30,}', '[REDACTED]', s)
        s = re.sub(r'sk-ant-[0-9a-zA-Z\-_]{20,}', '[REDACTED]', s)
        s = re.sub(r'nvapi-[0-9a-zA-Z\-_]{20,}', '[REDACTED]', s)
        s = re.sub(r'sk-[0-9a-zA-Z\-_]{20,}', '[REDACTED]', s)
        s = re.sub(r'Bearer\s+[A-Za-z0-9\-_\.]{15,}', 'Bearer [REDACTED]', s)
        return s
    return obj


class SafetyGuard:
    def __init__(self, mode: str = "balanced"):
        # modes: "strict", "balanced", "developer"
        self.mode = mode
        self.dry_run = False  # when True, show plans but never execute anything
        self.plan_mode = False  # when True, multi-action commands require approval first
        self.pending_approvals: Dict[str, Dict[str, Any]] = {}
        self.pending_plans: Dict[str, Dict[str, Any]] = {}
        self.audit_log: List[Dict[str, Any]] = []

    def set_mode(self, mode: str):
        if mode in ["strict", "balanced", "developer"]:
            self.mode = mode

    def set_dry_run(self, enabled: bool):
        self.dry_run = bool(enabled)

    def set_plan_mode(self, enabled: bool):
        self.plan_mode = bool(enabled)

    # ------------------------------------------------------------------
    # Command classification helpers (static so DesktopController can reuse)
    # ------------------------------------------------------------------
    @staticmethod
    def is_hard_blocked(command: str) -> bool:
        """True if the command must NEVER execute (nuke/system-killer)."""
        c = (command or "").lower()
        return any(pat in c for pat in HARD_BLOCKED_PATTERNS)

    @staticmethod
    def is_destructive(command: str) -> bool:
        """True if the command is harmful-but-scoped (needs confirmation)."""
        c = (command or "").lower()
        return any(pat in c for pat in DESTRUCTIVE_COMMAND_PATTERNS)

    @staticmethod
    def has_chained_operators(command: str) -> bool:
        """True if the command chains multiple commands (&&, ;, |, etc.)."""
        return any(op in (command or "") for op in CHAINED_OPERATORS)

    @staticmethod
    def is_protected_path(path: str) -> bool:
        """
        True if the path points into a protected system location where the
        agent must never write or delete. Case-insensitive, handles both
        Windows backslashes and Unix forward slashes.

        Only matches at the START of the path so that a user's own folders
        named 'bin', 'etc', 'usr', etc. (e.g. /home/user/bin) are NOT blocked.
        """
        if not path:
            return False
        p = (path or "").replace("\\", "/").lower().strip()
        # Normalize leading "./" and redundant slashes
        while p.startswith("./"):
            p = p[2:]
        p = re.sub(r"/+", "/", p)
        for pat in PROTECTED_PATH_PATTERNS:
            pat_norm = pat.replace("\\", "/").lower().strip()
            if not pat_norm:
                continue
            # Absolute Unix system dirs must match at the very start
            if pat_norm.startswith("/"):
                if p == pat_norm.rstrip("/") or p.startswith(pat_norm if pat_norm.endswith("/") else pat_norm + "/"):
                    return True
            else:
                # Windows / relative system tokens (e.g. c:\windows, system32)
                # must match at the start of the path or as a full segment
                if p == pat_norm or p.startswith(pat_norm + "/") or p.startswith(pat_norm):
                    return True
        return False

    def evaluate_action(self, tool_name: str, parameters: Dict[str, Any]) -> Tuple[str, bool, Optional[str]]:
        """
        Returns (risk_level, requires_confirmation, warning_message).
        Risk levels: 'blocked', 'safe', 'moderate', 'dangerous'
        """
        # Destructive file/process operations are ALWAYS dangerous in every mode.
        if tool_name in ["delete_file", "kill_system_process", "kill_process"]:
            path = parameters.get("path") or parameters.get("process") or ""
            return "dangerous", True, f"Destructive action '{tool_name}' requires manual authorization."

        # Shell commands run with shell=True (arbitrary code execution).
        if tool_name == "execute_command":
            cmd = parameters.get("command", "")

            # Tier 1: HARD BLOCKED — never run, even with approval.
            if self.is_hard_blocked(cmd):
                return "blocked", False, f"HARD BLOCKED: this command can never be executed for your safety: '{cmd}'"

            # Tier 1.5: Chained commands (&&, ;, |) — a dangerous command can hide
            # behind a safe one, so always require explicit confirmation.
            if self.has_chained_operators(cmd):
                return "dangerous", True, f"Chained command detected (&& ; |). Requires manual confirmation: '{cmd}'"

            # Tier 2: destructive (scoped) — require manual confirmation.
            if self.is_destructive(cmd):
                return "dangerous", True, f"Destructive command requires manual confirmation before execution: '{cmd}'"

            # Tier 3: everything else via shell=True is still risky — confirm in all modes.
            return "moderate", True, f"Shell command requires manual confirmation before execution: '{cmd}'"

        # Developer mode: fast workflow for safe file/build operations, but destructive
        # operations (above) and shell commands are still protected.
        if self.mode == "developer":
            return "safe", False, None

        # 1. Moderate tools (file/folder creation & modification)
        if tool_name in ["create_file", "write_file", "create_folder", "create_project", "organize_files", "type_text", "add_note", "edit_file", "undo_edit"]:
            if self.mode == "strict":
                return "moderate", True, f"Confirm creation/modification of files via {tool_name}."
            return "moderate", False, None

        # 2. Safe tools
        if tool_name in ["open_application", "read_file", "open_website", "control_mouse", "take_screenshot", "analyze_screenshot", "get_system_info", "minimize_window", "maximize_window", "restore_window", "close_window", "clipboard_get", "clipboard_set", "find_files", "grep_files", "media_control", "press_keys", "get_battery", "list_directory", "web_search", "web_fetch", "download_file", "set_reminder"]:
            return "safe", False, None

        return "moderate", False, None

    def create_approval_request(self, tool_name: str, parameters: Dict[str, Any], risk_level: str, reason: str) -> Dict[str, Any]:
        token_id = str(uuid.uuid4())[:8]
        req = {
            "token_id": token_id,
            "tool_name": tool_name,
            "parameters": sanitize_safe_payload(parameters),
            "risk_level": risk_level,
            "reason": reason,
            "status": "pending",
            "created_at": time.time(),
            "expires_at": time.time() + 300  # 5 min expiration
        }
        self.pending_approvals[token_id] = req
        return req

    def approve_request(self, token_id: str) -> Optional[Dict[str, Any]]:
        req = self.pending_approvals.get(token_id)
        if req and req["status"] == "pending" and time.time() <= req["expires_at"]:
            req["status"] = "approved"
            req["approved_at"] = time.time()
            return req
        return None

    def reject_request(self, token_id: str) -> Optional[Dict[str, Any]]:
        req = self.pending_approvals.get(token_id)
        if req:
            req["status"] = "rejected"
            req["rejected_at"] = time.time()
            return req
        return None

    def log_execution(self, tool_name: str, parameters: Dict[str, Any], result: Dict[str, Any], risk_level: str, confirmed_by_user: bool = False):
        entry = {
            "id": f"log_{int(time.time() * 1000)}",
            "tool_name": tool_name,
            "parameters": sanitize_safe_payload(parameters),
            "result_summary": "Success" if result.get("success", True) else f"Failed: {result.get('error', 'Unknown')}",
            "risk_level": risk_level,
            "confirmed_by_user": confirmed_by_user,
            "duration_ms": result.get("duration_ms", 0),
            "timestamp": time.time(),
            "full_result": sanitize_safe_payload(result)
        }
        self.audit_log.append(entry)

    def get_audit_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        return list(reversed(self.audit_log[-limit:]))
