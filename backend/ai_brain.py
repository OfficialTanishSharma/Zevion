"""
AI Brain Reasoning Engine & Universal AI Provider Management Layer
Handles natural language intent recognition, structured action conversion,
context memory, multi-step compound planning, and pluggable AI providers
(Gemini, Claude, ChatGPT, Kimi, DeepSeek, Qwen, NVIDIA, and Built-in Semantic Engine).
Implements real API verification on key entry, error category classification,
multilingual & Hinglish natural command parsing, and strict UI clean naming.
"""

import os
import re
import json
import time
import difflib
import urllib.parse
import urllib.request
import urllib.error
import mimetypes
import base64
import uuid
from typing import Dict, Any, List, Optional, Tuple, Callable

# Attachment Configuration Constants
MAX_ATTACHMENTS_PER_MESSAGE = 5
MAX_ATTACHMENT_SIZE_MB = 25
MAX_TOTAL_ATTACHMENT_SIZE_MB = 50
MAX_ATTACHMENT_SIZE_BYTES = MAX_ATTACHMENT_SIZE_MB * 1024 * 1024
MAX_TOTAL_ATTACHMENT_SIZE_BYTES = MAX_TOTAL_ATTACHMENT_SIZE_MB * 1024 * 1024

# Rolling Window Attachment Rate Limit Constants
ATTACHMENT_RATE_LIMIT_COUNT = 20
ATTACHMENT_RATE_LIMIT_WINDOW_SECONDS = 600  # 10 minutes (600 seconds)

SUPPORTED_EXTENSIONS = {
    # Images
    ".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg",
    # Video
    ".mp4", ".webm", ".mov", ".mkv", ".avi",
    # Documents
    ".pdf",
    # Text
    ".txt", ".md", ".csv", ".json", ".xml", ".log", ".yaml", ".yml", ".ini", ".conf", ".env",
    # Code
    ".js", ".jsx", ".ts", ".tsx", ".py", ".java", ".c", ".cpp", ".h", ".hpp",
    ".html", ".css", ".sql", ".sh", ".bat", ".ps1", ".go", ".rs", ".php", ".rb", ".cs"
}

def format_file_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{round(size_bytes / 1024, 1)} KB"
    else:
        return f"{round(size_bytes / (1024 * 1024), 1)} MB"

def get_file_category(extension: str) -> str:
    ext = extension.lower()
    if ext in [".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg"]:
        return "image"
    elif ext in [".mp4", ".webm", ".mov", ".mkv", ".avi"]:
        return "video"
    elif ext in [".pdf"]:
        return "document"
    elif ext in [".js", ".jsx", ".ts", ".tsx", ".py", ".java", ".c", ".cpp", ".h", ".hpp", ".html", ".css", ".sql", ".sh", ".bat", ".ps1", ".go", ".rs", ".php", ".rb", ".cs"]:
        return "code"
    return "text"


class MemoryManager:
    """
    Manages Level 2 persistent primary/global memory across all conversations.
    Stores user preferences, preferred name, and explicitly saved memories.
    """
    def __init__(self, memory_path: Optional[str] = None):
        self.memory_path = memory_path or os.path.expanduser("~/.ai_desktop_memory.json")
        self.enabled: bool = True
        self.memories: List[Dict[str, Any]] = []
        self._load_memory()

    def _load_memory(self):
        if os.path.exists(self.memory_path) and os.path.getsize(self.memory_path) > 0:
            try:
                with open(self.memory_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.enabled = data.get("enabled", True)
                        self.memories = data.get("memories", [])
            except Exception as e:
                print(f"[MemoryManager] Load notice: {e}")

    def _save_memory(self):
        try:
            with open(self.memory_path, "w", encoding="utf-8") as f:
                json.dump({
                    "enabled": self.enabled,
                    "memories": self.memories
                }, f, indent=2)
        except Exception as e:
            print(f"[MemoryManager] Save notice: {e}")

    def list_memories(self) -> List[Dict[str, Any]]:
        return list(self.memories)

    def add_memory(self, key: str, value: str, text: str) -> Dict[str, Any]:
        mem_id = f"mem_{int(time.time() * 1000)}_{uuid.uuid4().hex[:6]}"
        existing = [m for m in self.memories if m.get("key") == key]
        if existing:
            existing[0]["value"] = value
            existing[0]["text"] = text
            existing[0]["updated_at"] = time.time()
            self._save_memory()
            return existing[0]
        else:
            mem = {
                "id": mem_id,
                "key": key,
                "value": value,
                "text": text,
                "created_at": time.time(),
                "updated_at": time.time()
            }
            self.memories.append(mem)
            self._save_memory()
            return mem

    def delete_memory(self, memory_id: str) -> bool:
        init_len = len(self.memories)
        self.memories = [m for m in self.memories if m.get("id") != memory_id]
        if len(self.memories) < init_len:
            self._save_memory()
            return True
        return False

    def clear_memories(self) -> bool:
        self.memories = []
        self._save_memory()
        return True

    def get_memory_value(self, key: str) -> Optional[str]:
        if not self.enabled:
            return None
        for m in self.memories:
            if m.get("key") == key:
                return m.get("value")
        return None

    def extract_memory_intent(self, text: str) -> Optional[Dict[str, str]]:
        """Detects if user is explicitly asking to remember information."""
        low = text.lower().strip()
        # "Remember that my name is xyz", "Remember my name is xyz", "Mera naam xyz yaad rakhna"
        m_name = re.search(r'\b(?:remember\s+(?:that\s+)?my\s+name\s+is|remember\s+my\s+name\s+is|yaad\s+rakhna\s+mera\s+naam|mera\s+naam\s+([a-zA-Z0-9]+)\s+yaad\s+rakhna)\s*([a-zA-Z0-9]+)?', low)
        if m_name:
            name_val = (m_name.group(2) or m_name.group(1) or "").strip().capitalize()
            if name_val:
                return {
                    "key": "user_name",
                    "value": name_val,
                    "text": f"User's name is {name_val}"
                }
        
        m_gen = re.search(r'\bremember\s+(?:that\s+)?(.+)$', text, re.IGNORECASE)
        if m_gen:
            fact = m_gen.group(1).strip()
            if fact:
                key_name = re.sub(r'[^\w]', '_', fact[:20].lower())
                return {
                    "key": key_name,
                    "value": fact,
                    "text": fact
                }
        return None

    def get_context_summary(self) -> str:
        if not self.enabled or not self.memories:
            return ""
        lines = [f"- {m.get('text', m.get('value'))}" for m in self.memories]
        return "Saved Long-Term Memory (Across Conversations):\n" + "\n".join(lines)


class AttachmentManager:
    """
    Manages safe local storage, validation, metadata generation, and content retrieval
    for file attachments uploaded to the Zevion.
    """
    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir or os.path.expanduser("~/.ai_desktop_attachments")
        os.makedirs(self.storage_dir, exist_ok=True)
        self.metadata_cache: Dict[str, Dict[str, Any]] = {}
        self._load_existing_attachments()

    def _get_rate_limit_file(self) -> str:
        return os.path.join(self.storage_dir, "rate_limit_history.json")

    def _load_rate_limit_history(self) -> List[float]:
        rf = self._get_rate_limit_file()
        if os.path.exists(rf) and os.path.getsize(rf) > 0:
            try:
                with open(rf, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        return [float(x) for x in data if isinstance(x, (int, float))]
            except Exception:
                pass
        return []

    def _save_rate_limit_history(self, timestamps: List[float]):
        rf = self._get_rate_limit_file()
        try:
            with open(rf, "w", encoding="utf-8") as f:
                json.dump(timestamps, f)
        except Exception:
            pass

    def get_rate_limit_status(self, now: Optional[float] = None) -> Dict[str, Any]:
        """
        Calculates rolling rate limit status over the 10-minute window.
        Returns: { accepted, current_used, max_allowed, remaining_slots, window_seconds, cooldown_remaining_seconds, next_reset_timestamp }
        """
        current_time = now if now is not None else time.time()
        window_start = current_time - ATTACHMENT_RATE_LIMIT_WINDOW_SECONDS

        history = self._load_rate_limit_history()
        active_timestamps = [t for t in history if t > window_start]

        if len(active_timestamps) != len(history):
            self._save_rate_limit_history(active_timestamps)

        current_used = len(active_timestamps)
        remaining_slots = max(0, ATTACHMENT_RATE_LIMIT_COUNT - current_used)
        is_limited = remaining_slots <= 0

        cooldown_remaining_seconds = 0
        next_reset_timestamp = None

        if active_timestamps:
            oldest_timestamp = min(active_timestamps)
            next_reset_timestamp = oldest_timestamp + ATTACHMENT_RATE_LIMIT_WINDOW_SECONDS
            if is_limited:
                cooldown_remaining_seconds = max(1, int(next_reset_timestamp - current_time))
            else:
                cooldown_remaining_seconds = 0

        return {
            "accepted": not is_limited,
            "current_used": current_used,
            "max_allowed": ATTACHMENT_RATE_LIMIT_COUNT,
            "remaining_slots": remaining_slots,
            "window_seconds": ATTACHMENT_RATE_LIMIT_WINDOW_SECONDS,
            "cooldown_remaining_seconds": cooldown_remaining_seconds,
            "next_reset_timestamp": next_reset_timestamp
        }

    def validate_rate_limit(self, incoming_count: int, now: Optional[float] = None) -> Tuple[bool, Optional[str], Dict[str, Any]]:
        """
        Validates whether incoming upload batch fits within the rolling rate limit window.
        """
        status = self.get_rate_limit_status(now=now)
        if status["remaining_slots"] < incoming_count:
            rem_sec = status["cooldown_remaining_seconds"] or 60
            mins = rem_sec // 60
            secs = rem_sec % 60
            if mins > 0:
                time_str = f"{mins} minute{'s' if mins != 1 else ''} {secs} second{'s' if secs != 1 else ''}"
            else:
                time_str = f"{secs} second{'s' if secs != 1 else ''}"
            err = f"Attachment limit reached. You can attach files again in {time_str}."
            return False, err, status
        return True, None, status

    def record_successful_uploads(self, count: int, now: Optional[float] = None):
        """
        Records timestamps for successfully accepted attachments in the rolling window.
        """
        if count <= 0:
            return
        current_time = now if now is not None else time.time()
        window_start = current_time - ATTACHMENT_RATE_LIMIT_WINDOW_SECONDS
        history = [t for t in self._load_rate_limit_history() if t > window_start]
        history.extend([current_time] * count)
        self._save_rate_limit_history(history)

    def _load_existing_attachments(self):
        """Discovers existing stored attachment files and recovers metadata."""
        if not os.path.exists(self.storage_dir):
            return
        try:
            for fname in os.listdir(self.storage_dir):
                if fname.endswith(".meta.json"):
                    meta_path = os.path.join(self.storage_dir, fname)
                    try:
                        with open(meta_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            if isinstance(data, dict) and "id" in data:
                                self.metadata_cache[data["id"]] = data
                    except Exception:
                        pass
        except Exception as e:
            print(f"[AttachmentManager] Cache load notice: {e}")

    def validate_file(self, filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        Validates file extension and individual file size against defined limits.
        """
        if not filename or not filename.strip():
            return False, "Invalid filename."
        
        _, ext = os.path.splitext(filename.lower())
        if not ext or ext not in SUPPORTED_EXTENSIONS:
            return False, f"That file type ({ext or 'unknown'}) isn't supported."

        if file_size > MAX_ATTACHMENT_SIZE_BYTES:
            return False, f"That file is too large ({format_file_size(file_size)}). The maximum size is {MAX_ATTACHMENT_SIZE_MB} MB."

        if file_size <= 0:
            return False, "File is empty (0 bytes)."

        return True, None

    def validate_batch(self, files_info: List[Tuple[str, int]]) -> Tuple[bool, Optional[str]]:
        """
        Validates total count and total combined size for a batch of files.
        """
        if len(files_info) > MAX_ATTACHMENTS_PER_MESSAGE:
            return False, f"You can attach at most {MAX_ATTACHMENTS_PER_MESSAGE} files per message."

        total_size = sum(sz for _, sz in files_info)
        if total_size > MAX_TOTAL_ATTACHMENT_SIZE_BYTES:
            return False, f"Total attachment size ({format_file_size(total_size)}) exceeds the maximum limit of {MAX_TOTAL_ATTACHMENT_SIZE_MB} MB."

        for fname, sz in files_info:
            ok, err = self.validate_file(fname, sz)
            if not ok:
                return False, err

        return True, None

    def save_attachment(self, filename: str, content_bytes: bytes, mime_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Safely saves attachment bytes with a unique ID and sanitized name.
        Returns safe metadata dict without exposing internal filesystem paths.
        """
        file_size = len(content_bytes)
        ok, err = self.validate_file(filename, file_size)
        if not ok:
            raise ValueError(err)

        clean_orig_name = os.path.basename(filename.strip().replace("\\", "/"))
        clean_orig_name = re.sub(r'[^\w\.\-\s_]', '_', clean_orig_name)
        _, ext = os.path.splitext(clean_orig_name.lower())

        att_id = f"att_{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
        safe_disk_filename = f"{att_id}_{clean_orig_name}"
        disk_path = os.path.join(self.storage_dir, safe_disk_filename)

        with open(disk_path, "wb") as f:
            f.write(content_bytes)

        if not mime_type or mime_type == "application/octet-stream":
            guessed_mime, _ = mimetypes.guess_type(clean_orig_name)
            mime_type = guessed_mime or "application/octet-stream"

        category = get_file_category(ext)

        meta = {
            "id": att_id,
            "filename": clean_orig_name,
            "extension": ext,
            "mime_type": mime_type,
            "size_bytes": file_size,
            "size_formatted": format_file_size(file_size),
            "category": category,
            "timestamp": time.time(),
            "_disk_path": disk_path
        }

        meta_disk_path = os.path.join(self.storage_dir, f"{att_id}.meta.json")
        try:
            with open(meta_disk_path, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)
        except Exception:
            pass

        self.metadata_cache[att_id] = meta

        return {
            "id": att_id,
            "filename": clean_orig_name,
            "extension": ext,
            "mime_type": mime_type,
            "size_bytes": file_size,
            "size_formatted": format_file_size(file_size),
            "category": category,
            "timestamp": meta["timestamp"]
        }

    def get_attachment_path(self, attachment_id: str) -> Optional[str]:
        """Resolves full disk path safely, preventing traversal."""
        clean_id = re.sub(r'[^\w\-]', '', attachment_id)
        if clean_id in self.metadata_cache:
            disk_p = self.metadata_cache[clean_id].get("_disk_path")
            if disk_p and os.path.exists(disk_p):
                return disk_p

        if os.path.exists(self.storage_dir):
            for fname in os.listdir(self.storage_dir):
                if fname.startswith(f"{clean_id}_") and not fname.endswith(".meta.json"):
                    full_p = os.path.join(self.storage_dir, fname)
                    if os.path.exists(full_p):
                        return full_p
        return None

    def get_attachment_metadata(self, attachment_id: str) -> Optional[Dict[str, Any]]:
        clean_id = re.sub(r'[^\w\-]', '', attachment_id)
        if clean_id in self.metadata_cache:
            m = dict(self.metadata_cache[clean_id])
            m.pop("_disk_path", None)
            return m
        return None

    def read_attachment_bytes(self, attachment_id: str) -> Optional[bytes]:
        path = self.get_attachment_path(attachment_id)
        if path and os.path.exists(path):
            try:
                with open(path, "rb") as f:
                    return f.read()
            except Exception:
                return None
        return None

    def read_attachment_base64(self, attachment_id: str) -> Optional[str]:
        data = self.read_attachment_bytes(attachment_id)
        if data:
            return base64.b64encode(data).decode("utf-8")
        return None

    def read_attachment_text(self, attachment_id: str, max_chars: int = 30000) -> Optional[str]:
        """Reads text/code/data file safely with intelligent truncation."""
        data = self.read_attachment_bytes(attachment_id)
        if data is None:
            return None

        path = self.get_attachment_path(attachment_id)
        if path and path.lower().endswith(".pdf"):
            return self.extract_pdf_text(path, max_chars=max_chars)

        for enc in ["utf-8", "utf-16", "latin-1", "ascii"]:
            try:
                txt = data.decode(enc)
                if len(txt) > max_chars:
                    return txt[:max_chars] + f"\n... [Truncated: showing first {max_chars} characters of {len(txt)} total]"
                return txt
            except Exception:
                continue
        return None

    def extract_pdf_text(self, pdf_path: str, max_chars: int = 30000) -> str:
        """Extracts text from PDF using pypdf with graceful fallback."""
        try:
            from pypdf import PdfReader
            reader = PdfReader(pdf_path)
            extracted = []
            for i, page in enumerate(reader.pages):
                p_text = page.extract_text() or ""
                if p_text.strip():
                    extracted.append(f"--- Page {i + 1} ---\n{p_text}")
                if sum(len(x) for x in extracted) > max_chars:
                    break
            full_text = "\n\n".join(extracted)
            if len(full_text) > max_chars:
                return full_text[:max_chars] + f"\n... [Truncated: showing first {max_chars} characters]"
            return full_text or "PDF document loaded (no extractable text layer found)."
        except Exception as e:
            return f"PDF document loaded (unable to extract text locally: {e})."

    def delete_attachment(self, attachment_id: str) -> bool:
        path = self.get_attachment_path(attachment_id)
        meta_path = os.path.join(self.storage_dir, f"{attachment_id}.meta.json")
        deleted = False
        if path and os.path.exists(path):
            try:
                os.remove(path)
                deleted = True
            except Exception:
                pass
        if os.path.exists(meta_path):
            try:
                os.remove(meta_path)
                deleted = True
            except Exception:
                pass
        self.metadata_cache.pop(attachment_id, None)
        return deleted


class BaseAIProvider:
    """Base interface for all AI reasoning providers."""
    def __init__(self, provider_id: str, display_name: str, requires_key: bool = True):
        self.provider_id = provider_id
        self.display_name = display_name
        self.requires_key = requires_key
        self.api_key: str = ""
        self.enabled: bool = False
        self.is_configured: bool = False
        self._test_verification_hook: Optional[Callable[[str], Tuple[bool, str, str]]] = None
        self._test_query_hook: Optional[Callable[..., Optional[str]]] = None
        self.last_error_type: str = "valid"
        self.last_error_message: str = ""

    def _sanitize_conversational_text(self, text: str) -> str:
        if not text:
            return ""
        raw = text.strip()

        # Extract response from Markdown JSON or direct JSON if present
        if "```" in raw and ("response" in raw or "actions" in raw):
            try:
                json_m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
                if json_m:
                    d = json.loads(json_m.group(1))
                    if "response" in d and d["response"]:
                        return self._sanitize_conversational_text(d["response"])
            except Exception:
                pass

        if raw.startswith("{") and raw.endswith("}") and ("\"response\"" in raw or "'response'" in raw):
            try:
                d = json.loads(raw)
                if "response" in d and d["response"]:
                    return self._sanitize_conversational_text(d["response"])
            except Exception:
                pass

        # Check for explicit "Final Answer:", "Final Response:", "Chosen Response:", "Response:" marker at the end
        final_marker = re.search(r"(?:^|\n)(?:\*{0,2}final\s+(?:answer|response)|chosen\s+response|\*{0,2}response)[:\s]+(.+)$", raw, re.IGNORECASE | re.DOTALL)
        if final_marker:
            raw = final_marker.group(1).strip()

        lines = raw.split("\n")
        filtered_lines = []
        forbidden_prefixes = (
            "the user said", "the user says", "the user is", "the user wants",
            "the user introduced", "the user is introducing", "the user asks", "the user asked",
            "user says:", "user said:", "user input:", "user query:", "user persona:", "user persona",
            "friendly, conversational ai", "ai desktop assistant", "autonomous ai desktop agent",
            "i am an ai desktop assistant",
            "role:", "persona:",
            "language:", "tone:", "length:",
            "rule:", "rules:", "rule 1:", "rule 2:", "rule 3:", "rules to follow:",
            "plan:", "plan 1:", "step 1:", "step 2:", "step 3:", "step 4:", "step 5:",
            "analysis:", "internal reasoning:", "reasoning:", "thinking:", "thought process:",
            "candidate:", "candidates:", "candidate 1:", "candidate 2:", "candidate 3:", "candidate 1", "candidate 2",
            "option 1:", "option 2:", "option 3:", "option 4:", "option 5:", "option 1", "option 2", "option 3",
            "draft:", "draft 1:", "draft 2:", "draft 3:", "draft 1", "draft 2",
            "selected:", "selected option", "chosen:", "picked:",
            "short?", "natural/casual?", "matches tone?", "check:", "checklist:",
            "simple, fits", "fits the", "word limit", "5-25 word"
        )

        for line in lines:
            l_str = line.strip()
            l_low = l_str.lower()
            if not l_str:
                continue

            if any(l_low.startswith(fp) for fp in forbidden_prefixes):
                continue

            if any(bad in l_low for bad in ["fits the 5-25", "word limit", "short? yes", "matches tone? yes", "natural/casual? yes", "simple, fits"]):
                continue

            if l_low.rstrip(":!.") in ["rule", "rules", "perfect", "selected", "chosen", "options", "candidates", "drafts", "analysis", "plan", "reasoning", "thinking", "evaluation", "checklist"]:
                continue

            if (l_str.startswith("-") or l_str.startswith("*") or l_str.startswith("•")) and any(kw in raw.lower() for kw in ["option", "rules", "rule:", "user says", "user said", "the user", "tone:", "candidate", "draft", "plan:"]):
                continue

            if re.match(r"^\d+\.\s+(?:greet|ask|say|check|analyze|respond|output|verify|confirm)\b", l_low):
                continue

            if re.match(r"^(?:final\s+(?:answer|response)|chosen\s+response|response)[:\s]+", l_low):
                clean_ans = re.sub(r"^(?:final\s+(?:answer|response)|chosen\s+response|response)[:\s]+", "", l_str, flags=re.IGNORECASE).strip("\"' ")
                if clean_ans:
                    filtered_lines.append(clean_ans)
                continue

            filtered_lines.append(l_str)

        result = "\n".join(filtered_lines).strip()
        if (result.startswith("\"") and result.endswith("\"")) or (result.startswith("'") and result.endswith("'")):
            result = result[1:-1].strip()

        # Deduplicate repeated identical lines
        res_lines = [l.strip() for l in result.split("\n") if l.strip()]
        if res_lines:
            seen = set()
            deduped = []
            for l in res_lines:
                if l.lower() not in seen:
                    seen.add(l.lower())
                    deduped.append(l)
            result = " ".join(deduped)

        return result or raw

    def configure(self, api_key: str, enabled: bool = True):
        clean_key = (api_key or "").strip()
        self.api_key = clean_key
        self.is_configured = bool(clean_key) if self.requires_key else True
        self.enabled = enabled and self.is_configured

    def disable(self):
        self.enabled = False

    def enable(self):
        if self.is_configured or not self.requires_key:
            self.enabled = True

    def remove_key(self):
        self.api_key = ""
        self.is_configured = False
        self.enabled = False

    def get_masked_key(self) -> str:
        if not self.api_key:
            return ""
        if len(self.api_key) <= 8:
            return "••••••••"
        return f"{self.api_key[:4]}••••••••{self.api_key[-4:]}"

    def to_dict(self, is_active: bool = False) -> Dict[str, Any]:
        """Returns safe metadata showing ONLY the clean AI name, never technical model strings."""
        status = "Enabled" if self.enabled else ("Disabled" if self.is_configured else "Not configured")
        return {
            "id": self.provider_id,
            "name": self.display_name,
            "display_name": self.display_name,
            "requires_key": self.requires_key,
            "is_configured": self.is_configured,
            "enabled": self.enabled,
            "status": status,
            "has_key": bool(self.api_key),
            "masked_key": self.get_masked_key(),
            "is_active": is_active
        }

    def verify_key(self, api_key: str) -> Tuple[bool, str, str]:
        """
        Performs lightweight real authentication verification.
        Returns: (is_valid, error_type, user_friendly_message)
        error_type: 'valid', 'invalid_key', 'rate_limit', 'network_error', 'server_error'
        """
        raise NotImplementedError

    def query(self, prompt: str, system_prompt: str, conversation_context: Optional[List[Dict[str, Any]]] = None, attachments: Optional[List[Dict[str, Any]]] = None, attachment_manager: Optional[Any] = None) -> Optional[str]:
        raise NotImplementedError


class GeminiProvider(BaseAIProvider):
    def __init__(self):
        super().__init__("gemini", "Gemini", requires_key=True)
        self.available_models: List[str] = []

    def verify_key(self, api_key: str) -> Tuple[bool, str, str]:
        clean_key = (api_key or "").strip("'\" \t\r\n")
        # Reject empty or short keys ("A", "123", "hello")
        if not clean_key or len(clean_key) < 10:
            self.last_error_type = "invalid_key"
            self.last_error_message = "Gemini API key is invalid. Please check your key and try again."
            return False, "invalid_key", self.last_error_message

        # Support safe test hook for mocked environments
        if self._test_verification_hook:
            return self._test_verification_hook(clean_key)

        try:
            encoded_key = urllib.parse.quote_plus(clean_key)
            url = f"https://generativelanguage.googleapis.com/v1beta/models?key={encoded_key}"
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": clean_key
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                if resp.status in [200, 201]:
                    try:
                        raw_data = json.loads(resp.read().decode("utf-8"))
                        discovered = []
                        for m in raw_data.get("models", []):
                            m_name = m.get("name", "")
                            methods = m.get("supportedGenerationMethods", [])
                            if "generateContent" in methods:
                                clean_name = m_name.replace("models/", "")
                                discovered.append(clean_name)
                        if discovered:
                            self.available_models = discovered
                    except Exception:
                        pass
                    self.last_error_type = "valid"
                    self.last_error_message = "Gemini API key verified successfully."
                    return True, "valid", self.last_error_message
        except urllib.error.HTTPError as e:
            if e.code in [400, 401, 403]:
                self.last_error_type = "invalid_key"
                self.last_error_message = "Gemini API key is invalid. Please check your key and try again."
                return False, "invalid_key", self.last_error_message
            elif e.code == 429:
                self.last_error_type = "rate_limit"
                self.last_error_message = "Gemini rate limit or quota exceeded. Please check your account billing or try again later."
                return False, "rate_limit", self.last_error_message
            elif e.code == 404:
                self.last_error_type = "model_error"
                self.last_error_message = "Gemini model or endpoint not found. Please check API version compatibility."
                return False, "model_error", self.last_error_message
            elif e.code >= 500:
                self.last_error_type = "server_error"
                self.last_error_message = "Gemini server is temporarily unavailable. Please try again later."
                return False, "server_error", self.last_error_message
            else:
                self.last_error_type = "invalid_key"
                self.last_error_message = "Gemini API key is invalid. Please check your key and try again."
                return False, "invalid_key", self.last_error_message
        except (urllib.error.URLError, TimeoutError, OSError):
            self.last_error_type = "network_error"
            self.last_error_message = "Gemini network or connection error. Please check your internet connection."
            return False, "network_error", self.last_error_message
        except Exception:
            self.last_error_type = "network_error"
            self.last_error_message = "Gemini network or connection error. Please check your internet connection."
            return False, "network_error", self.last_error_message

        return False, "invalid_key", "Gemini API key is invalid. Please check your key and try again."

    def _sanitize_conversational_text(self, text: str) -> str:
        return super()._sanitize_conversational_text(text)

    def query(self, prompt: str, system_prompt: str, conversation_context: Optional[List[Dict[str, Any]]] = None, attachments: Optional[List[Dict[str, Any]]] = None, attachment_manager: Optional[Any] = None) -> Optional[str]:
        if not self.enabled or not self.api_key:
            return None

        if self._test_query_hook:
            try:
                raw_test = self._test_query_hook(prompt, system_prompt, conversation_context, attachments)
            except TypeError:
                try:
                    raw_test = self._test_query_hook(prompt, system_prompt, conversation_context)
                except TypeError:
                    try:
                        raw_test = self._test_query_hook(prompt, system_prompt)
                    except TypeError:
                        raw_test = self._test_query_hook(prompt)
            return raw_test

        clean_key = (self.api_key or "").strip("'\" \t\r\n")
        if not clean_key:
            return None

        preferred_order = [
            "gemini-1.5-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-flash-8b",
            "gemini-2.0-flash",
            "gemini-1.5-pro"
        ]
        candidate_models = []
        if self.available_models:
            for pref in preferred_order:
                if pref in self.available_models and pref not in candidate_models:
                    candidate_models.append(pref)
            for m in self.available_models:
                clean_m = m.replace("models/", "").strip()
                if clean_m not in candidate_models:
                    candidate_models.append(clean_m)
        if not candidate_models:
            candidate_models = preferred_order

        encoded_key = urllib.parse.quote_plus(clean_key)

        # Build contents array with multi-turn conversation context
        contents = []
        if conversation_context:
            for msg in conversation_context:
                role = "user" if msg.get("role") == "user" else "model"
                text = str(msg.get("content", "")).strip()
                prior_atts = msg.get("attachments", [])
                if prior_atts and attachment_manager:
                    att_summaries = []
                    for pa in prior_atts:
                        pa_id = pa.get("id")
                        pa_name = pa.get("filename", "file")
                        pa_cat = pa.get("category", "")
                        if pa_cat in ["text", "code", "document"]:
                            pa_txt = attachment_manager.read_attachment_text(pa_id, max_chars=3000)
                            if pa_txt:
                                att_summaries.append(f"[Previous attachment: {pa_name}]\n{pa_txt}")
                    if att_summaries:
                        text = f"{text}\n\n" + "\n\n".join(att_summaries)

                if text:
                    contents.append({
                        "role": role,
                        "parts": [{"text": text}]
                    })
        
        # Build current user turn parts
        current_turn_parts = [{"text": prompt}]
        if attachments and attachment_manager:
            for att in attachments:
                att_id = att.get("id")
                att_name = att.get("filename", "file")
                att_mime = att.get("mime_type", "application/octet-stream")
                att_cat = att.get("category", "")

                if att_cat == "image":
                    b64_data = attachment_manager.read_attachment_base64(att_id)
                    if b64_data:
                        current_turn_parts.append({
                            "inlineData": {
                                "mimeType": att_mime,
                                "data": b64_data
                            }
                        })
                elif att_cat == "document" and att_mime == "application/pdf":
                    b64_data = attachment_manager.read_attachment_base64(att_id)
                    if b64_data:
                        current_turn_parts.append({
                            "inlineData": {
                                "mimeType": "application/pdf",
                                "data": b64_data
                            }
                        })
                    else:
                        doc_text = attachment_manager.read_attachment_text(att_id, max_chars=20000)
                        if doc_text:
                            current_turn_parts.append({
                                "text": f"\n\n[Attached PDF: {att_name}]\n{doc_text}\n"
                            })
                else:
                    file_text = attachment_manager.read_attachment_text(att_id, max_chars=25000)
                    if file_text:
                        ext_clean = att.get("extension", "").lstrip(".")
                        current_turn_parts.append({
                            "text": f"\n\n[Attached file: {att_name}]\n```{ext_clean}\n{file_text}\n```\n"
                        })

        contents.append({
            "role": "user",
            "parts": current_turn_parts
        })

        for model in candidate_models:
            clean_model = model.replace("models/", "").strip()
            safe_endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{clean_model}:generateContent"
            req_url = f"{safe_endpoint}?key={encoded_key}"
            
            payload = {
                "system_instruction": {
                    "parts": [
                        {"text": system_prompt}
                    ]
                },
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.3,
                    "maxOutputTokens": 1000
                }
            }

            req_data = json.dumps(payload).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "x-goog-api-key": clean_key
            }

            try:
                req = urllib.request.Request(req_url, data=req_data, headers=headers)
                with urllib.request.urlopen(req, timeout=12.0) as resp:
                    status_code = resp.status
                    if status_code in [200, 201]:
                        raw_body = resp.read().decode("utf-8")
                        data = json.loads(raw_body)
                        candidates = data.get("candidates", [])
                        if candidates:
                            content = candidates[0].get("content", {})
                            parts = content.get("parts", [])
                            if parts:
                                text_parts = [p.get("text", "") for p in parts if "text" in p]
                                if text_parts:
                                    raw_text = "".join(text_parts).strip()
                                    res_text = self._sanitize_conversational_text(raw_text)
                                    self.last_error_type = "valid"
                                    self.last_error_message = ""
                                    print(f"[Gemini Chat Diagnostics] active_provider=gemini configured={self.is_configured} enabled={self.enabled} has_key={bool(self.api_key)} model={clean_model} status={status_code} result_len={len(res_text)}")
                                    return res_text
            except urllib.error.HTTPError as e:
                safe_reason = "UNKNOWN"
                err_msg = ""
                safe_err_detail = f"HTTP {e.code}"
                try:
                    raw_err = e.read().decode("utf-8", errors="replace")
                    err_json = json.loads(raw_err)
                    err_obj = err_json.get("error", {})
                    err_code = err_obj.get("code", e.code)
                    err_status = err_obj.get("status", "")
                    err_msg = err_obj.get("message", "")
                    details = err_obj.get("details", [])
                    reasons = []
                    for d in details:
                        if isinstance(d, dict) and "reason" in d:
                            reasons.append(d["reason"])
                    safe_reason = ", ".join(reasons) if reasons else err_status
                    safe_err_detail = f"status={err_status} code={err_code} reason={safe_reason} message={err_msg}"
                except Exception:
                    pass

                print(f"[Gemini Chat Diagnostics] active_provider=gemini configured={self.is_configured} enabled={self.enabled} has_key={bool(self.api_key)} model={clean_model} endpoint={safe_endpoint} status={e.code} reason={safe_reason} details={safe_err_detail}")

                if e.code in [401, 403]:
                    self.last_error_type = "invalid_key"
                    self.last_error_message = f"Gemini authentication failed ({err_msg or 'Invalid API key'}). Please check your API key in Settings."
                    break
                elif e.code == 429:
                    self.last_error_type = "rate_limit"
                    self.last_error_message = f"Gemini quota/rate limit exceeded on model '{clean_model}' ({err_msg or 'Resource exhausted'}). Please check your Google AI Studio plan and billing details."
                    # Continue attempting other candidate models that might have available quota
                    continue
                elif e.code == 404:
                    self.last_error_type = "model_error"
                    self.last_error_message = f"Gemini model '{clean_model}' was not found. Trying next compatible model."
                    continue
                elif e.code == 400:
                    self.last_error_type = "invalid_key"
                    self.last_error_message = f"Gemini request rejected for model '{clean_model}' ({err_msg or 'Bad Request'})."
                    continue
                elif e.code >= 500:
                    self.last_error_type = "server_error"
                    self.last_error_message = "Gemini server is temporarily unavailable. Please try again later."
                    continue
            except (urllib.error.URLError, TimeoutError, OSError) as e:
                print(f"[Gemini Chat Diagnostics] active_provider=gemini configured={self.is_configured} enabled={self.enabled} has_key={bool(self.api_key)} model={clean_model} endpoint={safe_endpoint} status=NetworkError exception={type(e).__name__}")
                self.last_error_type = "network_error"
                self.last_error_message = "Gemini network or connection error. Please check your internet connection."
                continue
            except Exception as e:
                print(f"[Gemini Chat Diagnostics] active_provider=gemini configured={self.is_configured} enabled={self.enabled} has_key={bool(self.api_key)} model={clean_model} endpoint={safe_endpoint} status=Exception exception={type(e).__name__}")
                self.last_error_type = "network_error"
                self.last_error_message = "Gemini encountered an unexpected connection error."
                continue

        return None


class ClaudeProvider(BaseAIProvider):
    def __init__(self):
        super().__init__("claude", "Claude", requires_key=True)

    def verify_key(self, api_key: str) -> Tuple[bool, str, str]:
        clean_key = (api_key or "").strip()
        if not clean_key or not clean_key.startswith("sk-ant-"):
            return False, "invalid_key", "Claude API key is invalid. Please check your key and try again."

        if self._test_verification_hook:
            return self._test_verification_hook(clean_key)

        try:
            url = "https://api.anthropic.com/v1/messages"
            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 1,
                "messages": [{"role": "user", "content": "ping"}]
            }
            headers = {
                "Content-Type": "application/json",
                "x-api-key": clean_key,
                "anthropic-version": "2023-06-01"
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                if resp.status in [200, 201]:
                    return True, "valid", "Claude API key verified successfully."
        except urllib.error.HTTPError as e:
            if e.code in [401, 403]:
                return False, "invalid_key", "Claude API key is invalid. Please check your key and try again."
            elif e.code == 429:
                return False, "rate_limit", "Claude rate limit or quota exceeded. Please check your account or try again later."
            elif e.code >= 500:
                return False, "server_error", "Claude server is temporarily unavailable. Please try again later."
            else:
                return False, "invalid_key", "Claude API key is invalid. Please check your key and try again."
        except (urllib.error.URLError, TimeoutError, OSError):
            return False, "network_error", "Claude network or connection error. Please check your internet connection."
        except Exception:
            return False, "network_error", "Claude network or connection error. Please check your internet connection."

        return False, "invalid_key", "Claude API key is invalid. Please check your key and try again."

    def query(self, prompt: str, system_prompt: str, conversation_context: Optional[List[Dict[str, Any]]] = None, attachments: Optional[List[Dict[str, Any]]] = None, attachment_manager: Optional[Any] = None) -> Optional[str]:
        if self._test_query_hook:
            try:
                return self._test_query_hook(prompt, system_prompt)
            except TypeError:
                return self._test_query_hook(prompt)

        if not self.enabled or not self.api_key:
            return None

        try:
            url = "https://api.anthropic.com/v1/messages"
            messages = []
            if conversation_context:
                for m in conversation_context:
                    role = "user" if m.get("role") == "user" else "assistant"
                    text = str(m.get("content", "")).strip()
                    if text:
                        messages.append({"role": role, "content": text})
            
            prompt_with_attachments = prompt
            if attachments and attachment_manager:
                att_texts = []
                for att in attachments:
                    txt = attachment_manager.read_attachment_text(att["id"], max_chars=15000)
                    if txt:
                        att_texts.append(f"\n\n[Attached file: {att.get('filename')}]\n{txt}\n")
                if att_texts:
                    prompt_with_attachments += "\n" + "\n".join(att_texts)

            messages.append({"role": "user", "content": prompt_with_attachments})

            payload = {
                "model": "claude-3-5-sonnet-20241022",
                "max_tokens": 300,
                "system": system_prompt,
                "messages": messages
            }
            headers = {
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                content = data.get("content", [])
                if content and isinstance(content, list):
                    return content[0].get("text", "")
        except Exception:
            return None
        return None


class ChatGPTProvider(BaseAIProvider):
    def __init__(self):
        super().__init__("chatgpt", "ChatGPT", requires_key=True)

    def verify_key(self, api_key: str) -> Tuple[bool, str, str]:
        clean_key = (api_key or "").strip()
        if not clean_key or not clean_key.startswith("sk-"):
            return False, "invalid_key", "ChatGPT API key is invalid. Please check your key and try again."

        if self._test_verification_hook:
            return self._test_verification_hook(clean_key)

        try:
            url = "https://api.openai.com/v1/models"
            headers = {
                "Authorization": f"Bearer {clean_key}"
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                if resp.status == 200:
                    return True, "valid", "ChatGPT API key verified successfully."
        except urllib.error.HTTPError as e:
            if e.code in [401, 403]:
                return False, "invalid_key", "ChatGPT API key is invalid. Please check your key and try again."
            elif e.code == 429:
                return False, "rate_limit", "ChatGPT rate limit or quota exceeded. Please check your account or try again later."
            elif e.code >= 500:
                return False, "server_error", "ChatGPT server is temporarily unavailable. Please try again later."
            else:
                return False, "invalid_key", "ChatGPT API key is invalid. Please check your key and try again."
        except (urllib.error.URLError, TimeoutError, OSError):
            return False, "network_error", "ChatGPT network or connection error. Please check your internet connection."
        except Exception:
            return False, "network_error", "ChatGPT network or connection error. Please check your internet connection."

        return False, "invalid_key", "ChatGPT API key is invalid. Please check your key and try again."

    def query(self, prompt: str, system_prompt: str, conversation_context: Optional[List[Dict[str, Any]]] = None, attachments: Optional[List[Dict[str, Any]]] = None, attachment_manager: Optional[Any] = None) -> Optional[str]:
        if self._test_query_hook:
            try:
                return self._test_query_hook(prompt, system_prompt)
            except TypeError:
                return self._test_query_hook(prompt)

        if not self.enabled or not self.api_key:
            return None

        try:
            url = "https://api.openai.com/v1/chat/completions"
            messages = [{"role": "system", "content": system_prompt}]
            if conversation_context:
                for m in conversation_context:
                    role = "user" if m.get("role") == "user" else "assistant"
                    text = str(m.get("content", "")).strip()
                    if text:
                        messages.append({"role": role, "content": text})
            
            prompt_with_attachments = prompt
            if attachments and attachment_manager:
                att_texts = []
                for att in attachments:
                    txt = attachment_manager.read_attachment_text(att["id"], max_chars=15000)
                    if txt:
                        att_texts.append(f"\n\n[Attached file: {att.get('filename')}]\n{txt}\n")
                if att_texts:
                    prompt_with_attachments += "\n" + "\n".join(att_texts)

            messages.append({"role": "user", "content": prompt_with_attachments})

            payload = {
                "model": "gpt-4o-mini",
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 300
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
        except Exception:
            return None
        return None


class NVIDIAProvider(BaseAIProvider):
    def __init__(self):
        super().__init__("nvidia", "NVIDIA", requires_key=True)
        self._internal_models = {
            "kimi": "moonshotai/moonshot-v1-8k",
            "deepseek": "deepseek-ai/deepseek-r1",
            "qwen": "qwen/qwen2.5-72b-instruct"
        }
        self.active_nvidia_choice = "kimi"

    def set_choice(self, choice: str):
        c_low = choice.lower().strip()
        if c_low in self._internal_models:
            self.active_nvidia_choice = c_low

    def verify_key(self, api_key: str) -> Tuple[bool, str, str]:
        clean_key = (api_key or "").strip()
        if not clean_key or not clean_key.startswith("nvapi-"):
            return False, "invalid_key", "NVIDIA API key is invalid. Please check your key and try again."

        if self._test_verification_hook:
            return self._test_verification_hook(clean_key)

        try:
            url = "https://integrate.api.nvidia.com/v1/models"
            headers = {
                "Authorization": f"Bearer {clean_key}"
            }
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                if resp.status == 200:
                    return True, "valid", "NVIDIA API key verified successfully."
        except urllib.error.HTTPError as e:
            if e.code in [401, 403]:
                return False, "invalid_key", "NVIDIA API key is invalid. Please check your key and try again."
            elif e.code == 429:
                return False, "rate_limit", "NVIDIA rate limit or quota exceeded. Please check your account or try again later."
            elif e.code >= 500:
                return False, "server_error", "NVIDIA server is temporarily unavailable. Please try again later."
            else:
                return False, "invalid_key", "NVIDIA API key is invalid. Please check your key and try again."
        except (urllib.error.URLError, TimeoutError, OSError):
            return False, "network_error", "NVIDIA network or connection error. Please check your internet connection."
        except Exception:
            return False, "network_error", "NVIDIA network or connection error. Please check your internet connection."

        return False, "invalid_key", "NVIDIA API key is invalid. Please check your key and try again."

    def query(self, prompt: str, system_prompt: str, specific_choice: Optional[str] = None, conversation_context: Optional[List[Dict[str, Any]]] = None, attachments: Optional[List[Dict[str, Any]]] = None, attachment_manager: Optional[Any] = None) -> Optional[str]:
        choice_to_use = specific_choice or self.active_nvidia_choice
        if self._test_query_hook:
            try:
                return self._test_query_hook(prompt, choice_to_use)
            except TypeError:
                try:
                    return self._test_query_hook(prompt, system_prompt)
                except TypeError:
                    return self._test_query_hook(prompt)

        if not self.enabled or not self.api_key:
            return None

        try:
            url = "https://integrate.api.nvidia.com/v1/chat/completions"
            internal_model = self._internal_models.get(choice_to_use, "deepseek-ai/deepseek-r1")
            messages = [{"role": "system", "content": system_prompt}]
            if conversation_context:
                for m in conversation_context:
                    role = "user" if m.get("role") == "user" else "assistant"
                    text = str(m.get("content", "")).strip()
                    if text:
                        messages.append({"role": role, "content": text})
            
            prompt_with_attachments = prompt
            if attachments and attachment_manager:
                att_texts = []
                for att in attachments:
                    txt = attachment_manager.read_attachment_text(att["id"], max_chars=15000)
                    if txt:
                        att_texts.append(f"\n\n[Attached file: {att.get('filename')}]\n{txt}\n")
                if att_texts:
                    prompt_with_attachments += "\n" + "\n".join(att_texts)

            messages.append({"role": "user", "content": prompt_with_attachments})

            payload = {
                "model": internal_model,
                "messages": messages,
                "temperature": 0.2,
                "max_tokens": 300
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
        except Exception:
            return None
        return None


class DirectNamedProvider(BaseAIProvider):
    """Direct provider representations for Kimi, DeepSeek, Qwen."""
    def __init__(self, provider_id: str, display_name: str, nvidia_ref: Optional[NVIDIAProvider] = None):
        super().__init__(provider_id, display_name, requires_key=True)
        self.nvidia_ref = nvidia_ref
        self._configured = False
        self._enabled = False

    @property
    def is_configured(self) -> bool:
        if self._configured or bool(self.api_key):
            return True
        return bool(self.nvidia_ref and self.nvidia_ref.is_configured)

    @is_configured.setter
    def is_configured(self, val: bool):
        self._configured = val

    @property
    def enabled(self) -> bool:
        if self._enabled or (bool(self.api_key) and self._configured):
            return True
        return bool(self.nvidia_ref and self.nvidia_ref.enabled and self.nvidia_ref.is_configured)

    @enabled.setter
    def enabled(self, val: bool):
        self._enabled = val

    def to_dict(self, is_active: bool = False) -> Dict[str, Any]:
        has_k = bool(self.api_key or (self.nvidia_ref and self.nvidia_ref.api_key))
        status = "Enabled" if self.enabled else ("Disabled" if self.is_configured else "Not configured")
        return {
            "id": self.provider_id,
            "name": self.display_name,
            "display_name": self.display_name,
            "requires_key": self.requires_key,
            "is_configured": self.is_configured,
            "enabled": self.enabled,
            "status": status,
            "has_key": has_k,
            "masked_key": self.get_masked_key() if self.api_key else (self.nvidia_ref.get_masked_key() if self.nvidia_ref else ""),
            "is_active": is_active
        }

    def verify_key(self, api_key: str) -> Tuple[bool, str, str]:
        if self.nvidia_ref:
            return self.nvidia_ref.verify_key(api_key)
        clean_key = (api_key or "").strip()
        if not clean_key:
            return False, "invalid_key", f"{self.display_name} API key is invalid. Please check your key and try again."
        return True, "valid", f"{self.display_name} API key verified successfully."

    def query(self, prompt: str, system_prompt: str, conversation_context: Optional[List[Dict[str, Any]]] = None, attachments: Optional[List[Dict[str, Any]]] = None, attachment_manager: Optional[Any] = None) -> Optional[str]:
        if self._test_query_hook:
            try:
                return self._test_query_hook(prompt, system_prompt)
            except TypeError:
                return self._test_query_hook(prompt)
        if self.nvidia_ref and (getattr(self.nvidia_ref, "_test_query_hook", None) or (self.nvidia_ref.enabled and self.nvidia_ref.api_key)):
            return self.nvidia_ref.query(prompt, system_prompt, specific_choice=self.provider_id, conversation_context=conversation_context, attachments=attachments, attachment_manager=attachment_manager)
        return None


def get_game_template(game_type: str, language: str = "html") -> Dict[str, str]:
    """Generates complete, fully playable source code for requested desktop game projects."""
    g = game_type.lower()
    if "snake" in g:
        if language == "python" or "py" in g:
            py_code = '''"""
Snake Game in Python (Desktop Edition)
Controls: Arrow Keys or WASD to navigate. Space to restart.
"""
import tkinter as tk
import random

GAME_WIDTH = 400
GAME_HEIGHT = 400
SPEED = 100
SPACE_SIZE = 20
BODY_PARTS = 3
SNAKE_COLOR = "#10b981"
FOOD_COLOR = "#ef4444"
BG_COLOR = "#020617"

class Snake:
    def __init__(self):
        self.body_size = BODY_PARTS
        self.coordinates = []
        self.squares = []
        for i in range(0, BODY_PARTS):
            self.coordinates.append([0, 0])

class Food:
    def __init__(self, canvas):
        x = random.randint(0, int(GAME_WIDTH / SPACE_SIZE) - 1) * SPACE_SIZE
        y = random.randint(0, int(GAME_HEIGHT / SPACE_SIZE) - 1) * SPACE_SIZE
        self.coordinates = [x, y]
        self.circle = canvas.create_oval(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=FOOD_COLOR, tag="food")

class SnakeGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Snake Arcade - Zevion")
        self.root.resizable(False, False)
        
        self.score = 0
        self.direction = "down"
        
        self.label = tk.Label(root, text=f"Score: {self.score}", font=('consolas', 20), bg="#1e293b", fg="#f8fafc")
        self.label.pack(fill="x")
        
        self.canvas = tk.Canvas(root, bg=BG_COLOR, height=GAME_HEIGHT, width=GAME_WIDTH)
        self.canvas.pack()
        
        self.root.bind('<Left>', lambda event: self.change_direction('left'))
        self.root.bind('<Right>', lambda event: self.change_direction('right'))
        self.root.bind('<Up>', lambda event: self.change_direction('up'))
        self.root.bind('<Down>', lambda event: self.change_direction('down'))
        self.root.bind('<a>', lambda event: self.change_direction('left'))
        self.root.bind('<d>', lambda event: self.change_direction('right'))
        self.root.bind('<w>', lambda event: self.change_direction('up'))
        self.root.bind('<s>', lambda event: self.change_direction('down'))
        self.root.bind('<space>', lambda event: self.restart_game())
        
        self.snake = Snake()
        self.food = Food(self.canvas)
        self.is_game_over = False
        self.next_turn()

    def change_direction(self, new_dir):
        if new_dir == 'left' and self.direction != 'right': self.direction = new_dir
        elif new_dir == 'right' and self.direction != 'left': self.direction = new_dir
        elif new_dir == 'up' and self.direction != 'down': self.direction = new_dir
        elif new_dir == 'down' and self.direction != 'up': self.direction = new_dir

    def next_turn(self):
        if self.is_game_over:
            return
        x, y = self.snake.coordinates[0]
        if self.direction == "up": y -= SPACE_SIZE
        elif self.direction == "down": y += SPACE_SIZE
        elif self.direction == "left": x -= SPACE_SIZE
        elif self.direction == "right": x += SPACE_SIZE
        
        self.snake.coordinates.insert(0, [x, y])
        square = self.canvas.create_rectangle(x, y, x + SPACE_SIZE, y + SPACE_SIZE, fill=SNAKE_COLOR)
        self.snake.squares.insert(0, square)
        
        if x == self.food.coordinates[0] and y == self.food.coordinates[1]:
            self.score += 10
            self.label.config(text=f"Score: {self.score}")
            self.canvas.delete("food")
            self.food = Food(self.canvas)
        else:
            del self.snake.coordinates[-1]
            self.canvas.delete(self.snake.squares[-1])
            del self.snake.squares[-1]
            
        if self.check_collisions():
            self.game_over()
        else:
            self.root.after(SPEED, self.next_turn)

    def check_collisions(self):
        x, y = self.snake.coordinates[0]
        if x < 0 or x >= GAME_WIDTH or y < 0 or y >= GAME_HEIGHT:
            return True
        for body_part in self.snake.coordinates[1:]:
            if x == body_part[0] and y == body_part[1]:
                return True
        return False

    def game_over(self):
        self.is_game_over = True
        self.canvas.delete("all")
        self.canvas.create_text(GAME_WIDTH/2, GAME_HEIGHT/2 - 20, font=('consolas', 30), text="GAME OVER", fill="#ef4444")
        self.canvas.create_text(GAME_WIDTH/2, GAME_HEIGHT/2 + 20, font=('consolas', 16), text=f"Final Score: {self.score}", fill="#f8fafc")
        self.canvas.create_text(GAME_WIDTH/2, GAME_HEIGHT/2 + 50, font=('consolas', 12), text="Press Space to Restart", fill="#94a3b8")

    def restart_game(self):
        self.is_game_over = False
        self.score = 0
        self.direction = "down"
        self.label.config(text=f"Score: {self.score}")
        self.canvas.delete("all")
        self.snake = Snake()
        self.food = Food(self.canvas)
        self.next_turn()

if __name__ == "__main__":
    window = tk.Tk()
    app = SnakeGame(window)
    window.mainloop()
'''
            return {"snake.py": py_code, "README.md": "# Snake Game in Python\nRun with: `python snake.py`\nControls: Arrow Keys or WASD. Space to restart.\n"}
        
        # HTML5 Canvas Snake Game (100% complete, fully visible snake, sandbox-safe)
        html_code = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Snake Game - Zevion</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="game-wrapper">
    <div class="game-card">
      <header class="game-header">
        <div class="game-title">
          <span class="game-icon">🐍</span>
          <h1>Snake Arcade</h1>
        </div>
        <div class="score-container">
          <div class="score-box">
            <span class="score-label">SCORE</span>
            <span id="score" class="score-val">0</span>
          </div>
          <div class="score-box highscore-box">
            <span class="score-label">HIGH SCORE</span>
            <span id="highScore" class="score-val">0</span>
          </div>
        </div>
      </header>

      <div class="canvas-container">
        <canvas id="gameCanvas" width="400" height="400"></canvas>
        <div id="gameOverOverlay" class="game-overlay hidden">
          <div class="overlay-content">
            <h2 class="game-over-title">GAME OVER</h2>
            <p class="final-score-text">Final Score: <span id="finalScore">0</span></p>
            <button id="restartBtnOverlay" class="btn btn-primary">Play Again</button>
          </div>
        </div>
      </div>

      <footer class="game-controls">
        <div class="button-group">
          <button id="startBtn" class="btn btn-primary">Restart</button>
          <button id="pauseBtn" class="btn btn-secondary">Pause</button>
        </div>
        <div class="instructions-card">
          <p>Controls: <kbd>↑</kbd> <kbd>↓</kbd> <kbd>←</kbd> <kbd>→</kbd> or <kbd>W</kbd> <kbd>A</kbd> <kbd>S</kbd> <kbd>D</kbd></p>
        </div>
      </footer>
    </div>
  </div>
  <script src="game.js"></script>
</body>
</html>'''

        css_code = '''* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

body {
  background: #090d16;
  color: #f8fafc;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  padding: 16px;
}

.game-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
}

.game-card {
  background: #131b2e;
  border: 1px solid #1e293b;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.6);
  max-width: 440px;
  width: 100%;
  text-align: center;
}

.game-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.game-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.game-icon {
  font-size: 24px;
}

.game-title h1 {
  font-size: 20px;
  font-weight: 700;
  color: #38bdf8;
  letter-spacing: -0.5px;
}

.score-container {
  display: flex;
  gap: 10px;
}

.score-box {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 8px;
  padding: 4px 10px;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 65px;
}

.score-label {
  font-size: 9px;
  font-weight: 700;
  color: #94a3b8;
  letter-spacing: 0.5px;
}

.score-val {
  font-size: 16px;
  font-weight: 800;
  color: #38bdf8;
  font-family: monospace;
}

.highscore-box .score-val {
  color: #f59e0b;
}

.canvas-container {
  position: relative;
  width: 400px;
  height: 400px;
  margin: 0 auto 16px auto;
  border-radius: 10px;
  overflow: hidden;
  border: 2px solid #334155;
  background: #020617;
  box-shadow: inset 0 0 20px rgba(0, 0, 0, 0.8);
}

#gameCanvas {
  display: block;
  width: 400px;
  height: 400px;
  background: #020617;
}

.game-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(2, 6, 23, 0.88);
  backdrop-filter: blur(4px);
  display: flex;
  justify-content: center;
  align-items: center;
  transition: opacity 0.2s;
}

.game-overlay.hidden {
  display: none;
}

.overlay-content {
  text-align: center;
  padding: 20px;
}

.game-over-title {
  font-size: 28px;
  font-weight: 900;
  color: #ef4444;
  margin-bottom: 8px;
  letter-spacing: 1px;
}

.final-score-text {
  font-size: 16px;
  color: #cbd5e1;
  margin-bottom: 16px;
}

.final-score-text span {
  font-weight: 800;
  color: #38bdf8;
}

.game-controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.button-group {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.btn {
  border: none;
  border-radius: 8px;
  padding: 10px 22px;
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s ease-in-out;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.btn-primary {
  background: #10b981;
  color: #ffffff;
}

.btn-primary:hover {
  background: #059669;
  transform: translateY(-1px);
}

.btn-secondary {
  background: #334155;
  color: #f8fafc;
}

.btn-secondary:hover {
  background: #475569;
}

.instructions-card {
  font-size: 12px;
  color: #94a3b8;
}

kbd {
  background: #1e293b;
  border: 1px solid #475569;
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 11px;
  font-family: monospace;
  color: #e2e8f0;
}'''

        js_code = '''// Self-executing setup compatible with standalone HTML and sandboxed iframes
(function () {
  let canvas, ctx;
  let scoreEl, highScoreEl, finalScoreEl, gameOverOverlay;
  let startBtn, pauseBtn, restartBtnOverlay;

  const gridSize = 20;
  const tileCount = 20;

  let snake = [
    { x: 10, y: 10 },
    { x: 9, y: 10 },
    { x: 8, y: 10 }
  ];

  let food = { x: 15, y: 10 };
  let dx = 1;
  let dy = 0;
  let nextDx = 1;
  let nextDy = 0;
  let score = 0;
  let highScore = 0;
  let gameInterval = null;
  let isPaused = false;
  let isGameOver = false;
  const gameSpeed = 110;

  function getStoredHighScore() {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        const val = localStorage.getItem('snake_arcade_highscore');
        return val ? parseInt(val, 10) || 0 : 0;
      }
    } catch (e) {}
    return 0;
  }

  function saveHighScore(val) {
    try {
      if (typeof window !== 'undefined' && window.localStorage) {
        localStorage.setItem('snake_arcade_highscore', val.toString());
      }
    } catch (e) {}
  }

  function spawnFood() {
    let valid = false;
    let attempts = 0;
    while (!valid && attempts < 200) {
      food.x = Math.floor(Math.random() * tileCount);
      food.y = Math.floor(Math.random() * tileCount);
      valid = true;
      for (let i = 0; i < snake.length; i++) {
        if (snake[i].x === food.x && snake[i].y === food.y) {
          valid = false;
          break;
        }
      }
      attempts++;
    }
  }

  function renderGrid() {
    ctx.strokeStyle = '#0f172a';
    ctx.lineWidth = 1;
    for (let x = 0; x <= 400; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, 400);
      ctx.stroke();
    }
    for (let y = 0; y <= 400; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(400, y);
      ctx.stroke();
    }
  }

  function drawGame() {
    if (!ctx) return;
    if (isPaused || isGameOver) return;

    dx = nextDx;
    dy = nextDy;

    const head = { x: snake[0].x + dx, y: snake[0].y + dy };

    if (head.x < 0 || head.x >= tileCount || head.y < 0 || head.y >= tileCount) {
      triggerGameOver();
      return;
    }

    for (let i = 0; i < snake.length; i++) {
      if (head.x === snake[i].x && head.y === snake[i].y) {
        triggerGameOver();
        return;
      }
    }

    snake.unshift(head);

    if (head.x === food.x && head.y === food.y) {
      score += 10;
      if (scoreEl) scoreEl.textContent = score;
      if (score > highScore) {
        highScore = score;
        if (highScoreEl) highScoreEl.textContent = highScore;
        saveHighScore(highScore);
      }
      spawnFood();
    } else {
      snake.pop();
    }

    render();
  }

  function render() {
    if (!ctx) return;

    ctx.fillStyle = '#020617';
    ctx.fillRect(0, 0, 400, 400);

    renderGrid();

    // Draw Food
    const fx = food.x * gridSize;
    const fy = food.y * gridSize;
    ctx.fillStyle = '#ef4444';
    ctx.beginPath();
    ctx.arc(fx + gridSize / 2, fy + gridSize / 2, gridSize / 2 - 2, 0, Math.PI * 2);
    ctx.fill();

    ctx.fillStyle = '#fca5a5';
    ctx.beginPath();
    ctx.arc(fx + gridSize / 2 - 3, fy + gridSize / 2 - 3, 2, 0, Math.PI * 2);
    ctx.fill();

    // Draw Snake
    snake.forEach((segment, index) => {
      const sx = segment.x * gridSize;
      const sy = segment.y * gridSize;

      if (index === 0) {
        ctx.fillStyle = '#10b981';
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(sx + 1, sy + 1, gridSize - 2, gridSize - 2, 5);
        } else {
          ctx.rect(sx + 1, sy + 1, gridSize - 2, gridSize - 2);
        }
        ctx.fill();

        ctx.fillStyle = '#ffffff';
        let eye1X = sx + 13, eye1Y = sy + 5;
        let eye2X = sx + 13, eye2Y = sy + 13;
        if (dx === -1) {
          eye1X = sx + 5; eye1Y = sy + 5;
          eye2X = sx + 5; eye2Y = sy + 13;
        } else if (dy === -1) {
          eye1X = sx + 5; eye1Y = sy + 5;
          eye2X = sx + 13; eye2Y = sy + 5;
        } else if (dy === 1) {
          eye1X = sx + 5; eye1Y = sy + 13;
          eye2X = sx + 13; eye2Y = sy + 13;
        }
        ctx.beginPath(); ctx.arc(eye1X, eye1Y, 2.5, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(eye2X, eye2Y, 2.5, 0, Math.PI * 2); ctx.fill();
        ctx.fillStyle = '#0f172a';
        ctx.beginPath(); ctx.arc(eye1X, eye1Y, 1.2, 0, Math.PI * 2); ctx.fill();
        ctx.beginPath(); ctx.arc(eye2X, eye2Y, 1.2, 0, Math.PI * 2); ctx.fill();
      } else {
        ctx.fillStyle = index % 2 === 0 ? '#34d399' : '#059669';
        ctx.beginPath();
        if (ctx.roundRect) {
          ctx.roundRect(sx + 1.5, sy + 1.5, gridSize - 3, gridSize - 3, 3);
        } else {
          ctx.rect(sx + 1.5, sy + 1.5, gridSize - 3, gridSize - 3);
        }
        ctx.fill();
      }
    });
  }

  function triggerGameOver() {
    isGameOver = true;
    if (gameInterval) clearInterval(gameInterval);
    if (finalScoreEl) finalScoreEl.textContent = score;
    if (gameOverOverlay) gameOverOverlay.classList.remove('hidden');
  }

  function resetGame() {
    if (gameInterval) clearInterval(gameInterval);

    snake = [
      { x: 10, y: 10 },
      { x: 9, y: 10 },
      { x: 8, y: 10 }
    ];
    dx = 1;
    dy = 0;
    nextDx = 1;
    nextDy = 0;
    score = 0;
    isPaused = false;
    isGameOver = false;

    if (scoreEl) scoreEl.textContent = '0';
    if (pauseBtn) pauseBtn.textContent = 'Pause';
    if (gameOverOverlay) gameOverOverlay.classList.add('hidden');

    spawnFood();
    render();
    gameInterval = setInterval(drawGame, gameSpeed);
  }

  function togglePause() {
    if (isGameOver) return;
    isPaused = !isPaused;
    if (pauseBtn) pauseBtn.textContent = isPaused ? 'Resume' : 'Pause';
  }

  function handleKey(e) {
    const key = e.key;
    if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', ' '].includes(key)) {
      e.preventDefault();
    }

    if (key === 'ArrowUp' || key === 'w' || key === 'W') {
      if (dy === 0) { nextDx = 0; nextDy = -1; }
    } else if (key === 'ArrowDown' || key === 's' || key === 'S') {
      if (dy === 0) { nextDx = 0; nextDy = 1; }
    } else if (key === 'ArrowLeft' || key === 'a' || key === 'A') {
      if (dx === 0) { nextDx = -1; nextDy = 0; }
    } else if (key === 'ArrowRight' || key === 'd' || key === 'D') {
      if (dx === 0) { nextDx = 1; nextDy = 0; }
    } else if (key === ' ' || key === 'Spacebar') {
      if (isGameOver) resetGame();
      else togglePause();
    }
  }

  function init() {
    canvas = document.getElementById('gameCanvas');
    if (!canvas) return;
    ctx = canvas.getContext('2d');

    scoreEl = document.getElementById('score');
    highScoreEl = document.getElementById('highScore');
    finalScoreEl = document.getElementById('finalScore');
    gameOverOverlay = document.getElementById('gameOverOverlay');
    startBtn = document.getElementById('startBtn');
    pauseBtn = document.getElementById('pauseBtn');
    restartBtnOverlay = document.getElementById('restartBtnOverlay');

    highScore = getStoredHighScore();
    if (highScoreEl) highScoreEl.textContent = highScore;

    if (startBtn) startBtn.onclick = resetGame;
    if (pauseBtn) pauseBtn.onclick = togglePause;
    if (restartBtnOverlay) restartBtnOverlay.onclick = resetGame;

    window.removeEventListener('keydown', handleKey);
    window.addEventListener('keydown', handleKey);

    resetGame();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();'''

        return {
            "index.html": html_code,
            "style.css": css_code,
            "game.js": js_code,
            "README.md": "# Snake Arcade Game\nOpen `index.html` in any web browser to play.\nControls: Arrow keys or WASD.\n"
        }

    elif "tic" in g or "toe" in g or "tictactoe" in g:
        html_code = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Tic-Tac-Toe - Zevion</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="container">
    <h1>Tic-Tac-Toe</h1>
    <div class="status" id="status">Turn: Player X</div>
    <div class="board" id="board">
      <div class="cell" data-index="0"></div>
      <div class="cell" data-index="1"></div>
      <div class="cell" data-index="2"></div>
      <div class="cell" data-index="3"></div>
      <div class="cell" data-index="4"></div>
      <div class="cell" data-index="5"></div>
      <div class="cell" data-index="6"></div>
      <div class="cell" data-index="7"></div>
      <div class="cell" data-index="8"></div>
    </div>
    <button id="restartBtn">Restart Game</button>
  </div>
  <script src="game.js"></script>
</body>
</html>'''

        css_code = '''body {
  background: #090d16;
  color: #fff;
  font-family: sans-serif;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  margin: 0;
}
.container { text-align: center; background: #131b2e; padding: 24px; border-radius: 12px; }
h1 { color: #38bdf8; margin-bottom: 8px; }
.status { font-size: 18px; margin-bottom: 16px; color: #cbd5e1; }
.board {
  display: grid;
  grid-template-columns: repeat(3, 100px);
  grid-gap: 8px;
  margin: 0 auto 16px;
}
.cell {
  width: 100px;
  height: 100px;
  background: #1e293b;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 36px;
  font-weight: bold;
  cursor: pointer;
  border-radius: 8px;
  color: #38bdf8;
  transition: 0.15s;
}
.cell:hover { background: #334155; }
button {
  background: #38bdf8;
  color: #090d16;
  border: none;
  padding: 10px 24px;
  border-radius: 6px;
  font-weight: bold;
  cursor: pointer;
}
button:hover { background: #0284c7; color: white; }'''

        js_code = '''const cells = document.querySelectorAll('.cell');
const statusEl = document.getElementById('status');
const restartBtn = document.getElementById('restartBtn');

let currentPlayer = 'X';
let board = ['', '', '', '', '', '', '', '', ''];
let active = true;

const winningConditions = [
  [0, 1, 2], [3, 4, 5], [6, 7, 8],
  [0, 3, 6], [1, 4, 7], [2, 5, 8],
  [0, 4, 8], [2, 4, 6]
];

function handleCellClick(e) {
  const index = e.target.getAttribute('data-index');
  if (board[index] !== '' || !active) return;

  board[index] = currentPlayer;
  e.target.textContent = currentPlayer;

  checkResult();
}

function checkResult() {
  let roundWon = false;
  for (let condition of winningConditions) {
    let [a, b, c] = condition;
    if (board[a] && board[a] === board[b] && board[a] === board[c]) {
      roundWon = true;
      break;
    }
  }

  if (roundWon) {
    statusEl.textContent = `Player ${currentPlayer} Wins! 🎉`;
    active = false;
    return;
  }

  if (!board.includes('')) {
    statusEl.textContent = "It's a Draw! 🤝";
    active = false;
    return;
  }

  currentPlayer = currentPlayer === 'X' ? 'O' : 'X';
  statusEl.textContent = `Turn: Player ${currentPlayer}`;
}

function restartGame() {
  currentPlayer = 'X';
  board = ['', '', '', '', '', '', '', '', ''];
  active = true;
  statusEl.textContent = 'Turn: Player X';
  cells.forEach(c => (c.textContent = ''));
}

cells.forEach(c => c.addEventListener('click', handleCellClick));
restartBtn.addEventListener('click', restartGame);'''

        return {
            "index.html": html_code,
            "style.css": css_code,
            "game.js": js_code,
            "README.md": "# Tic-Tac-Toe Game\nOpen `index.html` in browser.\n"
        }

    elif "flappy" in g or "bird" in g:
        html_code = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Flappy Bird - Zevion</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0b0d11;color:#e5e7eb;font-family:'Segoe UI',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh}
.wrap{text-align:center}
h1{background:linear-gradient(135deg,#f59e0b,#f43f5e);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:10px}
.score{font-size:20px;margin-bottom:8px;font-weight:600}
canvas{background:linear-gradient(#1e293b,#0f172a);border:2px solid #334155;border-radius:12px;display:block;margin:0 auto}
.hint{margin-top:10px;color:#94a3b8;font-size:13px}
button{margin-top:12px;background:linear-gradient(135deg,#f59e0b,#f43f5e);color:#0b0d11;border:none;padding:10px 24px;border-radius:8px;font-weight:700;cursor:pointer;font-size:14px}
</style>
</head>
<body>
<div class="wrap">
<h1>Flappy Bird</h1>
<div class="score">Score: <span id="score">0</span> &nbsp; Best: <span id="best">0</span></div>
<canvas id="c" width="400" height="520"></canvas>
<div class="hint">Click / Tap / Space to flap</div>
<button id="restart">Restart</button>
</div>
<script>
const cv=document.getElementById('c'),ctx=cv.getContext('2d');
const sEl=document.getElementById('score'),bEl=document.getElementById('best');
let best=0;try{best=parseInt(localStorage.getItem('flappy_best')||'0')||0}catch(e){}
bEl.textContent=best;
let bird, pipes, score, over, frames;
function audio(){try{const a=new (window.AudioContext||window.webkitAudioContext)();return{flap(){const o=a.createOscillator(),g=a.createGain();o.frequency.value=400;o.frequency.exponentialRampToValueAtTime(800,a.currentTime+0.08);g.gain.setValueAtTime(0.08,a.currentTime);g.gain.exponentialRampToValueAtTime(0.001,a.currentTime+0.12);o.connect(g);g.connect(a.destination);o.start();o.stop(a.currentTime+0.12)},die(){const o=a.createOscillator(),g=a.createGain();o.frequency.value=200;o.frequency.exponentialRampToValueAtTime(40,a.currentTime+0.3);g.gain.setValueAtTime(0.1,a.currentTime);g.gain.exponentialRampToValueAtTime(0.001,a.currentTime+0.3);o.connect(g);g.connect(a.destination);o.start();o.stop(a.currentTime+0.3)}}}catch(e){return{flap(){},die(){}}}}
const snd=audio();
function reset(){bird={y:260,v:0};pipes=[];score=0;over=false;frames=0;sEl.textContent='0'}
function flap(){if(over){reset();return}bird.v=-6;snd.flap()}
function update(){if(over)return;frames++;bird.v+=0.4;bird.y+=bird.v;
if(frames%80===0){let h=60+Math.random()*240;pipes.push({x:400,gap:140,top:h})}
for(let i=pipes.length-1;i>=0;i--){pipes[i].x-=2.5;
if(pipes[i].x<-60){pipes.splice(i,1);score++;sEl.textContent=score}}
for(let p of pipes){if(bird.x+15>p.x&&bird.x-15<p.x+50){if(bird.y-15<p.top||bird.y+15>p.top+p.gap){end()}}}
if(bird.y>520||bird.y<0)end()}
function end(){if(over)return;over=true;snd.die();if(score>best){best=score;bEl.textContent=best;try{localStorage.setItem('flappy_best',best)}catch(e){}}}
function draw(){ctx.clearRect(0,0,400,520);
ctx.fillStyle='#f59e0b';ctx.beginPath();ctx.arc(bird.x||60,bird.y,15,0,Math.PI*2);ctx.fill();
ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(58,bird.y-4,4,0,Math.PI*2);ctx.fill();
ctx.fillStyle='#fbbf24';ctx.beginPath();ctx.arc(60,bird.y-2,3,0,Math.PI*2);ctx.fill();
ctx.fillStyle='#34d399';for(let p of pipes){ctx.fillRect(p.x,0,50,p.top);ctx.fillRect(p.x,p.top+p.gap,50,520)}
if(over){ctx.fillStyle='rgba(0,0,0,0.6)';ctx.fillRect(0,200,400,80);ctx.fillStyle='#fca5a5';ctx.font='bold 28px sans-serif';ctx.textAlign='center';ctx.fillText('Game Over',200,245)}}
function loop(){update();draw();requestAnimationFrame(loop)}
bird={y:260,v:0};pipes=[];score=0;over=false;frames=0;
document.addEventListener('keydown',e=>{if(e.code==='Space'){e.preventDefault();flap()}});
cv.addEventListener('pointerdown',flap);
document.getElementById('restart').addEventListener('click',()=>{reset();flap()});
loop();
</script>
</body>
</html>'''
        return {"index.html": html_code, "README.md": "# Flappy Bird Game\nOpen `index.html` in browser. Click/Tap/Space to flap.\n"}

    elif "2048" in g or "twenty" in g:
        html_code = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>2048 - Zevion</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0b0d11;color:#e5e7eb;font-family:'Segoe UI',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh}
.wrap{text-align:center}
h1{background:linear-gradient(135deg,#f59e0b,#f43f5e);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:8px}
.scores{display:flex;justify-content:center;gap:20px;margin-bottom:12px}
.scores div{background:#1f2937;border-radius:8px;padding:6px 16px;font-size:14px;font-weight:600}
.board{display:grid;grid-template-columns:repeat(4,90px);gap:10px;background:#1f2937;padding:12px;border-radius:12px;width:max-content;margin:0 auto}
.cell{width:90px;height:90px;background:#111827;border-radius:8px;display:flex;justify-content:center;align-items:center;font-size:32px;font-weight:800;transition:0.12s}
.c2{background:#334155}.c4{background:#475569}.c8{background:#f59e0b}.c16{background:#fb923c}.c32{background:#f87171}.c64{background:#ef4444}.c128{background:#fbbf24}.c256{background:#facc15}.c512{background:#4ade80}.c1024{background:#22c55e}.c2048{background:#a855f7}
.over{position:relative}
button{margin-top:14px;background:linear-gradient(135deg,#f59e0b,#f43f5e);color:#0b0d11;border:none;padding:10px 24px;border-radius:8px;font-weight:700;cursor:pointer}
</style>
</head>
<body>
<div class="wrap">
<h1>2048</h1>
<div class="scores"><div>Score: <span id="score">0</span></div><div>Best: <span id="best">0</span></div></div>
<div class="board" id="board"></div>
<button id="restart">New Game</button>
</div>
<script>
const boardEl=document.getElementById('board'),sEl=document.getElementById('score'),bEl=document.getElementById('best');
let grid,best=0;try{best=parseInt(localStorage.getItem('2048_best')||'0')||0}catch(e){}bEl.textContent=best;
function spawn(){let empty=[];grid.forEach((r,i)=>r.forEach((v,j)=>{if(!v)empty.push([i,j])}));if(empty.length){let[i,j]=empty[Math.floor(Math.random()*empty.length)];grid[i][j]=Math.random()<0.9?2:4}}
function draw(){boardEl.innerHTML='';let score=0;grid.forEach(r=>r.forEach(v=>{score+=v;let d=document.createElement('div');d.className='cell '+(v?('c'+v):'');d.textContent=v||'';boardEl.appendChild(d)}));sEl.textContent=score;if(score>best){best=score;bEl.textContent=best;try{localStorage.setItem('2048_best',best)}catch(e){}}}
function slide(row){let a=row.filter(v=>v);let out=[],i=0;while(i<a.length){if(a[i]===a[i+1]){out.push(a[i]*2);i+=2}else{out.push(a[i]);i++}}while(out.length<4)out.push(0);return out}
function move(dir){let before=JSON.stringify(grid);let newGrid=[];if(dir==='left')grid=grid.map(slide);else if(dir==='right')grid=grid.map(r=>slide([...r].reverse()).reverse());else if(dir==='up'){for(let c=0;c<4;c++){let col=slide([grid[0][c],grid[1][c],grid[2][c],grid[3][c]]);for(let r=0;r<4;r++)grid[r][c]=col[r]}}else{for(let c=0;c<4;c++){let col=slide([grid[3][c],grid[2][c],grid[1][c],grid[0][c]]).reverse();for(let r=0;r<4;r++)grid[r][c]=col[r]}}if(JSON.stringify(grid)!==before)spawn();draw()}
function reset(){grid=[[0,0,0,0],[0,0,0,0],[0,0,0,0],[0,0,0,0]];spawn();spawn();draw()}
document.addEventListener('keydown',e=>{let m={ArrowLeft:'left',ArrowRight:'right',ArrowUp:'up',ArrowDown:'down'}[e.key];if(m){e.preventDefault();move(m)}});
let touchX=0,touchY=0;document.addEventListener('touchstart',e=>{touchX=e.touches[0].clientX;touchY=e.touches[0].clientY});document.addEventListener('touchend',e=>{let dx=e.changedTouches[0].clientX-touchX,dy=e.changedTouches[0].clientY-touchY;if(Math.abs(dx)>Math.abs(dy))move(dx>0?'right':'left');else move(dy>0?'down':'up')});
document.getElementById('restart').addEventListener('click',reset);
reset();
</script>
</body>
</html>'''
        return {"index.html": html_code, "README.md": "# 2048 Game\nOpen `index.html` in browser. Arrow keys or swipe to move.\n"}

    elif "breakout" in g or "brick" in g or "blocks" in g:
        html_code = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Breakout - Zevion</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0b0d11;color:#e5e7eb;font-family:'Segoe UI',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh}
.wrap{text-align:center}
h1{background:linear-gradient(135deg,#f59e0b,#f43f5e);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:10px}
.score{font-size:18px;margin-bottom:8px;font-weight:600}
canvas{background:#0f172a;border:2px solid #334155;border-radius:12px;display:block;margin:0 auto}
button{margin-top:12px;background:linear-gradient(135deg,#f59e0b,#f43f5e);color:#0b0d11;border:none;padding:10px 24px;border-radius:8px;font-weight:700;cursor:pointer}
</style>
</head>
<body>
<div class="wrap">
<h1>Breakout</h1>
<div class="score">Score: <span id="score">0</span> &nbsp; Lives: <span id="lives">3</span></div>
<canvas id="c" width="480" height="500"></canvas>
<button id="restart">Restart</button>
</div>
<script>
const cv=document.getElementById('c'),ctx=cv.getContext('2d');
const sEl=document.getElementById('score'),lEl=document.getElementById('lives');
let paddle,bricks,ball,dx,dy,score,lives;
function beep(){try{const a=new(window.AudioContext||window.webkitAudioContext)(),o=a.createOscillator(),g=a.createGain();o.frequency.value=600;g.gain.setValueAtTime(0.05,a.currentTime);g.gain.exponentialRampToValueAtTime(0.001,a.currentTime+0.08);o.connect(g);g.connect(a.destination);o.start();o.stop(a.currentTime+0.08)}catch(e){}}
function reset(){paddle={x:190,w:100};ball={x:240,y:400};dx=3;dy=-3;score=0;lives=3;sEl.textContent='0';lEl.textContent='3';bricks=[];let colors=['#f43f5e','#fb923c','#f59e0b','#facc15','#4ade80'];for(let r=0;r<5;r++)for(let c=0;c<8;c++)bricks.push({x:c*60+4,y:r*28+40,w:52,h:22,alive:true,c:colors[r]})}
function update(){ball.x+=dx;ball.y+=dy;
if(ball.x<8||ball.x>472)dx=-dx;if(ball.y<8)dy=-dy;
if(ball.y>480&&ball.x>paddle.x&&ball.x<paddle.x+paddle.w&&ball.y<500){dy=-Math.abs(dy);beep()}
if(ball.y>510){lives--;lEl.textContent=lives;if(lives<=0){ball={x:240,y:400};dx=3;dy=-3;return}ball={x:240,y:400};dx=3;dy=-3}
for(let b of bricks){if(b.alive&&ball.x>b.x&&ball.x<b.x+b.w&&ball.y>b.y&&ball.y<b.y+b.h){b.alive=false;dy=-dy;score+=10;sEl.textContent=score;beep();break}}}
function draw(){ctx.clearRect(0,0,480,500);
ctx.fillStyle='#f59e0b';ctx.beginPath();ctx.roundRect(paddle.x,490,paddle.w,12,6);ctx.fill();
ctx.fillStyle='#fff';ctx.beginPath();ctx.arc(ball.x,ball.y,7,0,Math.PI*2);ctx.fill();
for(let b of bricks){if(b.alive){ctx.fillStyle=b.c;ctx.beginPath();ctx.roundRect(b.x,b.y,b.w,b.h,4);ctx.fill()}}
if(bricks.every(b=>!b.alive)){ctx.fillStyle='#4ade80';ctx.font='bold 30px sans-serif';ctx.textAlign='center';ctx.fillText('You Win!',240,250)}}
function loop(){update();draw();requestAnimationFrame(loop)}
cv.addEventListener('pointermove',e=>{let r=cv.getBoundingClientRect();paddle.x=e.clientX-r.left-paddle.w/2;paddle.x=Math.max(0,Math.min(480-paddle.w,paddle.x))});
document.getElementById('restart').addEventListener('click',reset);
reset();loop();
</script>
</body>
</html>'''
        return {"index.html": html_code, "README.md": "# Breakout Game\nOpen `index.html` in browser. Move mouse to control paddle.\n"}

    elif "memory" in g or "match" in g or "cards" in g:
        html_code = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Memory Match - Zevion</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0b0d11;color:#e5e7eb;font-family:'Segoe UI',sans-serif;display:flex;justify-content:center;align-items:center;min-height:100vh}
.wrap{text-align:center}
h1{background:linear-gradient(135deg,#f59e0b,#f43f5e);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;margin-bottom:10px}
.info{margin-bottom:12px;font-size:15px}
.board{display:grid;grid-template-columns:repeat(4,80px);gap:10px;width:max-content;margin:0 auto}
.card{width:80px;height:80px;background:#1f2937;border-radius:10px;cursor:pointer;display:flex;justify-content:center;align-items:center;font-size:34px;transition:0.2s;user-select:none}
.card.flipped{background:#f59e0b;transform:scale(1.04)}
.card.matched{background:#4ade80;cursor:default}
button{margin-top:14px;background:linear-gradient(135deg,#f59e0b,#f43f5e);color:#0b0d11;border:none;padding:10px 24px;border-radius:8px;font-weight:700;cursor:pointer}
</style>
</head>
<body>
<div class="wrap">
<h1>Memory Match</h1>
<div class="info">Moves: <span id="moves">0</span> &nbsp; Pairs: <span id="pairs">0</span>/8</div>
<div class="board" id="board"></div>
<button id="restart">New Game</button>
</div>
<script>
const boardEl=document.getElementById('board'),mEl=document.getElementById('moves'),pEl=document.getElementById('pairs');
const emojis=['🍎','🍌','🍇','🍉','🍓','🍒','🥝','🍍'];
let cards,first,second,lock,moves,pairs;
function reset(){let deck=[...emojis,...emojis];deck.sort(()=>Math.random()-0.5);cards=deck.map((e,i)=>({e,i,flipped:false,matched:false}));first=second=null;lock=false;moves=0;pairs=0;mEl.textContent='0';pEl.textContent='0/8';draw()}
function draw(){boardEl.innerHTML='';cards.forEach((c,i)=>{let d=document.createElement('div');d.className='card'+(c.flipped?' flipped':'')+(c.matched?' matched':'');d.textContent=(c.flipped||c.matched)?c.e:'';d.onclick=()=>flip(i);boardEl.appendChild(d)})}
function flip(i){if(lock||cards[i].flipped||cards[i].matched)return;cards[i].flipped=true;if(!first){first=cards[i]}else{second=cards[i];moves++;mEl.textContent=moves;lock=true;if(first.e===second.e){first.matched=second.matched=true;pairs++;pEl.textContent=pairs+'/8';first=second=null;lock=false;draw()}else{setTimeout(()=>{first.flipped=second.flipped=false;first=second=null;lock=false;draw()},700)}}
draw()}
document.getElementById('restart').addEventListener('click',reset);
reset();
</script>
</body>
</html>'''
        return {"index.html": html_code, "README.md": "# Memory Match Game\nOpen `index.html` in browser. Click cards to find matching pairs.\n"}

    else:
        # Arcade / Pong Game (HTML5 Canvas modular)
        html_code = '''<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Arcade Game - Zevion</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <div class="game-wrapper">
    <div class="game-card">
      <header class="game-header">
        <h1>🕹️ Desktop Arcade</h1>
        <div class="score-box">Score: <span id="score">0</span></div>
      </header>
      <canvas id="gameCanvas" width="400" height="400"></canvas>
      <p class="controls-hint">Move mouse or use <kbd>←</kbd> <kbd>→</kbd> to move paddle</p>
    </div>
  </div>
  <script src="game.js"></script>
</body>
</html>'''

        css_code = '''* { box-sizing: border-box; margin: 0; padding: 0; }
body { background: #090d16; color: #fff; display: flex; justify-content: center; align-items: center; min-height: 100vh; font-family: sans-serif; }
.game-card { background: #131b2e; border: 1px solid #1e293b; border-radius: 16px; padding: 20px; text-align: center; }
.game-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
h1 { font-size: 20px; color: #38bdf8; }
.score-box { font-weight: bold; color: #10b981; }
#gameCanvas { background: #020617; border: 2px solid #334155; border-radius: 8px; display: block; margin: 0 auto 12px auto; }
.controls-hint { font-size: 12px; color: #94a3b8; }
kbd { background: #1e293b; padding: 2px 6px; border-radius: 4px; border: 1px solid #475569; }'''

        js_code = '''(function() {
  const canvas = document.getElementById('gameCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const scoreEl = document.getElementById('score');

  let x = 200, y = 200, dx = 3, dy = -3;
  let paddleWidth = 80, paddleHeight = 10, paddleX = 160;
  let score = 0;

  function handleMouseMove(e) {
    const rect = canvas.getBoundingClientRect();
    const relX = e.clientX - rect.left;
    if (relX > 0 && relX < canvas.width) {
      paddleX = Math.max(0, Math.min(canvas.width - paddleWidth, relX - paddleWidth / 2));
    }
  }

  function handleKeyDown(e) {
    if (e.key === 'ArrowLeft' || e.key === 'a') paddleX = Math.max(0, paddleX - 25);
    if (e.key === 'ArrowRight' || e.key === 'd') paddleX = Math.min(canvas.width - paddleWidth, paddleX + 25);
  }

  window.addEventListener('mousemove', handleMouseMove);
  window.addEventListener('keydown', handleKeyDown);

  function draw() {
    ctx.fillStyle = '#020617';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Draw ball
    ctx.beginPath();
    ctx.arc(x, y, 8, 0, Math.PI * 2);
    ctx.fillStyle = '#38bdf8';
    ctx.fill();
    ctx.closePath();

    // Draw paddle
    ctx.fillStyle = '#10b981';
    ctx.fillRect(paddleX, canvas.height - paddleHeight - 10, paddleWidth, paddleHeight);

    if (x + dx > canvas.width - 8 || x + dx < 8) dx = -dx;
    if (y + dy < 8) dy = -dy;
    else if (y + dy > canvas.height - paddleHeight - 18) {
      if (x > paddleX && x < paddleX + paddleWidth) {
        dy = -Math.abs(dy);
        score += 10;
        if (scoreEl) scoreEl.textContent = score;
      } else if (y + dy > canvas.height - 8) {
        x = 200; y = 200; dx = 3; dy = -3;
        score = 0;
        if (scoreEl) scoreEl.textContent = '0';
      }
    }

    x += dx;
    y += dy;
    requestAnimationFrame(draw);
  }

  draw();
})();'''

        return {
            "index.html": html_code,
            "style.css": css_code,
            "game.js": js_code,
            "README.md": "# Arcade Game\nOpen `index.html` in browser.\n"
        }


class DeterministicFallback(BaseAIProvider):
    def __init__(self):
        super().__init__("builtin", "Built-in", requires_key=False)
        self.is_configured = True
        self.enabled = True

    def verify_key(self, api_key: str) -> Tuple[bool, str, str]:
        return True, "valid", "Built-in engine ready."

    def query(self, prompt: str, system_prompt: str, conversation_context: Optional[List[Dict[str, Any]]] = None, attachments: Optional[List[Dict[str, Any]]] = None, attachment_manager: Optional[Any] = None) -> Optional[str]:
        return None


class AIBrain:
    def __init__(self, storage_path: Optional[str] = None):
        self.conversation_history: List[Dict[str, Any]] = []
        self.system_prompt = (
            "You are a friendly, conversational AI Desktop Assistant.\n"
            "CRITICAL INSTRUCTION: Output ONLY your single, direct, user-facing response. "
            "Never output chain-of-thought, reasoning, options, drafts, checklists, evaluations, or meta-analysis."
        )

        # Initialize Universal Provider Management Architecture
        self.attachment_manager = AttachmentManager()
        mem_path = storage_path.replace(".json", "_memory.json") if storage_path else None
        self.memory_manager = MemoryManager(memory_path=mem_path)
        self.nvidia_provider = NVIDIAProvider()
        self.providers: Dict[str, BaseAIProvider] = {
            "builtin": DeterministicFallback(),
            "gemini": GeminiProvider(),
            "claude": ClaudeProvider(),
            "chatgpt": ChatGPTProvider(),
            "nvidia": self.nvidia_provider,
            "kimi": DirectNamedProvider("kimi", "Kimi", nvidia_ref=self.nvidia_provider),
            "deepseek": DirectNamedProvider("deepseek", "DeepSeek", nvidia_ref=self.nvidia_provider),
            "qwen": DirectNamedProvider("qwen", "Qwen", nvidia_ref=self.nvidia_provider)
        }

        self.active_provider = "builtin"
        self.onboarding_completed = False
        self.safety_mode = "balanced"
        self.last_telemetry: Dict[str, Any] = {}

        # Usage tracking (persistent daily request counters per provider)
        self.usage_file = storage_path.replace(".json", "_usage.json") if storage_path else os.path.expanduser("~/.ai_desktop_usage.json")
        self.usage_stats: Dict[str, Any] = {"days": {}}
        self._load_usage()

        # Settings Persistence Initialization
        self.settings_file = storage_path.replace(".json", "_settings.json") if storage_path else os.path.expanduser("~/.ai_desktop_settings.json")
        self._load_settings()

        # Conversation History Storage Initialization
        self.storage_file = storage_path or os.path.expanduser("~/.ai_desktop_conversations.json")
        self.conversations: Dict[str, Dict[str, Any]] = {}
        self.active_conversation_id: Optional[str] = None
        self._load_conversations_from_disk()

        # Core known registry with comprehensive aliases for instant fuzzy resolution
        self.known_app_registry = {
            "chrome": {
                "key": "chrome",
                "name": "Google Chrome",
                "display_name": "Google Chrome",
                "aliases": ["chrome", "google chrome", "browser", "web browser", "chrom", "crome", "google crom", "gchrome", "googlechrome", "chome"],
                "icon": "chrome"
            },
            "notepad": {
                "key": "notepad",
                "name": "Notepad",
                "display_name": "Notepad",
                "aliases": ["notepad", "text editor", "notes", "editor", "notpad", "notepd", "notepadd", "ntpd", "notpd"],
                "icon": "file-text"
            },
            "vscode": {
                "key": "vscode",
                "name": "Visual Studio Code",
                "display_name": "Visual Studio Code",
                "aliases": ["vscode", "vs code", "code", "code editor", "vscodee", "vsc", "vscod", "visual studio code", "vcode"],
                "icon": "code"
            },
            "discord": {
                "key": "discord",
                "name": "Discord",
                "display_name": "Discord",
                "aliases": ["discord", "discrod", "discrd", "dicord", "disocrd", "discort", "discor", "dc", "chat"],
                "icon": "message-square"
            },
            "roblox_player": {
                "key": "roblox_player",
                "name": "Roblox Player",
                "display_name": "Roblox Player",
                "aliases": ["roblox", "roblox player", "roblx", "robloxplayer", "roblox game", "rblx"],
                "icon": "gamepad"
            },
            "roblox_studio": {
                "key": "roblox_studio",
                "name": "Roblox Studio",
                "display_name": "Roblox Studio",
                "aliases": ["roblox studio", "roblox stduio", "robloxstudio", "roblox development"],
                "icon": "gamepad"
            },
            "calculator": {
                "key": "calculator",
                "name": "Windows Calculator",
                "display_name": "Windows Calculator",
                "aliases": ["calc", "calculator", "math", "calcultr", "calculater", "clac", "calculat", "calcuator", "windows calculator"],
                "icon": "calculator"
            },
            "terminal": {
                "key": "terminal",
                "name": "Windows Terminal",
                "display_name": "Windows Terminal",
                "aliases": ["terminal", "windows terminal", "wt", "termnl", "trminal"],
                "icon": "terminal"
            },
            "explorer": {
                "key": "explorer",
                "name": "File Explorer",
                "display_name": "File Explorer",
                "aliases": ["explorer", "file explorer", "files", "my computer", "finder", "explorr", "my files", "this pc"],
                "icon": "folder"
            },
            "chatgpt_desktop": {
                "key": "chatgpt_desktop",
                "name": "ChatGPT Desktop",
                "display_name": "ChatGPT Desktop",
                "aliases": [
                    "chatgpt desktop", "chatgpt", "chat gpt desktop", "chat gpt",
                    "chatgpt app", "openai chatgpt", "chatgpt application",
                    "chatgpt desktop app", "chatgpt client"
                ],
                "icon": "sparkles"
            },
            "minecraft": {
                "key": "minecraft",
                "name": "Minecraft Launcher",
                "display_name": "Minecraft Launcher",
                "aliases": ["minecraft", "minecraft launcher", "mc", "minecraft game", "mine craft"],
                "icon": "gamepad"
            },
            "spotify": {
                "key": "spotify",
                "name": "Spotify",
                "display_name": "Spotify",
                "aliases": ["spotify", "music", "songs", "spotfy", "spotifay", "spofity", "spoty"],
                "icon": "music"
            },
            "paint": {
                "key": "paint",
                "name": "Paint",
                "display_name": "Paint",
                "aliases": ["paint", "mspaint", "drawing", "pnt", "ms paint", "microsoft paint"],
                "icon": "image"
            },
            "settings": {
                "key": "settings",
                "name": "Windows Settings",
                "display_name": "Windows Settings",
                "aliases": ["settings", "windows settings", "config", "settngs", "sttings", "pc settings"],
                "icon": "settings"
            },
            "edge": {
                "key": "edge",
                "name": "Microsoft Edge",
                "display_name": "Microsoft Edge",
                "aliases": ["edge", "ms edge", "microsoft edge", "edg", "msedge"],
                "icon": "globe"
            },
            "slack": {
                "key": "slack",
                "name": "Slack",
                "display_name": "Slack",
                "aliases": ["slack", "slck", "slak"],
                "icon": "message-square"
            },
            "zoom": {
                "key": "zoom",
                "name": "Zoom",
                "display_name": "Zoom",
                "aliases": ["zoom", "zm", "zoom meeting"],
                "icon": "video"
            },
            "steam": {
                "key": "steam",
                "name": "Steam",
                "display_name": "Steam",
                "aliases": ["steam", "stem", "gaming"],
                "icon": "gamepad"
            },
            "word": {
                "key": "word",
                "name": "Microsoft Word",
                "display_name": "Microsoft Word",
                "aliases": ["word", "ms word", "winword", "doc editor"],
                "icon": "file-text"
            },
            "excel": {
                "key": "excel",
                "name": "Microsoft Excel",
                "display_name": "Microsoft Excel",
                "aliases": ["excel", "ms excel", "spreadsheet", "sheets", "excl"],
                "icon": "table"
            },
            "task_manager": {
                "key": "task_manager",
                "name": "Task Manager",
                "display_name": "Task Manager",
                "aliases": ["task manager", "taskmgr", "task mgr", "task_manager", "taskmanger", "taks manager", "task manager please", "processes", "kill process"],
                "icon": "cpu"
            },
            "snipping_tool": {
                "key": "snipping_tool",
                "name": "Snipping Tool",
                "display_name": "Snipping Tool",
                "aliases": ["snipping tool", "snippingtool", "snip", "snip & sketch", "screen snip", "snipping"],
                "icon": "camera"
            },
            "control_panel": {
                "key": "control_panel",
                "name": "Control Panel",
                "display_name": "Control Panel",
                "aliases": ["control panel", "control", "controlpanel"],
                "icon": "settings"
            },
            "cmd": {
                "key": "cmd",
                "name": "Command Prompt",
                "display_name": "Command Prompt",
                "aliases": ["cmd", "command prompt", "commandprompt", "terminal cmd", "cmd.exe", "console", "dos prompt", "command line"],
                "icon": "terminal"
            },
            "powershell": {
                "key": "powershell",
                "name": "PowerShell",
                "display_name": "PowerShell",
                "aliases": ["powershell", "posh", "pwsh", "powrshell", "windows powershell", "power shell"],
                "icon": "terminal"
            },
            "registry_editor": {
                "key": "registry_editor",
                "name": "Registry Editor",
                "display_name": "Registry Editor",
                "aliases": ["regedit", "registry editor", "registry", "regedit.exe"],
                "icon": "settings"
            },
            "device_manager": {
                "key": "device_manager",
                "name": "Device Manager",
                "display_name": "Device Manager",
                "aliases": ["device manager", "devmgmt", "devices", "hardware manager"],
                "icon": "cpu"
            },
            "services": {
                "key": "services",
                "name": "Services",
                "display_name": "Services",
                "aliases": ["services", "services.msc", "windows services", "service manager"],
                "icon": "settings"
            },
            "disk_management": {
                "key": "disk_management",
                "name": "Disk Management",
                "display_name": "Disk Management",
                "aliases": ["disk management", "diskmgmt", "disk manager", "partitions", "format disk"],
                "icon": "hard-drive"
            },
            "system_information": {
                "key": "system_information",
                "name": "System Information",
                "display_name": "System Information",
                "aliases": ["system information", "msinfo32", "system info", "system specs", "hardware specs"],
                "icon": "info"
            },
            "resource_monitor": {
                "key": "resource_monitor",
                "name": "Resource Monitor",
                "display_name": "Resource Monitor",
                "aliases": ["resource monitor", "resmon", "perfmon /res", "res mon"],
                "icon": "activity"
            },
            "event_viewer": {
                "key": "event_viewer",
                "name": "Event Viewer",
                "display_name": "Event Viewer",
                "aliases": ["event viewer", "eventvwr", "event logs", "system logs", "crash logs"],
                "icon": "file-text"
            },
            "task_scheduler": {
                "key": "task_scheduler",
                "name": "Task Scheduler",
                "display_name": "Task Scheduler",
                "aliases": ["task scheduler", "taskschd", "scheduled tasks", "cron"],
                "icon": "clock"
            },
            "computer_management": {
                "key": "computer_management",
                "name": "Computer Management",
                "display_name": "Computer Management",
                "aliases": ["computer management", "compmgmt", "management console"],
                "icon": "settings"
            },
            "windows_security": {
                "key": "windows_security",
                "name": "Windows Security",
                "display_name": "Windows Security",
                "aliases": ["windows security", "windows defender", "security", "defender", "antivirus"],
                "icon": "shield"
            },
            "windows_update": {
                "key": "windows_update",
                "name": "Windows Update",
                "display_name": "Windows Update",
                "aliases": ["windows update", "check for updates", "update settings", "update windows"],
                "icon": "refresh-cw"
            },
            "network_connections": {
                "key": "network_connections",
                "name": "Network Connections",
                "display_name": "Network Connections",
                "aliases": ["network connections", "network settings", "ncpa", "adapter settings", "wifi settings"],
                "icon": "wifi"
            },
            "bluetooth_settings": {
                "key": "bluetooth_settings",
                "name": "Bluetooth Settings",
                "display_name": "Bluetooth Settings",
                "aliases": ["bluetooth", "bluetooth settings", "pair device", "bluetooth devices"],
                "icon": "bluetooth"
            },
            "display_settings": {
                "key": "display_settings",
                "name": "Display Settings",
                "display_name": "Display Settings",
                "aliases": ["display settings", "screen resolution", "display", "monitor settings"],
                "icon": "monitor"
            },
            "sound_settings": {
                "key": "sound_settings",
                "name": "Sound Settings",
                "display_name": "Sound Settings",
                "aliases": ["sound settings", "audio settings", "sound", "volume settings", "sound control"],
                "icon": "volume-2"
            },
            "apps_features": {
                "key": "apps_features",
                "name": "Apps & Features",
                "display_name": "Apps & Features",
                "aliases": ["apps and features", "installed apps", "add or remove programs", "uninstall a program"],
                "icon": "app-window"
            }
        }

    # =========================================================================
    # REAL API CONNECTION VERIFICATION & PROVIDER MANAGEMENT
    # =========================================================================

    def configure_provider(self, provider_id: str, api_key: str, enabled: bool = True, skip_verification: bool = False) -> Dict[str, Any]:
        """
        Configures an API key and performs real authentication verification.
        If valid: saves key, marks provider as configured and enabled.
        If invalid: does NOT save key or mark as configured. Returns user-friendly error.
        """
        p_id = provider_id.lower().strip()
        if p_id not in self.providers:
            return {
                "error": f"Unknown provider '{provider_id}'",
                "success": False,
                "configured": False,
                "enabled": False,
                "active": False,
                "message": f"Unknown provider '{provider_id}'"
            }

        provider = self.providers[p_id]
        if not provider.requires_key:
            provider.configure(api_key="", enabled=True)
            return {
                "success": True,
                "verified": True,
                "configured": True,
                "enabled": True,
                "active": (self.active_provider == p_id),
                "provider": provider.to_dict(is_active=(self.active_provider == p_id)),
                "message": f"{provider.display_name} is active."
            }

        clean_key = (api_key or "").strip()
        if not clean_key:
            return {
                "success": False,
                "configured": False,
                "enabled": False,
                "active": False,
                "error_type": "invalid_key",
                "error": f"{provider.display_name} API key is invalid. Please check your key and try again.",
                "message": f"{provider.display_name} API key is invalid. Please check your key and try again."
            }

        # Real API Connection Verification
        if not skip_verification:
            is_valid, err_type, err_msg = provider.verify_key(clean_key)
            if not is_valid:
                # Do NOT activate or mark as configured
                return {
                    "success": False,
                    "configured": False,
                    "enabled": False,
                    "active": False,
                    "error_type": err_type,
                    "error": err_msg,
                    "message": err_msg
                }

        # Verification succeeded: securely save key and mark as configured
        provider.configure(clean_key, enabled=enabled)

        # If NVIDIA is configured, enable the NVIDIA-backed choices (Kimi, DeepSeek, Qwen)
        if p_id == "nvidia":
            for choice_id in ["kimi", "deepseek", "qwen"]:
                if choice_id in self.providers:
                    self.providers[choice_id].enabled = enabled
                    self.providers[choice_id].is_configured = self.nvidia_provider.is_configured

        return {
            "success": True,
            "verified": True,
            "configured": True,
            "enabled": provider.enabled,
            "active": (self.active_provider == p_id),
            "provider": provider.to_dict(is_active=(self.active_provider == p_id)),
            "message": f"{provider.display_name} API key verified and configured successfully."
        }

    def remove_provider_key(self, provider_id: str) -> Dict[str, Any]:
        """Removes an API key, automatically marking the provider as unconfigured/disabled."""
        p_id = provider_id.lower().strip()
        if p_id in self.providers:
            provider = self.providers[p_id]
            provider.remove_key()
            if self.active_provider == p_id:
                # Gracefully fall back to another enabled provider or builtin
                fallback = "builtin"
                for k, p in self.providers.items():
                    if p.enabled and (p.is_configured or not p.requires_key):
                        fallback = k
                        break
                self.active_provider = fallback
            return provider.to_dict(is_active=(self.active_provider == p_id))
        return {"error": f"Unknown provider '{provider_id}'", "success": False}

    def set_provider_enabled(self, provider_id: str, enabled: bool) -> Dict[str, Any]:
        """Toggles Enable/Disable for a provider."""
        p_id = provider_id.lower().strip()
        if p_id in self.providers:
            provider = self.providers[p_id]
            if enabled:
                provider.enable()
            else:
                provider.disable()
                if self.active_provider == p_id:
                    self.active_provider = "builtin"
            return provider.to_dict(is_active=(self.active_provider == p_id))
        return {"error": f"Unknown provider '{provider_id}'", "success": False}

    def set_active_provider(self, provider_id: str) -> Dict[str, Any]:
        """Sets the active AI provider. Only enabled and configured providers can be selected."""
        p_id = provider_id.lower().strip()
        if p_id not in self.providers:
            return {"error": f"Provider '{provider_id}' not found.", "success": False}

        provider = self.providers[p_id]
        # Check if directly enabled or routed via configured NVIDIA provider
        is_ready = provider.enabled or (isinstance(provider, DirectNamedProvider) and self.nvidia_provider.enabled and self.nvidia_provider.is_configured) or p_id == "builtin"

        if not is_ready:
            return {
                "error": f"{provider.display_name} is currently disabled or not configured with an API key.",
                "success": False,
                "message": f"{provider.display_name} is currently disabled. Please enable it in Settings."
            }

        self.active_provider = p_id
        return {
            "success": True,
            "active_provider": p_id,
            "active_provider_name": provider.display_name,
            "message": f"Switched active AI to {provider.display_name}."
        }

    def get_providers_list(self) -> List[Dict[str, Any]]:
        """Returns clean list of all providers with simple AI names ONLY."""
        result = []
        for p_id, provider in self.providers.items():
            result.append(provider.to_dict(is_active=(self.active_provider == p_id)))
        return result

    def get_settings(self) -> Dict[str, Any]:
        """Returns safe public settings without exposing raw keys."""
        active_p = self.providers.get(self.active_provider, self.providers["builtin"])
        return {
            "onboarding_completed": self.onboarding_completed,
            "active_provider": self.active_provider,
            "active_provider_name": active_p.display_name,
            "safety_mode": self.safety_mode,
            "providers": self.get_providers_list(),
            "has_claude_key": bool(self.providers["claude"].api_key),
            "has_chatgpt_key": bool(self.providers["chatgpt"].api_key),
            "has_nvidia_key": bool(self.nvidia_provider.api_key),
            "has_gemini_key": bool(self.providers["gemini"].api_key),
            "nvidia_choices": ["Kimi", "DeepSeek", "Qwen"]
        }

    def _load_settings(self):
        if hasattr(self, "settings_file") and os.path.exists(self.settings_file) and os.path.getsize(self.settings_file) > 0:
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.safety_mode = data.get("safety_mode", "balanced")
                        if "onboarding_completed" in data:
                            self.onboarding_completed = data["onboarding_completed"]
                        if "active_provider" in data and data["active_provider"] in self.providers:
                            self.active_provider = data["active_provider"]
            except Exception as e:
                print(f"[AIBrain] Settings load notice: {e}")

    def _save_settings(self):
        if hasattr(self, "settings_file"):
            try:
                with open(self.settings_file, "w", encoding="utf-8") as f:
                    json.dump({
                        "safety_mode": self.safety_mode,
                        "active_provider": self.active_provider,
                        "onboarding_completed": self.onboarding_completed
                    }, f, indent=2)
            except Exception as e:
                print(f"[AIBrain] Settings save notice: {e}")

    def set_safety_mode(self, mode: str):
        if mode in ["strict", "balanced", "developer"]:
            self.safety_mode = mode
            self._save_settings()

    def _load_usage(self):
        if hasattr(self, "usage_file") and os.path.exists(self.usage_file) and os.path.getsize(self.usage_file) > 0:
            try:
                with open(self.usage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "days" in data:
                        self.usage_stats = data
            except Exception:
                pass

    def _save_usage(self):
        if hasattr(self, "usage_file"):
            try:
                with open(self.usage_file, "w", encoding="utf-8") as f:
                    json.dump(self.usage_stats, f, indent=2)
            except Exception:
                pass

    def record_usage(self, provider_id: str, success: bool, approx_tokens: int = 0):
        """Record one AI request against today's daily usage bucket."""
        try:
            today = time.strftime("%Y-%m-%d")
            self.usage_stats.setdefault("days", {})
            day = self.usage_stats["days"].setdefault(today, {
                "requests": 0, "success": 0, "failed": 0, "tokens": 0, "providers": {}
            })
            day["requests"] += 1
            day["success" if success else "failed"] += 1
            day["tokens"] += int(approx_tokens or 0)
            p = day["providers"].setdefault(provider_id, {"requests": 0, "tokens": 0})
            p["requests"] += 1
            p["tokens"] += int(approx_tokens or 0)
            self._save_usage()
        except Exception:
            pass

    def get_usage_stats(self) -> Dict[str, Any]:
        """Return usage summary: today + last 7 days + per-provider breakdown."""
        try:
            days = self.usage_stats.get("days", {})
            today = time.strftime("%Y-%m-%d")
            today_stats = days.get(today, {"requests": 0, "success": 0, "failed": 0, "tokens": 0, "providers": {}})
            # Last 7 days totals
            last7 = {"requests": 0, "success": 0, "failed": 0, "tokens": 0}
            sorted_days = sorted(days.keys())[-7:]
            for d in sorted_days:
                dd = days[d]
                for k in ["requests", "success", "failed", "tokens"]:
                    last7[k] += dd.get(k, 0)
            return {
                "today": today_stats,
                "last_7_days": last7,
                "total_days": len(days)
            }
        except Exception:
            return {"today": {"requests": 0, "tokens": 0}, "last_7_days": {"requests": 0, "tokens": 0}, "total_days": 0}

    def _load_conversations_from_disk(self):
        if os.path.exists(self.storage_file) and os.path.getsize(self.storage_file) > 0:
            try:
                with open(self.storage_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.conversations = data.get("conversations", {})
                        self.active_conversation_id = data.get("active_conversation_id")
            except Exception as e:
                print(f"[AIBrain] Conversation load notice: {e}")

    def _save_conversations_to_disk(self):
        try:
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump({
                    "conversations": self.conversations,
                    "active_conversation_id": self.active_conversation_id
                }, f, indent=2)
        except Exception as e:
            print(f"[AIBrain] Conversation save notice: {e}")

    def list_conversations(self, include_empty: bool = False) -> List[Dict[str, Any]]:
        result = []
        for c_id, c_data in self.conversations.items():
            msgs = c_data.get("messages", [])
            # Filter out empty conversations (0 messages) so empty draft chats don't appear in Recent Chats
            if len(msgs) == 0 and not include_empty:
                continue
            result.append({
                "id": c_id,
                "title": c_data.get("title", "Conversation"),
                "created_at": c_data.get("created_at", time.time()),
                "updated_at": c_data.get("updated_at", time.time()),
                "message_count": len(msgs)
            })
        result.sort(key=lambda x: x.get("updated_at", 0), reverse=True)
        return result

    def create_conversation(self, title: str = "New Chat", initial_messages: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        c_id = f"conv_{int(time.time() * 1000)}_{len(self.conversations) + 1}"
        now = time.time()
        conv = {
            "id": c_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "messages": initial_messages or []
        }
        self.conversations[c_id] = conv
        self.active_conversation_id = c_id
        self._save_conversations_to_disk()
        return conv

    def get_conversation(self, conv_id: str) -> Optional[Dict[str, Any]]:
        return self.conversations.get(conv_id)

    def rename_conversation(self, conv_id: str, new_title: str) -> bool:
        if conv_id in self.conversations:
            clean_title = new_title.strip()
            if clean_title:
                self.conversations[conv_id]["title"] = clean_title
                self.conversations[conv_id]["updated_at"] = time.time()
                self._save_conversations_to_disk()
                return True
        return False

    def delete_conversation(self, conv_id: str) -> bool:
        if conv_id in self.conversations:
            del self.conversations[conv_id]
            if self.active_conversation_id == conv_id:
                remaining = list(self.conversations.keys())
                self.active_conversation_id = remaining[0] if remaining else None
            self._save_conversations_to_disk()
            return True
        return False

    def add_message_pair_to_conversation(self, conv_id: Optional[str], user_msg: Dict[str, Any], ai_msg: Dict[str, Any]) -> str:
        target_id = conv_id
        if not target_id or target_id not in self.conversations:
            conv = self.create_conversation(title="New Chat")
            target_id = conv["id"]

        conv = self.conversations[target_id]
        messages = conv.setdefault("messages", [])

        # If title is default "New Chat", auto-generate short title from user message
        if conv.get("title") in ["New Chat", "New Conversation"] and user_msg.get("content"):
            user_text = str(user_msg.get("content")).strip()
            short_title = user_text[:30].title() + ("..." if len(user_text) > 30 else "")
            conv["title"] = short_title if short_title else "New Chat"

        messages.append(user_msg)
        messages.append(ai_msg)
        conv["updated_at"] = time.time()
        self.active_conversation_id = target_id
        self._save_conversations_to_disk()
        return target_id

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        return self.conversation_history

    def clear_history(self):
        self.conversation_history = []

    def complete_onboarding(self, api_key: Optional[str] = None, skip: bool = False) -> Dict[str, Any]:
        """
        Completes the first-launch onboarding flow.
        Gemini API key is optional.
        Backend is the SINGLE SOURCE OF TRUTH:
        - If skip is True or api_key is empty: Gemini remains unconfigured and active provider is 'builtin'.
        - If api_key is provided: performs real verification via configure_provider(skip_verification=False).
          Only if verification succeeds does Gemini become configured and active.
          If verification fails: onboarding is NOT completed with Gemini, returns structured failure result.
        """
        clean_key = (api_key or "").strip()
        if skip or not clean_key:
            self.onboarding_completed = True
            self.active_provider = "builtin"
            return {
                "success": True,
                "status": "completed",
                "onboarding_completed": True,
                "configured": False,
                "enabled": False,
                "active": False,
                "active_provider": "builtin",
                "active_provider_name": self.providers["builtin"].display_name,
                "has_gemini_key": False,
                "message": "Onboarding completed with Built-in engine."
            }

        # User entered a key to configure Gemini during onboarding
        cfg_res = self.configure_provider("gemini", api_key=clean_key, enabled=True, skip_verification=False)
        if not cfg_res.get("success", False):
            # Verification failed: DO NOT complete onboarding, DO NOT activate Gemini
            return {
                "success": False,
                "status": "failed",
                "onboarding_completed": self.onboarding_completed,
                "configured": False,
                "enabled": False,
                "active": False,
                "active_provider": self.active_provider,
                "active_provider_name": self.providers[self.active_provider].display_name,
                "has_gemini_key": False,
                "error_type": cfg_res.get("error_type", "invalid_key"),
                "error": cfg_res.get("error", "Gemini API key is invalid. Please check your key and try again."),
                "message": cfg_res.get("message", "Gemini API key is invalid. Please check your key and try again.")
            }

        # Verification succeeded!
        self.onboarding_completed = True
        self.active_provider = "gemini"
        return {
            "success": True,
            "status": "completed",
            "onboarding_completed": True,
            "configured": True,
            "enabled": True,
            "active": True,
            "active_provider": "gemini",
            "active_provider_name": self.providers["gemini"].display_name,
            "has_gemini_key": True,
            "message": "Gemini connected successfully."
        }

    def resolve_fuzzy_app(self, candidate_str: str) -> Tuple[Optional[str], Optional[Dict[str, Any]], float]:
        raw = candidate_str.lower().strip()
        # Strip common English & Hinglish modifiers
        norm = re.sub(r"\b(?:the|a|an|new|another|separate|app|application|program|software|window|instance|bhai|bro|please|plz|khol|khol\s+de|kholo|chala|chalao|karo|kar|de|open|start|run|launch)\b", "", raw).strip()
        norm = re.sub(r"[\s_\-]+", " ", norm)
        norm_no_spaces = norm.replace(" ", "")

        if not norm:
            return None, None, 0.0

        if norm in self.known_app_registry:
            return norm, self.known_app_registry[norm], 1.0

        for key, info in self.known_app_registry.items():
            disp_name = info.get("display_name", info.get("name", "")).lower()
            key_aliases = [a.lower() for a in info.get("aliases", [])]

            if norm == disp_name or norm_no_spaces == key.replace("_", ""):
                return key, info, 1.0
            if norm in key_aliases or norm_no_spaces in [a.replace(" ", "") for a in key_aliases]:
                return key, info, 0.98

        best_match_key = None
        best_match_info = None
        best_score = 0.0

        for key, info in self.known_app_registry.items():
            disp_name = info.get("display_name", info.get("name", "")).lower()
            disp_clean = re.sub(r"[\s_\-]+", " ", disp_name)
            aliases = [a.lower() for a in info.get("aliases", [])]

            score = 0.0
            if set(norm.split()) == set(disp_clean.split()):
                score = 0.95
            elif disp_name.startswith(norm) or (len(norm) >= 4 and any(a.startswith(norm) for a in aliases)):
                score = 0.88
            elif (len(norm) >= 4 and norm in disp_name) or (len(norm) >= 4 and any(norm in a for a in aliases)):
                score = 0.82
            else:
                candidates = [key, disp_name, disp_clean] + aliases
                for c in candidates:
                    r1 = difflib.SequenceMatcher(None, norm, c).ratio()
                    r2 = difflib.SequenceMatcher(None, norm_no_spaces, c.replace(" ", "")).ratio()
                    score = max(score, r1, r2)

            if score > best_score:
                best_score = score
                best_match_key = key
                best_match_info = info

        if best_match_key and best_score >= 0.78:
            return best_match_key, best_match_info, best_score

        return None, None, 0.0

    def query_active_provider(self, prompt: str, conversation_context: Optional[List[Dict[str, Any]]] = None, attachments: Optional[List[Dict[str, Any]]] = None) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Queries the currently selected active provider and tracks telemetry:
        active_provider, request_started, request_completed, request_failed, fallback_used.
        If an external provider is selected and the request fails, does NOT silently answer using Built-in.
        """
        active_id = self.active_provider
        provider = self.providers.get(active_id, self.providers["builtin"])

        telemetry = {
            "active_provider": active_id,
            "active_provider_name": provider.display_name,
            "request_started": True,
            "request_completed": False,
            "request_failed": False,
            "fallback_used": False,
            "routed_model": None
        }

        # 1. Built-in Local Engine
        if active_id == "builtin":
            telemetry["request_completed"] = True
            self.last_telemetry = telemetry
            return None, telemetry

        # 2. External Provider Configuration Check
        if not getattr(provider, "_test_query_hook", None) and (not provider.enabled or (provider.requires_key and not provider.api_key and not (isinstance(provider, DirectNamedProvider) and self.nvidia_provider.enabled and self.nvidia_provider.api_key))):
            telemetry["request_failed"] = True
            self.last_telemetry = telemetry
            msg = f"{provider.display_name} is currently unavailable. You can switch to another configured AI provider in Settings."
            return msg, telemetry

        try:
            if isinstance(provider, DirectNamedProvider):
                telemetry["routed_model"] = self.nvidia_provider._internal_models.get(provider.provider_id)
            elif isinstance(provider, NVIDIAProvider):
                telemetry["routed_model"] = provider._internal_models.get(provider.active_nvidia_choice)

            resp = provider.query(
                prompt,
                self.system_prompt,
                conversation_context=conversation_context,
                attachments=attachments,
                attachment_manager=self.attachment_manager
            )
            if resp:
                telemetry["request_completed"] = True
                self.last_telemetry = telemetry
                self.record_usage(active_id, success=True, approx_tokens=max(1, len(prompt) // 4))
                return resp, telemetry
            else:
                telemetry["request_failed"] = True
                self.last_telemetry = telemetry
                self.record_usage(active_id, success=False)
                err_msg = getattr(provider, "last_error_message", None)
                if not err_msg:
                    err_msg = f"{provider.display_name} is currently unavailable. You can switch to another configured AI provider in Settings."
                return err_msg, telemetry
        except Exception:
            telemetry["request_failed"] = True
            self.last_telemetry = telemetry
            self.record_usage(active_id, success=False)
            err_msg = getattr(provider, "last_error_message", None)
            if not err_msg:
                err_msg = f"{provider.display_name} is currently unavailable. You can switch to another configured AI provider in Settings."
            return err_msg, telemetry

    def _query_ai_for_intent(self, prompt: str, workspace: str, conversation_context: Optional[List[Dict[str, Any]]] = None, attachments: Optional[List[Dict[str, Any]]] = None) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Sends the user query to the active external AI provider with the intent-understanding system prompt.
        Translates natural English, Hindi, and Hinglish into safe structured tool actions.
        """
        active_id = self.active_provider
        provider = self.providers.get(active_id, self.providers["builtin"])

        telemetry = {
            "active_provider": active_id,
            "active_provider_name": provider.display_name,
            "request_started": True,
            "request_completed": False,
            "request_failed": False,
            "fallback_used": False,
            "routed_model": None
        }

        if active_id == "builtin":
            telemetry["request_completed"] = True
            self.last_telemetry = telemetry
            return None, telemetry

        if not getattr(provider, "_test_query_hook", None) and (not provider.enabled or (provider.requires_key and not provider.api_key and not (isinstance(provider, DirectNamedProvider) and self.nvidia_provider.enabled and self.nvidia_provider.api_key))):
            telemetry["request_failed"] = True
            self.last_telemetry = telemetry
            msg = f"{provider.display_name} is currently unavailable. You can switch to another configured AI provider in Settings."
            return msg, telemetry

        intent_sys_prompt = (
            "You are the Natural Language Intent Understanding layer for an Zevion on Windows.\n"
            "Your role is to understand user requests in natural English, Hindi, or Hinglish, and translate them into structured computer intents for the deterministic execution engine.\n\n"
            "Supported tools ONLY:\n"
            "- open_application: {\"tool\": \"open_application\", \"parameters\": {\"app_name\": \"<app_key>\", \"new_window\": false}}\n"
            "  Known apps: chrome, notepad, cmd, powershell, vscode, discord, roblox_player, roblox_studio, calculator, paint, explorer, settings, control_panel, task_manager, terminal, chatgpt_desktop, spotify, minecraft, etc. Set \"new_window\": true for a new/another window.\n"
            "- open_website: {\"tool\": \"open_website\", \"parameters\": {\"url\": \"<url>\", \"search_query\": \"<query>\", \"playback\": true/false, \"play_first\": true/false, \"filter_latest\": true/false, \"channel\": \"<creator>\", \"is_shorts\": true/false}}\n"
            "  For YouTube Shorts: {\"tool\": \"open_website\", \"parameters\": {\"url\": \"https://www.youtube.com/shorts\", \"search_query\": \"...\", \"playback\": true, \"play_first\": true, \"is_shorts\": true}}\n"
            "  For YouTube video playback: {\"tool\": \"open_website\", \"parameters\": {\"search_query\": \"...\", \"playback\": true, \"play_first\": true}}\n"
            "  For web search: {\"tool\": \"open_website\", \"parameters\": {\"url\": \"https://www.google.com/search?q=...\", \"search_query\": \"...\"}}\n"
            "- type_text: {\"tool\": \"type_text\", \"parameters\": {\"text\": \"<text>\", \"target_app\": \"<app_key>\"}}\n"
            "- minimize_window: {\"tool\": \"minimize_window\", \"parameters\": {\"app_name\": \"current\" | \"<app_key>\"}}\n"
            "- maximize_window: {\"tool\": \"maximize_window\", \"parameters\": {\"app_name\": \"current\" | \"<app_key>\"}}\n"
            "- restore_window: {\"tool\": \"restore_window\", \"parameters\": {\"app_name\": \"current\" | \"<app_key>\"}}\n"
            "- close_window: {\"tool\": \"close_window\", \"parameters\": {\"app_name\": \"current\" | \"<app_key>\"}}\n"
            "- create_folder: {\"tool\": \"create_folder\", \"parameters\": {\"folder_path\": \"<name>\"}}\n"
            "- create_file: {\"tool\": \"create_file\", \"parameters\": {\"path\": \"<file>\", \"content\": \"<content>\"}}\n"
            "- read_file: {\"tool\": \"read_file\", \"parameters\": {\"path\": \"<file>\"}}\n"
            "- delete_file: {\"tool\": \"delete_file\", \"parameters\": {\"path\": \"<file>\"}}\n"
            "- organize_files: {\"tool\": \"organize_files\", \"parameters\": {\"directory\": \"Downloads\" | \"Desktop\"}}\n"
            "- take_screenshot: {\"tool\": \"take_screenshot\", \"parameters\": {\"region\": \"fullscreen\", \"save_path\": \"screenshot.png\"}}\n"
            "- execute_command: {\"tool\": \"execute_command\", \"parameters\": {\"command\": \"<cmd>\"}}\n"
            "- get_system_info: {\"tool\": \"get_system_info\", \"parameters\": {}}\n\n"
            "Rules:\n"
            "1. If the user's message is a natural language computer command or automation task, output a valid JSON object:\n"
            "{\n"
            "  \"summary\": \"<short description>\",\n"
            "  \"actions\": [\n"
            "    {\"tool\": \"<tool_name>\", \"parameters\": { ... }}\n"
            "  ],\n"
            "  \"response\": \"<natural explanation of what will be done>\"\n"
            "}\n"
            "2. If the user's request CANNOT be safely mapped to the supported tools, do NOT invent unsupported commands or scripts. Output: {\"actions\": [], \"response\": \"<polite explanation that this specific operation is not currently supported>\"}.\n"
            "3. If the user is chatting, asking a general question, or seeking ideas, output a short, natural, human-like response (1-3 sentences, 5-25 words) matching the user's language and casual tone (English -> casual English; Hindi/Hinglish -> casual Hinglish like 'bhai', 'bro', 'kya scene hai', 'tu bata'): {\"actions\": [], \"response\": \"<short casual reply>\"}.\n"
            "4. Return ONLY the JSON object."
        )

        try:
            if isinstance(provider, DirectNamedProvider):
                telemetry["routed_model"] = self.nvidia_provider._internal_models.get(provider.provider_id)
            elif isinstance(provider, NVIDIAProvider):
                telemetry["routed_model"] = provider._internal_models.get(provider.active_nvidia_choice)

            resp = provider.query(
                prompt,
                intent_sys_prompt,
                conversation_context=conversation_context,
                attachments=attachments,
                attachment_manager=self.attachment_manager
            )
            if resp:
                telemetry["request_completed"] = True
                self.last_telemetry = telemetry
                return resp, telemetry
            else:
                telemetry["request_failed"] = True
                self.last_telemetry = telemetry
                err_msg = getattr(provider, "last_error_message", None) or f"{provider.display_name} is currently unavailable. You can switch to another configured AI provider in Settings."
                return err_msg, telemetry
        except Exception:
            telemetry["request_failed"] = True
            self.last_telemetry = telemetry
            err_msg = getattr(provider, "last_error_message", None) or f"{provider.display_name} is currently unavailable. You can switch to another configured AI provider in Settings."
            return err_msg, telemetry

    def _validate_and_normalize_ai_plan(self, ai_output_str: str, user_query: str, workspace: str) -> Optional[Dict[str, Any]]:
        """
        Parses JSON from the AI provider's output, validates each action against supported deterministic tools,
        and normalizes parameters. If the action is unsupported or unsafe, it rejects the action and returns conversational explanation.
        """
        if not ai_output_str or not isinstance(ai_output_str, str):
            return None

        clean_str = ai_output_str.strip()
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', clean_str, re.DOTALL)
        if json_match:
            clean_str = json_match.group(1).strip()
        else:
            first_brace = clean_str.find('{')
            last_brace = clean_str.rfind('}')
            if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
                clean_str = clean_str[first_brace:last_brace + 1].strip()

        try:
            data = json.loads(clean_str)
        except Exception:
            return None

        if not isinstance(data, dict):
            return None

        raw_actions = data.get("actions", [])
        ai_response = data.get("response", "")
        summary = data.get("summary", "Execute AI-interpreted actions")

        if not raw_actions:
            return {
                "summary": summary,
                "reasoning": f"AI interpreted request ({self.providers[self.active_provider].display_name}). No desktop actions required.",
                "actions": [],
                "safety_level": "safe",
                "confirmation_required": False,
                "response": self._sanitize_conversational_text(ai_response) if ai_response else "I have processed your request."
            }

        supported_tools = {
            "open_application", "open_website", "type_text", "minimize_window",
            "maximize_window", "restore_window", "close_window", "create_folder",
            "create_file", "write_file", "create_project", "read_file", "delete_file", "organize_files",
            "take_screenshot", "control_mouse", "execute_command", "get_system_info"
        }

        validated_actions = []
        has_dangerous = False
        confirmation_payload = None

        for act in raw_actions:
            if not isinstance(act, dict):
                continue
            tool = act.get("tool")
            if tool not in supported_tools:
                # Unsupported tool generated by AI -> reject and do not execute
                continue

            params = dict(act.get("parameters", {}))
            
            # Normalization per tool
            if tool == "open_application":
                raw_app = params.get("app_name", "")
                m_k, m_i, m_s = self.resolve_fuzzy_app(raw_app)
                if m_i:
                    params["app_name"] = m_k
                params["new_window"] = bool(params.get("new_window", False))
                act["description"] = f"Launch {params['app_name']}" if not params["new_window"] else f"Launch new {params['app_name']} window"

            elif tool == "open_website":
                url = params.get("url", "")
                sq = params.get("search_query", "")
                is_shorts = bool(params.get("is_shorts", False) or "shorts" in str(url).lower() or "shorts" in str(sq).lower())
                if is_shorts:
                    params["is_shorts"] = True
                    params["playback"] = True
                    if sq and "shorts" not in sq.lower():
                        params["search_query"] = f"{sq} shorts"
                    if not url or "google.com" in url:
                        if params.get("search_query"):
                            encoded = urllib.parse.quote_plus(params["search_query"])
                            params["url"] = f"https://www.youtube.com/results?search_query={encoded}"
                        else:
                            params["url"] = "https://www.youtube.com/shorts"
                elif params.get("playback") and sq and not url:
                    encoded = urllib.parse.quote_plus(sq)
                    params["url"] = f"https://www.youtube.com/results?search_query={encoded}"
                elif sq and not url:
                    encoded = urllib.parse.quote_plus(sq)
                    params["url"] = f"https://www.google.com/search?q={encoded}"
                act["description"] = f"Open {params.get('url', 'website')}"

            elif tool == "type_text":
                if "target_app" not in params:
                    params["target_app"] = "notepad"
                act["description"] = f"Type text into {params['target_app']}"

            elif tool == "delete_file":
                has_dangerous = True
                confirmation_payload = {
                    "action_title": f"Delete {params.get('path', 'file')}",
                    "severity": "high",
                    "impact": f"This will permanently delete '{params.get('path')}' from the filesystem.",
                    "tool": "delete_file",
                    "parameters": params
                }

            elif tool == "execute_command":
                cmd = params.get("command", "")
                if any(bad in cmd.lower() for bad in ["rm -rf", "format", "del /f", "drop database"]):
                    has_dangerous = True
                    confirmation_payload = {
                        "action_title": f"Execute Command '{cmd}'",
                        "severity": "high",
                        "impact": f"High risk command execution: '{cmd}'",
                        "tool": "execute_command",
                        "parameters": params
                    }

            act["parameters"] = params
            act["status"] = "pending"
            validated_actions.append(act)

        if not validated_actions:
            # AI produced something that was unsupported -> return clean conversational explanation
            clean_explanation = "I understand what you would like to do, but that specific operation is not currently supported on your desktop."
            return {
                "summary": "Unsupported Operation",
                "reasoning": "The requested computer task cannot be safely mapped to existing desktop tools.",
                "actions": [],
                "safety_level": "safe",
                "confirmation_required": False,
                "response": clean_explanation
            }

        return {
            "summary": summary,
            "reasoning": f"Parsed natural language request via {self.providers[self.active_provider].display_name}.",
            "actions": validated_actions,
            "safety_level": "dangerous" if has_dangerous else "safe",
            "confirmation_required": has_dangerous,
            "confirmation_payload": confirmation_payload,
            "response": self._sanitize_conversational_text(ai_response) if ai_response else f"I will {summary.lower()}."
        }

    def _format_action_response(self, act: Dict[str, Any], summary: str) -> str:
        tool_name = act.get("tool")
        if tool_name == "open_application":
            raw_app = act["parameters"].get("app_name", "")
            new_win = act["parameters"].get("new_window", False)
            m_k, m_i, m_s = self.resolve_fuzzy_app(raw_app)
            app_name = m_i.get("display_name", raw_app.replace("_", " ").title()) if m_i else raw_app.replace("_", " ").title()
            return f"Opening a new {app_name} window." if new_win else f"Opening {app_name}."
        elif tool_name == "open_website":
            q = act["parameters"].get("search_query", "")
            if act["parameters"].get("is_shorts"):
                return f"Opening and playing {q or 'YouTube Shorts'} on YouTube."
            elif act["parameters"].get("filter_latest"):
                ch = act["parameters"].get("channel", "creator")
                ch_display = "MrBeast" if ch.lower() == "mrbeast" else ch.title()
                return f"Finding and playing the latest video from {ch_display} on YouTube."
            elif act["parameters"].get("playback"):
                return f"Playing \"{q}\" on YouTube."
            elif q:
                return f"Searching for \"{q}\" in your browser."
            else:
                return f"Opening {act['parameters'].get('url', 'website')} in Google Chrome."
        elif tool_name == "minimize_window":
            app_target = act["parameters"].get("app_name", "current")
            disp = "current window" if app_target in ["current", "this", "active", "it"] else app_target.title()
            return f"Minimizing {disp}."
        elif tool_name == "maximize_window":
            app_target = act["parameters"].get("app_name", "current")
            disp = "current window" if app_target in ["current", "this", "active", "it"] else app_target.title()
            return f"Maximizing {disp}."
        elif tool_name == "restore_window":
            app_target = act["parameters"].get("app_name", "current")
            disp = "current window" if app_target in ["current", "this", "active", "it"] else app_target.title()
            return f"Restoring {disp}."
        elif tool_name == "close_window":
            app_target = act["parameters"].get("app_name", "current")
            disp = "current window" if app_target in ["current", "this", "active", "it"] else app_target.title()
            return f"Closing {disp}."
        elif tool_name == "type_text":
            return f"Typing text into {act['parameters'].get('target_app', 'notepad')}."
        elif tool_name == "create_folder":
            return f"I will create a folder named **{act['parameters'].get('folder_path')}**."
        elif tool_name in ["create_file", "write_file"]:
            return f"I will create the file **{act['parameters'].get('path')}**."
        elif tool_name == "create_project":
            return f"I will create the project **{act['parameters'].get('project_name')}**."
        elif tool_name == "read_file":
            return f"I will open and read the file **{act['parameters'].get('path')}** for you."
        elif tool_name == "delete_file":
            return f"⚠️ **Confirmation Required**: You have requested to delete **{act['parameters'].get('path')}**. Because this is a destructive action, please confirm to proceed."
        elif tool_name == "organize_files":
            return f"I will organize the files in your {act['parameters'].get('directory', 'Downloads')} folder."
        elif tool_name == "take_screenshot":
            return "I am capturing a screenshot of your current desktop."
        elif tool_name == "execute_command":
            return f"I will execute the command `{act['parameters'].get('command')}` in the terminal."
        elif tool_name == "get_system_info":
            return "I will inspect your system resources, CPU, RAM, and active processes."
        return f"I will {summary}."

    def process_message(self, user_message: str, current_workspace: str = "/home/user", conversation_id: Optional[str] = None, attachments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Main entry point for processing a user command.
        Handles normal conversation, Hinglish/multilingual requests, desktop action execution,
        and multimodal/file attachment reasoning.
        """
        timestamp = time.time()
        msg_clean = user_message.strip()
        user_attachments = attachments or []

        active_provider_obj = self.providers.get(self.active_provider, self.providers["builtin"])
        provider_label = active_provider_obj.display_name

        # Retrieve conversation context for active conversation
        target_conv_id = conversation_id or self.active_conversation_id
        conversation_context = []
        if target_conv_id and target_conv_id in self.conversations:
            raw_msgs = self.conversations[target_conv_id].get("messages", [])
            for m in raw_msgs[-12:]:
                c_role = m.get("role")
                c_text = str(m.get("content", "")).strip()
                c_atts = m.get("attachments", [])
                if c_role in ["user", "assistant"] and (c_text or c_atts) and not c_text.startswith("👋 Welcome"):
                    conversation_context.append({
                        "role": c_role,
                        "content": c_text,
                        "attachments": c_atts
                    })

        thoughts = [
            {
                "step": "understanding",
                "title": f"Understanding command ({provider_label})...",
                "detail": f"Analyzing query: \"{msg_clean or '[Attached Files]'}\"" + (f" with {len(user_attachments)} attachment(s)" if user_attachments else ""),
                "status": "completed",
                "timestamp": time.time()
            }
        ]

        plan = self._parse_intent_and_plan(msg_clean, current_workspace, conversation_context=conversation_context, attachments=user_attachments)
        
        thoughts.append({
            "step": "planning",
            "title": f"Decided Plan: {plan.get('summary', 'Execute action')}",
            "detail": plan.get("reasoning", "Parsed intent into structured tool call."),
            "status": "completed",
            "timestamp": time.time()
        })

        safety_level = plan.get("safety_level", "safe")
        confirmation_required = plan.get("confirmation_required", False)
        
        thoughts.append({
            "step": "safety",
            "title": f"Safety Verification: {safety_level.upper()}",
            "detail": plan.get("safety_reason", "Action verified against safety policy."),
            "status": "completed",
            "level": safety_level,
            "timestamp": time.time()
        })

        result = {
            "id": f"msg_{int(timestamp * 1000)}",
            "user_message": msg_clean,
            "attachments": user_attachments,
            "thoughts": thoughts,
            "actions": plan.get("actions", []),
            "response": plan.get("response", "I have processed your request."),
            "safety_level": safety_level,
            "confirmation_required": confirmation_required,
            "confirmation_payload": plan.get("confirmation_payload", None),
            "active_provider": self.active_provider,
            "active_provider_name": provider_label,
            "telemetry": self.last_telemetry,
            "timestamp": timestamp
        }

        self.conversation_history.append({
            "role": "user",
            "content": msg_clean,
            "attachments": user_attachments,
            "timestamp": timestamp
        })
        self.conversation_history.append({
            "role": "assistant",
            "content": result["response"],
            "actions": result["actions"],
            "timestamp": time.time()
        })

        return result

    def _sanitize_conversational_text(self, text: str) -> str:
        provider = self.providers.get(self.active_provider, self.providers["builtin"])
        return provider._sanitize_conversational_text(text)

    def _is_explicit_greeting_or_chat(self, text: str) -> bool:
        low = text.lower().strip()
        # Greetings (English & Hinglish)
        if re.match(r'^(?:hello|hi|hey|greetings|yo|yo\s+bro|howdy|namaste|satsriakal|good\s+(?:morning|afternoon|evening|day))[\s!\.\?,]*$', low) or low in ["yo", "yo bro", "bhai", "bro", "hey", "hello"]:
            return True
        # Status inquiry / How are you / Kya haal hai / Kaisa hai
        if re.search(r'\bhow\s+are\s+you(?:\s+doing)?\b|\bhow(?:\'s|\s+is)\s+(?:it\s+going|everything|your\s+day|life)\b|\b(?:kya\s+haal|kya\s+haal\s+chal|kaise\s+ho|kaisa\s+hai|kaise\s+hai|sab\s+badhiya)\b', low):
            return True
        # Memory recall questions (Name, preferences, favorites)
        if any(k in low for k in ["what is my name", "what was my name", "what's my name", "mera naam", "who am i", "my name is", "my name", "favorite game", "favourite game", "my favorite", "my favourite", "remember my name"]):
            return True
        # What are you doing / Bored / Kya karu / Kya kar rha hai / Kya scene hai
        if re.search(r'\bwhat\s+are\s+you\s+(?:doing|up\s+to)\b|\bwhat(?:\'s|\s+is)\s+up\b|\b(?:kya\s+karu|bore\s+ho\s+raha|kya\s+chal\s+raha|kya\s+kar\s+rha|kya\s+kar\s+raha|kya\s+scene\s+hai)\b', low):
            return True
        # Joke
        if re.search(r'\b(?:tell\s+me\s+a\s+joke|tell\s+a\s+joke|make\s+me\s+laugh|say\s+something\s+funny|joke)\b', low):
            return True
        # Gratitude
        if re.search(r'^(?:thank\s+you|thanks|thx|awesome|great\s+job|perfect|nice|cool|good\s+job|shukriya|dhanyawad)[\s!\.\?]*$', low):
            return True
        # Identity
        if re.search(r'\b(?:who\s+are\s+you|what\s+is\s+your\s+name|what\s+are\s+you|kaun\s+ho\s+tum|kaun\s+hai\s+tu)\b', low):
            return True
        # Capabilities / What can you do
        if re.search(r'\b(?:what\s+can\s+you\s+do|kya\s+kar\s+sakte?\s+ho|your\s+features|capabilities|kaunse\s+kaam|what\s+are\s+your\s+features)\b', low):
            return True
        # Time / Date
        if re.search(r'\b(?:what\s+time|what\s+is\s+the\s+time|whats\s+the\s+time|current\s+time|kya\s+time\s+hua|time\s+kya\s+hai|kitne\s+baje)\b', low):
            return True
        # Basic math
        if re.search(r'^\s*(?:calculate|calc|what\s+is|kitna\s+hua|solve)?\s*\(?\s*\d+(?:\.\d+)?\s*[+\-*/×÷x]\s*\d+(?:\.\d+)?\s*\)?\s*\??\s*$', low):
            return True
        return False

    def _handle_conversational_response(self, text: str, conversation_context: Optional[List[Dict[str, Any]]] = None, attachments: Optional[List[Dict[str, Any]]] = None) -> Optional[str]:
        raw_text = text.strip()
        low = raw_text.lower()

        # If attachments are present and an external AI provider is active, query the active provider
        if attachments and self.active_provider != "builtin":
            ai_reply, telemetry = self.query_active_provider(raw_text, conversation_context=conversation_context, attachments=attachments)
            if ai_reply:
                return self._sanitize_conversational_text(ai_reply)

        if not self._is_explicit_greeting_or_chat(raw_text) and not (attachments and self.active_provider == "builtin"):
            return None

        # If an external AI provider (Gemini, Claude, ChatGPT, etc.) is active, route conversational dialogue through it
        if self.active_provider != "builtin":
            ai_reply, telemetry = self.query_active_provider(raw_text, conversation_context=conversation_context, attachments=attachments)
            if ai_reply:
                return self._sanitize_conversational_text(ai_reply)

        # Check for explicit memory store request: "Remember that my name is xyz", "Remember that I like Python"
        mem_intent = self.memory_manager.extract_memory_intent(raw_text)
        if mem_intent:
            self.memory_manager.add_memory(mem_intent["key"], mem_intent["value"], mem_intent["text"])
            if "name" in mem_intent["key"]:
                return f"I've saved that to memory: Your name is {mem_intent['value']}! 🧠"
            return f"I've saved that to memory: \"{mem_intent['value']}\"! 🧠"

        # Built-in contextual memory recall (when running in basic mode without external AI)
        if conversation_context:
            # Check for name recall in local conversation
            if any(k in low for k in ["what is my name", "what was my name", "what's my name", "what is my name again", "what was my name again", "mera naam kya hai", "mera naam kya", "who am i", "do you know my name", "remember my name"]):
                for m in reversed(conversation_context):
                    if m.get("role") == "user":
                        u_txt = m.get("content", "")
                        name_match = re.search(r"\b(?:my name is|i am|naam|call me)\s+([a-zA-Z0-9]+)", u_txt, re.IGNORECASE)
                        if name_match:
                            found_name = name_match.group(1).strip().capitalize()
                            return f"Your name is {found_name}!" if "my name" in low or "who am i" in low else f"Aapka naam {found_name} hai bhai."

            # Check for favorite game recall
            if any(k in low for k in ["favorite game", "favourite game"]):
                for m in reversed(conversation_context):
                    if m.get("role") == "user":
                        u_txt = m.get("content", "")
                        game_match = re.search(r"\b(?:favorite game is|favourite game is|fav game is)\s+([a-zA-Z0-9\s]+)", u_txt, re.IGNORECASE)
                        if game_match:
                            found_game = game_match.group(1).strip().strip(".")
                            return f"Your favorite game is {found_game}."

        # Check Level 2 Primary/Global Memory across conversations
        if any(k in low for k in ["what is my name", "what was my name", "what's my name", "who am i", "mera naam kya hai", "do you remember my name"]):
            global_name = self.memory_manager.get_memory_value("user_name")
            if global_name:
                return f"Your name is {global_name}!" if "my name" in low or "who am i" in low else f"Aapka naam {global_name} hai bhai."

        # User Introduction (English & Hinglish)
        intro_match = re.search(r'\b(?:my name is|i am|call me|mera naam)\s+([a-zA-Z0-9]+)', low)
        if intro_match and not any(k in low for k in ["what is", "what's", "kya hai", "tell me", "who am i"]):
            user_name = intro_match.group(1).strip().capitalize()
            self.memory_manager.add_memory("user_name", user_name, f"User's name is {user_name}")
            if any(k in low for k in ["mera", "naam", "bhai", "hai"]):
                return f"Arre badhiya {user_name} bhai! Kaise ho? 😄"
            return f"Nice to meet you, {user_name}! 😄"

        # Built-in Handling for Attachments in Basic Mode
        if attachments:
            att_responses = []
            for att in attachments:
                att_name = att.get("filename", "file")
                att_cat = att.get("category", "text")
                att_size = att.get("size_formatted", "")
                att_id = att.get("id")

                if att_cat in ["text", "code", "document"]:
                    file_txt = self.attachment_manager.read_attachment_text(att_id, max_chars=1200)
                    line_count = len(file_txt.splitlines()) if file_txt else 0
                    preview_snip = file_txt[:350].strip() if file_txt else "Empty content"
                    att_responses.append(f"I've received and inspected **{att_name}** ({att_size}, {line_count} lines).\n\nContent preview:\n```{att.get('extension', '').lstrip('.')}\n{preview_snip}\n```")
                elif att_cat == "image":
                    att_responses.append(f"I received your image **{att_name}** ({att_size}). For visual object recognition and image understanding, connect a Gemini API key in Settings!")
            
            if att_responses:
                return "\n\n".join(att_responses)

        # Built-in conversational dialogue responses (short, natural, casual, and human-like)
        # 1. Greetings (English & Hinglish)
        if re.match(r'^(?:hello|hi|hey|greetings|yo|yo\s+bro|howdy|namaste|satsriakal|good\s+(?:morning|afternoon|evening|day))[\s!\.\?,]*$', low) or low in ["yo", "yo bro", "bhai", "bro", "hey", "hello"]:
            if any(k in low for k in ["namaste", "namaskar", "satsriakal"]):
                return "Namaste bhai! Kaise ho?"
            elif any(k in low for k in ["bhai"]):
                return "Yo bhai 😂 Kya scene hai?"
            elif "yo" in low:
                return "Yo! What's up? I'm running in basic mode right now because no AI provider is configured."
            return "Hello! How's it going? I'm in basic mode right now."

        # 2. Status inquiry / How are you / Kya haal hai / Kaisa hai
        if re.search(r'\bhow\s+are\s+you(?:\s+doing)?\b|\bhow(?:\'s|\s+is)\s+(?:it\s+going|everything|your\s+day|life)\b|\b(?:kya\s+haal|kya\s+haal\s+chal|kaise\s+ho|kaisa\s+hai)\b', low):
            if any(k in low for k in ["kya haal", "kaisa hai", "kaise ho", "bhai"]):
                return "Badhiya bhai 😄 Tu bata, kya scene hai?"
            return "I'm doing good! I'm in basic mode right now since no AI provider is connected."

        # 3. What are you doing / Bored / Kya kar rha hai / Bore ho raha hu / Kya scene hai
        if re.search(r'\bwhat\s+are\s+you\s+(?:doing|up\s+to)\b|\bwhat(?:\'s|\s+is)\s+up\b|\b(?:kya\s+karu|bore\s+ho\s+raha|kya\s+chal\s+raha|kya\s+kar\s+rha|kya\s+kar\s+raha|kya\s+scene\s+hai|kya\s+scene)\b', low):
            if any(k in low for k in ["kya kar", "bore", "kya karu"]):
                return "Bas ready hoon bhai 😂 Bol kya karna hai."
            return "Just chilling and ready! Bol kya scene hai?"

        # 4. Tell me a joke
        if re.search(r'\b(?:tell\s+me\s+a\s+joke|tell\s+a\s+joke|make\s+me\s+laugh|say\s+something\s+funny|joke)\b', low):
            return "Why did the computer keep freezing? Because it left its Windows open! 🪟😂"

        # 5. Gratitude / Compliments
        if re.search(r'^(?:thank\s+you|thanks|thx|awesome|great\s+job|perfect|nice|cool|good\s+job|shukriya|dhanyawad)[\s!\.\?]*$', low):
            if any(k in low for k in ["shukriya", "dhanyawad", "bhai"]):
                return "Arre koi na bhai! Anytime 😎"
            return "You're welcome! Anytime 😄"

        # 6. Identity / Introduction
        if re.search(r'\b(?:who\s+are\s+you|what\s+is\s+your\s+name|what\s+are\s+you|kaun\s+ho\s+tum)\b', low):
            if any(k in low for k in ["kaun ho", "tum", "tera"]):
                return "Main Zevion hoon — tera AI desktop copilot bhai! Apps khol, files bana, games bana, sab kuch kar sakta hoon. Bol kya karna hai?"
            return "I'm Zevion, your AI desktop copilot. I can open apps, create files and folders, build games, take screenshots, run web searches, and more — just tell me what to do!"

        # 7. Capabilities / What can you do
        if re.search(r'\b(?:what\s+can\s+you\s+do|kya\s+kar\s+sakte?\s+ho|your\s+features|capabilities|kaunse\s+kaam|what\s+are\s+your\s+features)\b', low):
            return ("Main ye sab kar sakta hoon bhai:\n"
                    "• Apps open/close (Chrome, Notepad, Discord...)\n"
                    "• Files & folders create/read/delete\n"
                    "• Games bana (Snake, Flappy Bird, 2048, Breakout...)\n"
                    "• Web search + file download\n"
                    "• Screenshot + screen analyze\n"
                    "• PC diagnostics, battery, reminders\n"
                    "• Clipboard, keyboard shortcuts, media control\n\n"
                    "Bas natural language me bolo!")

        # 8. Time / Date queries
        if re.search(r'\b(?:what\s+time|what\s+is\s+the\s+time|whats\s+the\s+time|current\s+time|kya\s+time\s+hua|time\s+kya\s+hai|kitne\s+baje)\b', low):
            import datetime as _dt
            now = _dt.datetime.now()
            return f"Abhi time hai **{now.strftime('%I:%M %p')}** ({now.strftime('%Y-%m-%d')})."

        # 9. Basic math evaluation
        m_math = re.search(r'^\s*(?:calculate|calc|what\s+is|kitna\s+hua|solve)?\s*\(?\s*(\d+(?:\.\d+)?)\s*([+\-*/×÷x])\s*(\d+(?:\.\d+)?)\s*\)?\s*\??\s*$', low)
        if m_math:
            try:
                a = float(m_math.group(1)); op = m_math.group(2); b = float(m_math.group(3))
                if op in ['+', 'plus']: result = a + b
                elif op in ['-', 'minus']: result = a - b
                elif op in ['*', 'x', '×', 'times']: result = a * b
                elif op in ['/', '÷']: result = a / b if b != 0 else float('inf')
                else: result = None
                if result is not None:
                    r = int(result) if float(result).is_integer() else round(result, 4)
                    return f"Answer: **{r}**"
            except Exception:
                pass

        return None

    def _split_into_clauses(self, text: str) -> List[str]:
        raw = text.strip()
        # Match English and Hinglish/Hindi connectors: and then, followed by, after that, then, and, aur fir, phir, fir, aur, commas, semicolons, ke baad
        parts = re.split(r'\s*(?:,\s*(?:and\s+then|followed\s+by|after\s+that|aur\s+(?:fir|phir)|then|and|phir|fir|aur|ke\s+baad)?|;\s*|\s+(?:and\s+then|followed\s+by|after\s+that|aur\s+(?:fir|phir)|then|and|phir|fir|aur|ke\s+baad))\s+', raw, flags=re.IGNORECASE)
        cleaned = [p.strip() for p in parts if p.strip()]
        return cleaned

    def _parse_single_clause(self, clause_text: str, context: Dict[str, Any], workspace: str) -> Optional[Dict[str, Any]]:
        raw = clause_text.strip()
        low = raw.lower().strip()

        # 0. Claude Code-style tools (priority: real web search, fetch, grep, edit)
        # These run BEFORE the browser-based "search for X" so explicit requests return
        # actual results/content instead of just opening a browser tab.

        # A. Web Search (return real search results as text)
        if re.search(r'\b(?:web\s+search|search\s+the\s+web|search\s+web|google\s+search|search\s+on\s+google|search\s+internet)\b', low):
            m_ws = re.search(r'(?:search\s+(?:the\s+)?(?:web|internet)|web\s+search|google\s+search|search\s+on\s+google)\s+(?:for\s+|about\s+|:)?\s*(.+)$', raw, re.IGNORECASE)
            if m_ws:
                query = m_ws.group(1).strip().strip('"\'.')
                if query:
                    return {
                        "action": {
                            "tool": "web_search",
                            "parameters": {"query": query},
                            "description": f"Search the web for '{query}'",
                            "status": "pending"
                        },
                        "summary": f"web search '{query}'",
                        "safety_level": "safe"
                    }

        # B. Web Fetch (retrieve content of a URL)
        if re.search(r'\b(?:fetch|scrape|summarize|read\s+(?:this|the)\s+(?:url|page|website|site|link))\b', low):
            m_wf = re.search(r'(https?://\S+|www\.\S+)\b', raw, re.IGNORECASE)
            if m_wf:
                url = m_wf.group(1).rstrip('.,;')
                if url.lower().startswith("www."):
                    url = "https://" + url
                return {
                    "action": {
                        "tool": "web_fetch",
                        "parameters": {"url": url},
                        "description": f"Fetch content from {url}",
                        "status": "pending"
                    },
                    "summary": f"fetch {url}",
                    "safety_level": "safe"
                }

        # B2. Download a file from a URL
        if re.search(r'\b(?:download|save\s+file|download\s+file|daanlod|download\s+kar)\b', low):
            m_dl = re.search(r'(https?://\S+|www\.\S+)\b', raw, re.IGNORECASE)
            if m_dl:
                url = m_dl.group(1).rstrip('.,;')
                if url.lower().startswith("www."):
                    url = "https://" + url
                return {
                    "action": {
                        "tool": "download_file",
                        "parameters": {"url": url},
                        "description": f"Download file from {url}",
                        "status": "pending"
                    },
                    "summary": f"download {url}",
                    "safety_level": "safe"
                }

        # C. Grep / Search inside file contents
        if re.search(r'\b(?:grep|search\s+(?:inside|within|in)\s+(?:the\s+)?(?:files?|folders?|directory|code|content))\b', low) or low.startswith("grep "):
            m_gr = re.search(r'(?:grep|search\s+(?:inside|within|in)\s+(?:the\s+)?(?:files?|folders?|directory|code|content))\s+(?:for\s+)?["\']?(.+?)["\']?(?:\s+(?:in|inside|within)\s+(?:the\s+|my\s+)?(desktop|downloads|documents|projects|workspace))?\s*$', raw, re.IGNORECASE)
            if m_gr:
                pattern = m_gr.group(1).strip().strip('"\'')
                directory = m_gr.group(2).capitalize() if m_gr.group(2) else None
                if pattern:
                    return {
                        "action": {
                            "tool": "grep_files",
                            "parameters": {"pattern": pattern, "directory": directory},
                            "description": f"Search file contents for '{pattern}'",
                            "status": "pending"
                        },
                        "summary": f"grep for '{pattern}'",
                        "safety_level": "safe"
                    }

        # D. Edit File (find & replace in existing file)
        m_edit = re.search(r'^(?:edit|modify|update|change)\s+(?:the\s+)?(?:file\s+)?([^\s]+?)\s+(?:replace|change|update|set|:)\s+["\']?(.+?)["\']?\s+(?:with|to|into)\s+["\']?(.+?)["\']?$', raw, re.IGNORECASE)
        if m_edit and not re.search(r'\b(?:open|launch|khol|create|bana)\b', low):
            file_path = m_edit.group(1).strip()
            old_text = m_edit.group(2).strip().strip('"\'')
            new_text = m_edit.group(3).strip().strip('"\'')
            if file_path and old_text:
                return {
                    "action": {
                        "tool": "edit_file",
                        "parameters": {"path": file_path, "old_text": old_text, "new_text": new_text},
                        "description": f"Edit {file_path}: replace '{old_text}' with '{new_text}'",
                        "status": "pending"
                    },
                    "summary": f"edit {file_path}",
                    "safety_level": "moderate"
                }

        # E. Undo last edit
        if low in ["undo", "undo edit", "undo last edit", "undo kar", "undo karo", "wapas kar", "undo the edit", "revert", "revert last edit", "last edit wapas kar", "last edit undo kar"]:
            return {
                "action": {
                    "tool": "undo_edit",
                    "parameters": {},
                    "description": "Undo the last file edit",
                    "status": "pending"
                },
                "summary": "undo last edit",
                "safety_level": "moderate"
            }

        # F. Set a timed reminder (scheduled task lite)
        m_remind = re.search(r'(?:remind\s+me|yaad\s+(?:dilana|dila|rakhna|rakh)|reminder|remember|yaad\s+dilao)\s+(?:in\s+|about\s+)?(?:(\d+)\s*(?:minutes?|mins?|seconds?|secs?|hours?)\s*(?:me|mein|ke\s+baad|baad\s+me|from\s+now)?\s*(?:to\s+|about\s+|ki\s+|:)?\s*)?(.+)$', raw, re.IGNORECASE)
        if m_remind and m_remind.group(2):
            text = m_remind.group(2).strip().strip('"\'')
            # Strip a leading "to" from "remind me to X"
            if text.lower().startswith("to "):
                text = text[3:].strip()
            minutes = 5.0
            if m_remind.group(1):
                num = int(m_remind.group(1))
                # detect unit
                unit_match = re.search(r'(second|sec|minute|min|hour)', low)
                if unit_match:
                    unit = unit_match.group(1)
                    if unit.startswith("sec"):
                        minutes = num / 60.0
                    elif unit.startswith("hour"):
                        minutes = num * 60.0
                    else:
                        minutes = float(num)
            return {
                "action": {
                    "tool": "set_reminder",
                    "parameters": {"text": text, "minutes": minutes},
                    "description": f"Set reminder: '{text}' in {minutes} min",
                    "status": "pending"
                },
                "summary": f"set reminder '{text[:40]}'",
                "safety_level": "safe"
            }

        famous_sites = {
            "youtube": "https://www.youtube.com",
            "google": "https://www.google.com",
            "github": "https://github.com",
            "reddit": "https://www.reddit.com",
            "twitter": "https://x.com",
            "x": "https://x.com",
            "wikipedia": "https://www.wikipedia.org",
            "facebook": "https://www.facebook.com",
            "instagram": "https://www.instagram.com",
            "linkedin": "https://www.linkedin.com",
            "netflix": "https://www.netflix.com",
            "amazon": "https://www.amazon.com",
            "chatgpt": "https://chatgpt.com",
            "openai": "https://openai.com",
            "bing": "https://www.bing.com",
            "duckduckgo": "https://duckduckgo.com"
        }

        # 0A. Game & Project Creation (English & Hinglish)
        # Handles default HTML/CSS/JS web games and explicit Python games.
        # Supports existing-folder targeting (e.g. TestAgent folder ke andar snake game bana de, TestAgent wale folder mein Snake Game bana de)
        # and direct-file placement (e.g. TestAgent folder mein directly files bana de).
        is_explicit_python = bool(re.search(r'\b(?:python|pygame|tkinter|\.py)\b', low))
        lang = "python" if is_explicit_python else "html"
        is_direct = bool(re.search(r'\b(?:directly|direct|seedha|bina\s+extra\s+folder\s+ke|bina\s+folder\s+ke|direct\s+files)\b', low))
        clean_raw = re.sub(r'^(?:bhai\s+|please\s+|plz\s+|bro\s+|kripya\s+)', '', raw, flags=re.IGNORECASE).strip()

        reserved_words = {'desktop', 'workspace', 'my', 'the', 'ek', 'a', 'an', 'snake', 'game', 'python', 'pygame', 'tictactoe', 'arcade', 'khel', 'new', 'mere', 'par', 'pe', 'mein', 'me', 'ke', 'andar', 'wale', 'wali', 'directly', 'direct', 'files', 'flappy', 'bird', '2048', 'breakout', 'brick', 'memory', 'match', 'card', 'block'}

        # Parent folder detection
        parent_folder = None
        m_parent = re.search(r'(?:(?:desktop|workspace)?\s*(?:ke|par|pe)?\s*)?([a-zA-Z0-9_\-]+)\s+(?:wale\s+folder\s+mein|folder\s+(?:ke\s+andar|mein|me)|dir\s+(?:ke\s+andar|mein|me)|directory\s+(?:ke\s+andar|mein|me))', clean_raw, re.IGNORECASE)
        if not m_parent:
            m_parent = re.search(r'(?:(?:desktop|workspace)?\s*(?:ke|par|pe)?\s*)?([a-zA-Z0-9_\-]+)\s+(?:ke\s+andar|wale\s+folder\s+mein)', clean_raw, re.IGNORECASE)
        if not m_parent:
            m_parent = re.search(r'(?:inside|in|within)\s+(?:the\s+)?(?:folder\s+)?([a-zA-Z0-9_\-]+)(?:\s+folder)?', clean_raw, re.IGNORECASE)

        if m_parent:
            p_cand = m_parent.group(1).strip()
            if p_cand.lower() not in reserved_words:
                parent_folder = p_cand

        m_game = re.search(r'^(?:bhai\s+|please\s+|plz\s+|bro\s+|kripya\s+)?(?:mere\s+desktop\s+par\s+|desktop\s+pe\s+|desktop\s+par\s+)?(?:create|make|build|bana\s+de|bana\s+do|banao|bana)\s+(?:a\s+|an\s+|ek\s+)?(?:new\s+)?([a-zA-Z0-9_\-\s]+?)\s*(?:game|khel)(?:\s+(?:in|using)\s+([a-zA-Z0-9]+))?(?:\s+(?:on|in|pe|par)\s+(?:my\s+)?(?:desktop|workspace))?$', raw, re.IGNORECASE)
        if not m_game:
            # Suffix verb form: "bhai ek snake game bana de", "ek game bana do"
            m_game = re.search(r'^(?:bhai\s+|please\s+|plz\s+|bro\s+|kripya\s+)?(?:mere\s+desktop\s+par\s+|desktop\s+pe\s+|desktop\s+par\s+)?(?:a\s+|an\s+|ek\s+)?(?:new\s+)?([a-zA-Z0-9_\-\s]+?)\s*(?:game|khel)(?:\s+(?:in|using)\s+([a-zA-Z0-9]+))?(?:\s+(?:on|in|pe|par)\s+(?:my\s+)?(?:desktop|workspace))?\s+(?:bana\s+de|bana\s+do|banao|bana|create\s+kar|create\s+karo|build)$', raw, re.IGNORECASE)
        if not m_game and is_explicit_python:
            m_game = re.search(r'^(?:bhai\s+|please\s+)?(?:make\s+(?:it\s+)?in\s+python|pygame\s+(?:mein|me)\s+(?:bana|banao|bana\s+de|bana\s+do)|python\s+game\s+bana(?:o| de| do)?)$', raw, re.IGNORECASE)
        if not m_game and any(k in low for k in ["snake game", "tic tac toe", "tictactoe", "arcade game", "snake game bana", "game bana", "game banao", "game bana de", "game bana do", "ek game", "files bana"]):
            if any(verb in low for verb in ["create", "make", "bana", "banao", "build", "play", "bana de", "bana do"]):
                m_game = re.search(r'^(?:bhai\s+|please\s+|plz\s+|bro\s+|kripya\s+)?(?:mere\s+desktop\s+par\s+|desktop\s+pe\s+|desktop\s+par\s+)?(?:create|make|build|bana|banao|bana\s+de|bana\s+do)\s+(?:a\s+|an\s+|ek\s+)?(?:new\s+)?([a-zA-Z0-9_\-\s]+)$', raw, re.IGNORECASE)

        if m_game or any(k in low for k in ["snake game", "tic tac toe", "tictactoe", "create game", "game bana", "game banao", "game bana de", "game bana do", "files bana"]):
            g_str = m_game.group(1).lower().strip() if (m_game and hasattr(m_game, 'group') and m_game.lastindex and m_game.lastindex >= 1 and m_game.group(1)) else low
            if m_game and hasattr(m_game, 'lastindex') and m_game.lastindex and m_game.lastindex >= 2 and m_game.group(2):
                specified_lang = m_game.group(2).lower().strip()
                if specified_lang in ["python", "py", "pygame", "tkinter"]:
                    lang = "python"

            if "snake" in g_str or "snake" in low:
                proj_name = "SnakeGame"
                game_type = "snake"
            elif "tic" in g_str or "toe" in g_str or "tictactoe" in low:
                proj_name = "TicTacToe"
                game_type = "tictactoe"
            elif "flappy" in g_str or "flappy" in low or "bird" in g_str:
                proj_name = "FlappyBird"
                game_type = "flappy"
            elif "2048" in g_str or "2048" in low or "twenty" in low:
                proj_name = "Game2048"
                game_type = "2048"
            elif "breakout" in g_str or "breakout" in low or "brick" in low or "block" in low:
                proj_name = "Breakout"
                game_type = "breakout"
            elif "memory" in g_str or "memory" in low or "match" in low or "card" in low:
                proj_name = "MemoryMatch"
                game_type = "memory"
            else:
                proj_name = "ArcadeGame"
                game_type = "arcade"

            # Check if an explicit subfolder was requested e.g. "SnakeGame folder bana ke"
            m_sub = re.search(r'([a-zA-Z0-9_\-]+)\s+folder\s+bana\s+(?:ke|kar)', clean_raw, re.IGNORECASE)
            if m_sub:
                s_cand = m_sub.group(1).strip()
                if s_cand.lower() not in reserved_words:
                    proj_name = s_cand

            # Folder & Target Dir Resolution
            if is_direct:
                target_dir = f"Desktop/{parent_folder}" if parent_folder else "Desktop"
                final_proj_name = "" # direct files into parent folder
            elif parent_folder:
                target_dir = f"Desktop/{parent_folder}"
                final_proj_name = proj_name
            else:
                target_dir = "Desktop"
                final_proj_name = proj_name

            files_dict = get_game_template(game_type, lang)

            return {
                "action": {
                    "tool": "create_project",
                    "parameters": {
                        "project_name": final_proj_name,
                        "target_dir": target_dir,
                        "files": files_dict
                    },
                    "description": f"Create and physically verify {final_proj_name or game_type.title() + ' files'} in {target_dir}",
                    "status": "pending"
                },
                "summary": f"create {final_proj_name or game_type.title()} project in {target_dir}",
                "safety_level": "moderate"
            }

        # 0B. File Content Writing / Updating (English & Hinglish)
        # E.g. "hello.txt mein Hello from Zevion likh de", "write Hello in hello.txt", "Desktop par TestAgent folder ke andar hello.txt mein Hello likh de"
        is_desk_loc = bool(re.search(r'\b(?:on\s+(?:my\s+)?desktop|in\s+(?:my\s+)?desktop|desktop\s+(?:par|pe|me|mein|par\s+se)|mere\s+desktop)\b', low))

        # Form 1: <file> mein/me/ke andar likh/likh de <content>
        m_fw_verb_first = re.search(r'^(?:bhai\s+|please\s+|plz\s+)?(?:mere\s+desktop\s+par\s+|desktop\s+pe\s+|desktop\s+par\s+)?(?:([a-zA-Z0-9_\-]+)\s+folder\s+(?:ke\s+andar|mein|me)\s+)?["\']?([a-zA-Z0-9_\-\.\/\\]+\.[a-zA-Z0-9]+)["\']?\s+(?:mein|me|ke\s+andar|pe|par)\s+(?:likh\s+de|likh\s+do|likho|likh|write\s+kar\s+de|write\s+kar\s+do|write\s+kar|write\s+karo|daal\s+de|daal\s+do|daalo|daal|save\s+kar\s+do|save\s+kar)\s+["\']?(.+?)["\']?$', raw, re.IGNORECASE)
        if m_fw_verb_first:
            folder = m_fw_verb_first.group(1)
            filename = m_fw_verb_first.group(2).strip('\"\' ')
            content = m_fw_verb_first.group(3).strip('\"\' ')
            if folder:
                path = f"Desktop/{folder}/{filename}" if is_desk_loc or not folder.startswith("Desktop") else f"{folder}/{filename}"
            else:
                path = f"Desktop/{filename}" if is_desk_loc and not "/" in filename and not "\\" in filename else filename
            return {
                "action": {
                    "tool": "create_file",
                    "parameters": {"path": path, "content": content},
                    "description": f"Write content into '{path}'",
                    "status": "pending"
                },
                "summary": f"write to {path}",
                "safety_level": "moderate"
            }

        # Form 2: <file> mein/me/ke andar <content> likh/likh de
        m_fw_content_first = re.search(r'^(?:bhai\s+|please\s+|plz\s+)?(?:mere\s+desktop\s+par\s+|desktop\s+pe\s+|desktop\s+par\s+)?(?:([a-zA-Z0-9_\-]+)\s+folder\s+(?:ke\s+andar|mein|me)\s+)?["\']?([a-zA-Z0-9_\-\.\/\\]+\.[a-zA-Z0-9]+)["\']?\s+(?:mein|me|ke\s+andar|pe|par)\s+["\']?(.+?)["\']?\s+(?:likh\s+de|likh\s+do|likho|likh|write\s+kar\s+de|write\s+kar\s+do|write\s+kar|write\s+karo|daal\s+de|daal\s+do|daalo|daal|save\s+kar\s+do|save\s+kar)$', raw, re.IGNORECASE)
        if m_fw_content_first:
            folder = m_fw_content_first.group(1)
            filename = m_fw_content_first.group(2).strip('\"\' ')
            content = m_fw_content_first.group(3).strip('\"\' ')
            if folder:
                path = f"Desktop/{folder}/{filename}" if is_desk_loc or not folder.startswith("Desktop") else f"{folder}/{filename}"
            else:
                path = f"Desktop/{filename}" if is_desk_loc and not "/" in filename and not "\\" in filename else filename
            return {
                "action": {
                    "tool": "create_file",
                    "parameters": {"path": path, "content": content},
                    "description": f"Write content into '{path}'",
                    "status": "pending"
                },
                "summary": f"write to {path}",
                "safety_level": "moderate"
            }

        # Form 3: write <content> in/into/to <file>
        m_fw_eng_c = re.search(r'^(?:bhai\s+|please\s+|plz\s+)?(?:write|put|insert|add|save)\s+["\']?(.+?)["\']?\s+(?:in|into|to|inside)\s+(?:the\s+file\s+)?["\']?([a-zA-Z0-9_\-\.\/\\]+\.[a-zA-Z0-9]+)["\']?(?:\s+(?:on|in)\s+(?:my\s+)?desktop)?$', raw, re.IGNORECASE)
        if m_fw_eng_c:
            content = m_fw_eng_c.group(1).strip('\"\' ')
            filename = m_fw_eng_c.group(2).strip('\"\' ')
            path = f"Desktop/{filename}" if is_desk_loc and not "/" in filename and not "\\" in filename and not filename.startswith("Desktop") else filename
            return {
                "action": {
                    "tool": "create_file",
                    "parameters": {"path": path, "content": content},
                    "description": f"Write content into '{path}'",
                    "status": "pending"
                },
                "summary": f"write to {path}",
                "safety_level": "moderate"
            }

        # Form 4: in/inside <file> write <content>
        m_fw_eng_d = re.search(r'^(?:in|inside)\s+(?:the\s+file\s+)?["\']?([a-zA-Z0-9_\-\.\/\\]+\.[a-zA-Z0-9]+)["\']?\s+(?:write|put|insert|add|save)\s+["\']?(.+?)["\']?$', raw, re.IGNORECASE)
        if m_fw_eng_d:
            filename = m_fw_eng_d.group(1).strip('\"\' ')
            content = m_fw_eng_d.group(2).strip('\"\' ')
            return {
                "action": {
                    "tool": "create_file",
                    "parameters": {"path": filename, "content": content},
                    "description": f"Write content into '{filename}'",
                    "status": "pending"
                },
                "summary": f"write to {filename}",
                "safety_level": "moderate"
            }

        # 1. Typing / Writing into an application (English & Hinglish: type, write, likh, likh de, likho, isme likh, iske andar likh)
        if not any(k in low for k in [".txt", ".py", ".json", ".html", ".css", ".js", ".csv", ".md", ".sh", ".bat", " mein ", " me ", " ke andar ", "folder", "directory"]):
            m_type = re.search(r'^(?:type|write|input|put|likh|likho|likh\s+de)\s+(?:["\']?(.+?)["\']?)(?:\s+(?:in|into|on|to|pe|par|me|mein)\s+(?:the\s+)?([a-zA-Z0-9_\-\.]+))?$', raw, re.IGNORECASE)
            if not m_type:
                # Suffix form: "hello brother likh de", "hello likh", "hello type kar"
                m_type_suffix = re.search(r'^["\']?(.+?)["\']?\s+(?:likh\s+de|likho|likh|type\s+kar|type\s+karo)$', raw, re.IGNORECASE)
                if m_type_suffix:
                    text_val = m_type_suffix.group(1).strip('"\' ')
                    target_app = context.get("last_app", "notepad")
                    return {
                        "action": {
                            "tool": "type_text",
                            "parameters": {"text": text_val, "target_app": target_app},
                            "description": f"Type text '{text_val}' into {target_app}",
                            "status": "pending"
                        },
                        "summary": f"type \"{text_val}\" into {target_app}",
                        "safety_level": "safe"
                    }

            # Contextual typing: "iske andar hello likh", "isme hello likh", "isme test type kar"
            m_type_context = re.search(r'^(?:iske\s+andar|isme|ismein|in\s+this|in\s+it)\s+["\']?(.+?)["\']?\s+(?:likh|likho|likh\s+de|type\s+kar|type\s+karo|type)$', raw, re.IGNORECASE)
            if m_type_context:
                text_val = m_type_context.group(1).strip('"\' ')
                target_app = context.get("last_app", "notepad")
                return {
                    "action": {
                        "tool": "type_text",
                        "parameters": {"text": text_val, "target_app": target_app},
                        "description": f"Type text '{text_val}' into {target_app}",
                        "status": "pending"
                    },
                    "summary": f"type \"{text_val}\" into {target_app}",
                    "safety_level": "safe"
                }

            if m_type and not any(k in low for k in ["file", "folder", "directory", "dir"]):
                text_to_type = m_type.group(1).strip('"\' ')
                target_specified = m_type.group(2)
                target_app = target_specified.lower().strip() if target_specified else context.get("last_app", "notepad")
                return {
                    "action": {
                        "tool": "type_text",
                        "parameters": {"text": text_to_type, "target_app": target_app},
                        "description": f"Type text '{text_to_type}' into {target_app}",
                        "status": "pending"
                    },
                    "summary": f"type \"{text_to_type}\" into {target_app}",
                    "safety_level": "safe"
                }

        # 2. YouTube Shorts Resolution (English & Hinglish)
        # E.g. "shorts chala de", "shorts chala", "youtube shorts", "youtube shorts open kar", "open shorts"
        m_generic_shorts = re.search(r'^(?:shorts\s+(?:chala|chalao|chala\s+de|khol|kholo|play|open)|(?:open|play|watch|launch)\s+(?:the\s+)?(?:youtube\s+)?shorts|youtube\s+shorts|shorts)$', low)
        if m_generic_shorts:
            return {
                "action": {
                    "tool": "open_website",
                    "parameters": {
                        "url": "https://www.youtube.com/shorts",
                        "search_query": "YouTube Shorts",
                        "playback": True,
                        "play_first": False,
                        "is_shorts": True
                    },
                    "description": "Open YouTube Shorts feed in Google Chrome",
                    "status": "pending"
                },
                "summary": "open YouTube Shorts",
                "safety_level": "safe"
            }

        # E.g. "bhai YouTube pe koi Minecraft short laga de", "Minecraft ki shorts chala", "latest Minecraft short laga", "bhai ek Minecraft short chala de"
        m_specific_shorts = re.search(r'^(?:bhai\s+)?(?:youtube\s+(?:pe|par)\s+)?(?:koi\s+|ek\s+)?(?:latest\s+|newest\s+)?(.+?)\s+(?:ki\s+)?shorts?\s+(?:chala|chalao|chala\s+de|laga|laga\s+de|play|khol|kholo|dikhaye|dekho|search)(?:\s+de)?$', raw, re.IGNORECASE)
        if not m_specific_shorts:
            m_specific_shorts = re.search(r'^(?:play|watch|find)\s+(.+?)\s+shorts(?:\s+(?:on|in)\s+youtube)?$', raw, re.IGNORECASE)
        if not m_specific_shorts:
            m_specific_shorts = re.search(r'^(?:latest\s+|newest\s+)?(.+?)\s+shorts?\s+(?:laga|chala|play|open)(?:\s+de)?$', raw, re.IGNORECASE)

        if m_specific_shorts:
            raw_q = m_specific_shorts.group(1).strip()
            # Clean modifier words
            clean_q = re.sub(r'^(?:the|a|an|koi|ek|bhai)\s+', '', raw_q, flags=re.IGNORECASE).strip()
            if clean_q and clean_q.lower() not in ["youtube", "yt"]:
                encoded = urllib.parse.quote_plus(f"{clean_q} shorts")
                url = f"https://www.youtube.com/results?search_query={encoded}"
                return {
                    "action": {
                        "tool": "open_website",
                        "parameters": {
                            "url": url,
                            "search_query": f"{clean_q} shorts",
                            "playback": True,
                            "play_first": True,
                            "is_shorts": True
                        },
                        "description": f"Play {clean_q.title()} Shorts on YouTube",
                        "status": "pending"
                    },
                    "summary": f"play {clean_q.title()} Shorts on YouTube",
                    "safety_level": "safe"
                }

        # 3. Latest Creator Video on YouTube
        m_latest = re.search(r'^(?:play|watch|find|view)\s+(?:the\s+)?(?:latest|newest|recent)\s+(?:video\s+(?:from|by|of)\s+|upload\s+(?:from|by|of)\s+)?([a-zA-Z0-9\s_\-\'\.]+?)(?:\'s)?\s+(?:latest\s+|newest\s+|recent\s+)?(?:video|upload|episode)?(?:\s+(?:on|in)\s+youtube)?(?:\s+and\s+play\s+it)?$', raw, re.IGNORECASE)
        if not m_latest:
            m_latest = re.search(r'^(?:play|watch|find)\s+([a-zA-Z0-9\s_\-\'\.]+?)(?:\'s)?\s+(?:latest|newest|recent)\s+(?:video|upload)?(?:\s+(?:on|in)\s+youtube)?(?:\s+and\s+play\s+it)?$', raw, re.IGNORECASE)

        if m_latest:
            creator = m_latest.group(1).strip("'\"")
            creator = re.sub(r'^(?:the|a)\s+', '', creator, flags=re.IGNORECASE).strip()
            creator_display = "MrBeast" if creator.lower() == "mrbeast" else creator.title()
            encoded = urllib.parse.quote_plus(f"{creator} latest")
            url = f"https://www.youtube.com/results?search_query={encoded}&sp=CAISAhAB"
            return {
                "action": {
                    "tool": "open_website",
                    "parameters": {
                        "url": url,
                        "search_query": f"{creator} latest",
                        "playback": True,
                        "filter_latest": True,
                        "channel": creator
                    },
                    "description": f"Find and play newest video from {creator_display} on YouTube",
                    "status": "pending"
                },
                "summary": f"play newest {creator_display} video on YouTube",
                "safety_level": "safe"
            }

        # 4. Search YouTube & Play First Result (explicit composite clause)
        m_search_play = re.search(r'^(?:search\s+(?:yt|youtube)\s+for\s+(.+?)(?:\s+and\s+play(?:\s+the\s+first\s+result|\s+it)?|\s+and\s+watch\s+it))$', raw, re.IGNORECASE)
        if m_search_play:
            query = m_search_play.group(1).strip()
            encoded = urllib.parse.quote_plus(query)
            url = f"https://www.youtube.com/results?search_query={encoded}"
            return {
                "action": {
                    "tool": "open_website",
                    "parameters": {
                        "url": url,
                        "search_query": query,
                        "playback": True,
                        "play_first": True
                    },
                    "description": f"Search YouTube for '{query}' and play first result",
                    "status": "pending"
                },
                "summary": f"play first result for {query} on YouTube",
                "safety_level": "safe"
            }

        # 5. Play First Video on YouTube
        m_first = re.search(r'^(?:play|watch)\s+the\s+first\s+(.+?)(?:\s+(?:video)?(?:\s+(?:on|in)\s+youtube))?$', raw, re.IGNORECASE)
        if m_first:
            query = m_first.group(1).strip()
            encoded = urllib.parse.quote_plus(query)
            url = f"https://www.youtube.com/results?search_query={encoded}"
            return {
                "action": {
                    "tool": "open_website",
                    "parameters": {
                        "url": url,
                        "search_query": query,
                        "playback": True,
                        "play_first": True
                    },
                    "description": f"Play first video for '{query}' on YouTube",
                    "status": "pending"
                },
                "summary": f"play first {query} video",
                "safety_level": "safe"
            }

        # 6. Play / Watch Video on YouTube (English & Hinglish: "bhai Minecraft ki videos chala", "Minecraft ki video chala", "YouTube pe Minecraft chala de", "play Minecraft survival")
        m_play = re.search(r'^(?:bhai\s+)?(?:play|watch|chala|chalao|chala\s+de|laga|laga\s+de)\s+(?:the\s+)?(.+?)(?:\s+(?:on|in|pe|par)\s+youtube)?$', raw, re.IGNORECASE)
        if not m_play:
            # Hinglish: "Minecraft ki video chala", "Minecraft video play kar", "bhai Minecraft ki videos chala"
            m_play = re.search(r'^(?:bhai\s+)?(.+?)\s+(?:ki\s+)?(?:videos?|video)\s+(?:chala|chalao|chala\s+de|play\s+kar|laga|laga\s+de)(?:\s+de)?$', raw, re.IGNORECASE)
        if not m_play:
            # Hinglish: "YouTube pe Minecraft play kar"
            m_play = re.search(r'^(?:(?:on|in|pe|par)\s+)?youtube\s+(?:pe|par|me|mein)?\s*(.+?)\s+(?:play|chala|search)\s*(?:kar|karo|de)?$', raw, re.IGNORECASE)

        if m_play and not any(kw in low for kw in ["game", "program", "music", "audio", "with", "latest", "newest", "short", "shorts"]):
            raw_q = m_play.group(1).strip()
            raw_q = re.sub(r'\b(?:video|videos|ki|ke|bhai)\b', '', raw_q, flags=re.IGNORECASE).strip()
            if len(raw_q) >= 2:
                encoded = urllib.parse.quote_plus(raw_q)
                url = f"https://www.youtube.com/results?search_query={encoded}"
                return {
                    "action": {
                        "tool": "open_website",
                        "parameters": {
                            "url": url,
                            "search_query": raw_q,
                            "playback": True,
                            "play_first": True
                        },
                        "description": f"Play video '{raw_q}' on YouTube",
                        "status": "pending"
                    },
                    "summary": f"play \"{raw_q}\" on YouTube",
                    "safety_level": "safe"
                }

        # 7. Search YouTube explicitly (English & Hinglish)
        m_yt_search = re.search(r'^(?:search\s+(?:yt|youtube)\s+for\s+(.+)|search\s+for\s+(.+?)\s+(?:on|in|pe|par)\s+youtube|search\s+(?:yt|youtube)\s+(.+)|youtube\s+(?:pe|par)\s+(.+?)\s+search\s*(?:kar|karo|de)?)$', raw, re.IGNORECASE)
        if m_yt_search:
            query = (m_yt_search.group(1) or m_yt_search.group(2) or m_yt_search.group(3) or m_yt_search.group(4) or "").strip()
            if query:
                encoded = urllib.parse.quote_plus(query)
                url = f"https://www.youtube.com/results?search_query={encoded}"
                return {
                    "action": {
                        "tool": "open_website",
                        "parameters": {
                            "url": url,
                            "search_query": query,
                            "playback": False
                        },
                        "description": f"Search YouTube for '{query}'",
                        "status": "pending"
                    },
                    "summary": f"search YouTube for \"{query}\"",
                    "safety_level": "safe"
                }

        # 8. Open YouTube Homepage / Bare YouTube (English & Hinglish: "youtube khol", "youtube laga", "open youtube")
        if re.match(r'^(?:open|launch|visit|go\s+to|khol|kholo|khol\s+de|laga|laga\s+de)\s+(?:the\s+)?(?:yt|youtube)$', low) or low in ["open yt", "open youtube", "yt", "youtube", "youtube khol", "youtube khol de", "youtube kholo", "youtube laga", "youtube laga de"]:
            return {
                "action": {
                    "tool": "open_website",
                    "parameters": {
                        "url": "https://www.youtube.com",
                        "search_query": "",
                        "playback": False
                    },
                    "description": "Open YouTube homepage in Google Chrome",
                    "status": "pending"
                },
                "summary": "open YouTube",
                "safety_level": "safe"
            }

        # 9. Web Search (Google or Contextual YouTube Search)
        # E.g. "open the browser and search for Minecraft", "search for Minecraft", "search the web for AI"
        m_web = re.search(r'^(?:(?:open\s+(?:the\s+)?(?:browser|web\s+browser|chrome)\s+and\s+)?(?:search\s+(?:the\s+)?web(?:\s+for)?|search\s+(?:google|bing|duckduckgo)?\s*(?:for\s+)?|lookup|look\s+up|search\s+for|search)\s+["\']?([^"\']+)["\']?)$', raw, re.IGNORECASE)
        if not m_web:
            # Suffix search form: "Minecraft search kar", "Minecraft search karo", "Minecraft search", "Minecraft dhoondh", "Minecraft dhoondo"
            m_web = re.search(r'^["\']?([^"\']+)["\']?\s+(?:search\s*(?:kar|karo|de|do)?|dhoondh|dhoondo)$', raw, re.IGNORECASE)
        if m_web:
            query = m_web.group(1).strip()
            if query and query.lower() not in ["something", "the web", "web"]:
                encoded = urllib.parse.quote_plus(query)
                if context.get("last_site") == "youtube" or "youtube" in query.lower():
                    clean_q = re.sub(r'\s+(?:on|in|pe|par)\s+youtube.*$', '', query, flags=re.IGNORECASE).strip()
                    encoded_yt = urllib.parse.quote_plus(clean_q)
                    return {
                        "action": {
                            "tool": "open_website",
                            "parameters": {
                                "url": f"https://www.youtube.com/results?search_query={encoded_yt}",
                                "search_query": clean_q,
                                "playback": False
                            },
                            "description": f"Search YouTube for '{clean_q}'",
                            "status": "pending"
                        },
                        "summary": f"search YouTube for \"{clean_q}\"",
                        "safety_level": "safe"
                    }
                else:
                    return {
                        "action": {
                            "tool": "open_website",
                            "parameters": {
                                "url": f"https://www.google.com/search?q={encoded}",
                                "search_query": query,
                                "playback": False
                            },
                            "description": f"Search Google for '{query}'",
                            "status": "pending"
                        },
                        "summary": f"search for \"{query}\"",
                        "safety_level": "safe"
                    }

        # Contextual search: "ab isme Minecraft search kar", "isme Minecraft dhoondh"
        m_context_search = re.search(r'^(?:ab\s+)?(?:isme|ismein|in\s+this|on\s+this)\s+(.+?)\s+search\s*(?:kar|karo|de)?$', raw, re.IGNORECASE)
        if m_context_search:
            q_val = m_context_search.group(1).strip()
            encoded = urllib.parse.quote_plus(q_val)
            url_target = f"https://www.youtube.com/results?search_query={encoded}" if context.get("last_site") == "youtube" else f"https://www.google.com/search?q={encoded}"
            return {
                "action": {
                    "tool": "open_website",
                    "parameters": {"url": url_target, "search_query": q_val, "playback": False},
                    "description": f"Search for '{q_val}'",
                    "status": "pending"
                },
                "summary": f"search for \"{q_val}\"",
                "safety_level": "safe"
            }

        # 10. Open Website in Specific Browser
        open_site_in_browser = re.search(
            r'^(?:open|launch|visit|go\s+to|khol|kholo)\s+(?:the\s+)?([a-zA-Z0-9\-\.\/:]+)\s+(?:in|on|using|with|pe|me)\s+(?:chrome|google\s+chrome|browser|web\s+browser|edge|firefox)$',
            low
        )
        if open_site_in_browser:
            site_target = open_site_in_browser.group(1).lower().strip()
            if site_target in famous_sites:
                target_url = famous_sites[site_target]
            elif site_target.startswith("http://") or site_target.startswith("https://"):
                target_url = site_target
            elif "." in site_target:
                target_url = f"https://{site_target}"
            else:
                target_url = f"https://www.{site_target}.com"

            return {
                "action": {
                    "tool": "open_website",
                    "parameters": {"url": target_url, "search_query": ""},
                    "description": f"Open {target_url} in Google Chrome",
                    "status": "pending"
                },
                "summary": f"open {target_url} in Chrome",
                "safety_level": "safe"
            }

        # 11. Direct URL Match
        url_match = re.search(
            r'^(?:open|go\s+to|visit|browse|navigate\s+to|khol)\s+(?:url\s+)?(https?:\/\/[^\s]+|[a-zA-Z0-9\-\.]+\.(?:com|org|io|dev|net|edu|gov|co|ai|tv|me|app|info)(?:\/[^\s]*)?)$',
            raw,
            re.IGNORECASE
        )
        if url_match:
            raw_url = url_match.group(1).strip()
            if not raw_url.startswith("http://") and not raw_url.startswith("https://"):
                raw_url = f"https://{raw_url}"
            return {
                "action": {
                    "tool": "open_website",
                    "parameters": {"url": raw_url, "search_query": ""},
                    "description": f"Navigate to {raw_url} in Chrome",
                    "status": "pending"
                },
                "summary": f"open {raw_url}",
                "safety_level": "safe"
            }

        # 12. Open Famous Web Services
        famous_match = re.search(
            r'^(?:open|launch|visit|go\s+to|khol|kholo)\s+(?:the\s+)?(youtube|reddit|github|wikipedia|netflix|amazon|facebook|instagram|linkedin|chatgpt|openai|twitch|stackoverflow)$',
            low
        )
        if not famous_match:
            famous_match = re.search(
                r'^(?:the\s+)?(youtube|reddit|github|wikipedia|netflix|amazon|facebook|instagram|linkedin|chatgpt|openai|twitch|stackoverflow)\s+(?:open|launch|visit|khol|kholo|chala|laga|open\s+kar|open\s+karo|khol\s+de|khol\s+do|chala\s+de|laga\s+de)$',
                low
            )
        if famous_match:
            site_key = famous_match.group(1).lower()
            site_url = famous_sites.get(site_key, f"https://www.{site_key}.com")
            return {
                "action": {
                    "tool": "open_website",
                    "parameters": {"url": site_url, "search_query": ""},
                    "description": f"Open {site_url} in Google Chrome",
                    "status": "pending"
                },
                "summary": f"open {site_key.title()}",
                "safety_level": "safe"
            }

        # 12b. Absolute / Drive path file & folder creation (any drive, any folder)
        # E.g. "D:\projects\test.txt bana de", "C:/Users/xyz/Documents/note.txt bana de",
        #      "D drive me file bana de", "E drive pe folder bana de", "/home/user/data/file.txt bana de"
        m_abs_path = re.search(r'(?:(?:create|make|write|bana\s+de|bana\s+do|banao|bana)\s+(?:a\s+)?(?:new\s+)?(?:file|folder|directory)?\s+(?:at|in|on|par|pe)?\s*)?([A-Za-z]:[\\/][^\s\'"]+|[\\/](?:home|Users|tmp|opt|srv|mnt|media|data|projects)[\\/][^\s\'"]+)', raw, re.IGNORECASE)
        m_drive = re.search(r'\b([A-Za-z])\s*:\s*\\?\s*(?:drive|disk)\b', low)
        m_drive_file = re.search(r'^(?:create|make|write|new|bana\s+de|bana\s+do|banao|bana)\s+(?:a\s+)?(?:new\s+)?(?:file\s+(?:named|called)\s+|file\s+)?["\']?([a-zA-Z0-9_\-\.]+(?:\.[a-zA-Z0-9]+)?)["\']?\s+(?:file|folder|directory)?\s*(?:on|in|at|par|pe|me|mein)\s+(?:the\s+)?([A-Za-z])\s*(?::)?\s*(?:drive|disk)', raw, re.IGNORECASE)
        m_drive_suffix = re.search(r'^(?:create|make|write|new|bana\s+de|bana\s+do|banao|bana)\s+(?:a\s+)?(?:new\s+)?(?:file\s+(?:named|called)\s+|file\s+)?["\']?([a-zA-Z0-9_\-\.]+(?:\.[a-zA-Z0-9]+)?)["\']?\s+(?:file|folder|directory)?\s+(?:in|on)\s+(?:the\s+)?([A-Za-z])\s*(?::)?\s*(?:drive|disk)', raw, re.IGNORECASE)
        # Drive-first form: "D drive me test.txt file bana de", "E drive pe folder bana de"
        m_drive_first = re.search(r'\b([A-Za-z])\s*(?::)?\s*(?:drive|disk)\s+(?:me|mein|par|pe|per|on|in)\s+(?:ek\s+)?["\']?([a-zA-Z0-9_\-\.]+(?:\.[a-zA-Z0-9]+)?)["\']?\s*(?:file|folder|directory)?\s*(?:bana\s+de|bana\s+do|banao|bana|create\s+kar|create\s+karo|create|make|new)?', raw, re.IGNORECASE)

        if m_abs_path and (re.search(r'\b(?:create|make|write|bana|banao|bana\s+de|bana\s+do|new)\b', low)):
            full_path = m_abs_path.group(1).strip()
            full_path = full_path.rstrip('.,;')
            is_file = '.' in full_path.split('/')[-1].split('\\')[-1]
            content = f"# Created by Zevion\n"
            if is_file:
                return {
                    "action": {
                        "tool": "create_file",
                        "parameters": {"path": full_path, "content": content},
                        "description": f"Create file at '{full_path}'",
                        "status": "pending"
                    },
                    "summary": f"create file {full_path}",
                    "safety_level": "moderate"
                }
            else:
                return {
                    "action": {
                        "tool": "create_folder",
                        "parameters": {"folder_path": full_path},
                        "description": f"Create folder at '{full_path}'",
                        "status": "pending"
                    },
                    "summary": f"create folder {full_path}",
                    "safety_level": "safe"
                }

        if m_drive_file or m_drive_suffix or m_drive_first:
            if m_drive_first:
                drive = m_drive_first.group(1).upper()
                name = m_drive_first.group(2).strip()
            else:
                m = m_drive_file or m_drive_suffix
                name = m.group(1).strip()
                drive = m.group(2).upper()
            is_folder = bool(re.search(r'\b(folder|directory)\b', low))
            # If the captured name is just the keyword "file"/"folder", use a default name
            if name.lower() in ["file", "folder", "directory"]:
                name = "New Folder" if is_folder else "new_file.txt"
            if is_folder:
                full_path = f"{drive}:\\{name}"
                return {
                    "action": {
                        "tool": "create_folder",
                        "parameters": {"folder_path": full_path},
                        "description": f"Create folder '{full_path}' on drive {drive}:",
                        "status": "pending"
                    },
                    "summary": f"create folder on {drive}:",
                    "safety_level": "safe"
                }
            else:
                full_path = f"{drive}:\\{name}"
                content = f"# Created by Zevion\n"
                return {
                    "action": {
                        "tool": "create_file",
                        "parameters": {"path": full_path, "content": content},
                        "description": f"Create file '{full_path}' on drive {drive}:",
                        "status": "pending"
                    },
                    "summary": f"create file on {drive}:",
                    "safety_level": "moderate"
                }

        # 13. Create Folder (English & Hinglish)
        # E.g. "mere Desktop par TestAgent naam ka folder bana de", "Desktop pe TestAgent folder banao", "create folder TestAgent on my desktop", "bhai ek folder bana de Projects naam ka"
        on_desktop = "desktop" in low
        clean_folder_raw = re.sub(r'^(?:bhai\s+|please\s+|plz\s+|bro\s+|kripya\s+)', '', raw, flags=re.IGNORECASE).strip()

        # Desktop pe/par <name> folder banao / Desktop par <name> naam ka folder bana do / Desktop par folder bana de
        m_desk_folder = re.search(r'^(?:mere\s+)?(?:desktop|workspace)\s+(?:pe|par|me|mein)\s+(?:(?:([a-zA-Z0-9_\-]+)\s+naam\s+ka\s+)?(?:folder|dir)\s+(?:bana\s+de|bana\s+do|create\s+karo|create\s+kar|banao|bana)|(?:([a-zA-Z0-9_\-]+)\s+folder\s+(?:bana\s+de|bana\s+do|create\s+karo|create\s+kar|banao|bana))|(?:folder|dir)\s+(?:bana\s+de|bana\s+do|create\s+karo|create\s+kar|banao|bana)\s*([a-zA-Z0-9_\-]+)?)$', clean_folder_raw, re.IGNORECASE)
        
        # ek folder bana de <name> [naam ka] / folder bana do [workspace]
        m_ek_folder = re.search(r'^(?:mere\s+)?(?:desktop|workspace)?\s*(?:pe|par|me|mein)?\s*(?:ek\s+|a\s+|an\s+)?(?:folder|dir|directory)\s+(?:bana\s+de|bana\s+do|create\s+karo|create\s+kar|banao|bana|make|create)(?:\s+(?:named|called|naam\s+ka))?\s*(?:["\']?([a-zA-Z0-9_\-\.\s]+?)["\']?)?(?:\s+(?:named|called|naam\s+ka))?(?:\s+(?:on|in|pe|par)\s+(?:my\s+)?(?:desktop|workspace))?$', clean_folder_raw, re.IGNORECASE)

        # create/make/bana [ek] folder [named] <name>
        m_create_folder = re.search(r'^(?:mere\s+desktop\s+par\s+|desktop\s+pe\s+|desktop\s+par\s+)?(?:create|make|bana\s+de|bana\s+do|create\s+karo|create\s+kar|banao|bana)\s+(?:a\s+|an\s+|ek\s+)?(?:new\s+)?(?:folder|dir|directory)(?:\s+(?:named|called|naam\s+ka))?\s*["\']?([a-zA-Z0-9_\-\.\s]+?)?["\']?(?:\s+(?:named|called|naam\s+ka))?(?:\s+(?:on|in|pe|par)\s+(?:my\s+)?(?:desktop|workspace))?$', clean_folder_raw, re.IGNORECASE)

        res_folder_name = None
        if m_desk_folder:
            res_folder_name = m_desk_folder.group(1) or m_desk_folder.group(2) or m_desk_folder.group(3) or "New Folder"
        elif m_ek_folder:
            res_folder_name = m_ek_folder.group(1) or "New Folder"
        elif m_create_folder:
            res_folder_name = m_create_folder.group(1) or "New Folder"

        if res_folder_name:
            folder_name = re.sub(r'\s+(?:on|in|pe|par)\s+(?:my\s+)?(?:desktop|workspace).*$', '', res_folder_name, flags=re.IGNORECASE).strip()
            folder_name = re.sub(r'\s+(?:naam\s+ka|named|called)$', '', folder_name, flags=re.IGNORECASE).strip()
            if not folder_name or folder_name.lower() in ["on my desktop", "on desktop", "my desktop", "desktop", "workspace"]:
                folder_name = "New Folder"
            
            final_folder_path = f"Desktop/{folder_name}" if on_desktop and not folder_name.startswith("Desktop") else folder_name
            return {
                "action": {
                    "tool": "create_folder",
                    "parameters": {"folder_path": final_folder_path},
                    "description": f"Create directory '{final_folder_path}'",
                    "status": "pending"
                },
                "summary": f"create folder {final_folder_path}",
                "safety_level": "safe"
            }

        # 14. Create File (English & Hinglish)
        # E.g. "mere Desktop par TestAgent folder ke andar hello.txt bana de", "Desktop par TestAgent folder mein hello.txt banao", "create hello.txt inside TestAgent folder on desktop", "create test.txt on my desktop"
        clean_file_raw = re.sub(r'^(?:bhai\s+|please\s+|plz\s+|bro\s+|kripya\s+)', '', raw, flags=re.IGNORECASE).strip()

        # Nested: Desktop par/pe <folder> folder ke andar/mein <file> bana de
        m_nested_file = re.search(r'^(?:mere\s+)?(?:desktop|workspace)?\s*(?:pe|par|me|mein)?\s*(?:["\']?([a-zA-Z0-9_\-]+)["\']?\s+(?:folder|dir)\s+(?:ke\s+andar|mein|me))\s+(?:["\']?([a-zA-Z0-9_\-\.\/\\]+\.[a-zA-Z0-9]+)["\']?)\s*(?:file\s+)?(?:bana\s+de|bana\s+do|create\s+karo|create\s+kar|banao|bana|make|create)(?:\s+(?:with\s+content|containing)\s+["\']?(.+?)["\']?)?$', clean_file_raw, re.IGNORECASE)
        if m_nested_file:
            folder = m_nested_file.group(1).strip()
            filename = m_nested_file.group(2).strip()
            content = m_nested_file.group(3) if m_nested_file.lastindex and m_nested_file.lastindex >= 3 and m_nested_file.group(3) else f"# Created by Zevion: {filename}\n"
            path = f"Desktop/{folder}/{filename}" if on_desktop and not folder.startswith("Desktop") else f"{folder}/{filename}"
            return {
                "action": {
                    "tool": "create_file",
                    "parameters": {"path": path, "content": content},
                    "description": f"Create file '{path}'",
                    "status": "pending"
                },
                "summary": f"create file {path}",
                "safety_level": "moderate"
            }

        # Nested English: create/make <file> inside/in <folder> [folder] [on desktop]
        m_eng_nested_file = re.search(r'^(?:create|make|write|new|bana\s+de|bana\s+do|banao|bana)\s+(?:a\s+)?(?:new\s+)?(?:file\s+(?:named|called)\s+|file\s+)?["\']?([a-zA-Z0-9_\-\.\/\\]+\.[a-zA-Z0-9]+)["\']?\s+(?:inside|in)\s+(?:the\s+)?(?:folder\s+)?["\']?([a-zA-Z0-9_\-]+)["\']?(?:\s+folder)?(?:\s+(?:on|in|pe|par)\s+(?:my\s+)?(?:desktop|workspace))?(?:\s+(?:with\s+content|containing)\s+["\']?(.+?)["\']?)?$', clean_file_raw, re.IGNORECASE)
        if m_eng_nested_file:
            filename = m_eng_nested_file.group(1).strip()
            folder = m_eng_nested_file.group(2).strip()
            content = m_eng_nested_file.group(3) if m_eng_nested_file.lastindex and m_eng_nested_file.lastindex >= 3 and m_eng_nested_file.group(3) else f"# Created by Zevion: {filename}\n"
            path = f"Desktop/{folder}/{filename}" if on_desktop and not folder.startswith("Desktop") else f"{folder}/{filename}"
            return {
                "action": {
                    "tool": "create_file",
                    "parameters": {"path": path, "content": content},
                    "description": f"Create file '{path}'",
                    "status": "pending"
                },
                "summary": f"create file {path}",
                "safety_level": "moderate"
            }

        # Standard create file on desktop or in workspace
        m_file = re.search(r'^(?:create|make|write|new|bana\s+de|bana\s+do|banao|bana)\s+(?:a\s+)?(?:new\s+)?(?:file\s+(?:named|called)\s+|file\s+)?["\']?([a-zA-Z0-9_\-\.\/\\]+\.[a-zA-Z0-9]+)["\']?(?:\s+(?:on|in|pe|par)\s+(?:my\s+)?(?:desktop|workspace))?(?:\s+(?:with\s+content|containing)\s+["\']?(.+?)["\']?)?$', clean_file_raw, re.IGNORECASE)
        if not m_file:
            m_file = re.search(r'^(?:mere\s+)?(?:desktop|workspace)?\s*(?:pe|par|me|mein)?\s*["\']?([a-zA-Z0-9_\-\.\/\\]+\.[a-zA-Z0-9]+)["\']?\s+(?:file\s+)?(?:bana\s+de|bana\s+do|create\s+karo|create\s+kar|banao|bana)(?:\s+(?:with\s+content|containing)\s+["\']?(.+?)["\']?)?$', clean_file_raw, re.IGNORECASE)

        if m_file:
            filename = m_file.group(1).strip()
            content = m_file.group(2) if m_file.lastindex and m_file.lastindex >= 2 and m_file.group(2) else f"# Created by Zevion: {filename}\n"
            path = f"Desktop/{filename}" if on_desktop and not filename.startswith("Desktop") and not "/" in filename and not "\\" in filename else filename
            return {
                "action": {
                    "tool": "create_file",
                    "parameters": {"path": path, "content": content},
                    "description": f"Create file '{path}' with complete content",
                    "status": "pending"
                },
                "summary": f"create file {path}",
                "safety_level": "moderate"
            }

        # Extension only (e.g. "create a new .txt file", "create a python file on desktop")
        m_ext = re.search(r'^(?:create|make|new|bana\s+de|bana\s+do|banao|bana)\s+(?:a\s+)?(?:new\s+)?\.?([a-zA-Z0-9]+)\s+file(?:\s+(?:on|in|pe|par)\s+(?:my\s+)?(?:desktop|workspace))?$', clean_file_raw, re.IGNORECASE)
        if m_ext:
            ext = m_ext.group(1).lstrip('.').lower()
            ext_map = {"python": "py", "javascript": "js", "typescript": "ts", "html": "html", "css": "css", "json": "json", "text": "txt"}
            real_ext = ext_map.get(ext, ext)
            filename = f"document.{real_ext}"
            path = f"Desktop/{filename}" if on_desktop else filename
            return {
                "action": {
                    "tool": "create_file",
                    "parameters": {"path": path, "content": f"# Created by Zevion\n"},
                    "description": f"Create file '{path}' with initial content",
                    "status": "pending"
                },
                "summary": f"create file {path}",
                "safety_level": "moderate"
            }

        # 15. Read File
        file_read_match = re.search(r'^(?:read|view|show|display|cat|examine|padh)\s+(?:the\s+)?file\s+["\']?([^"\']+)["\']?$', low)
        if file_read_match or low in ["open file", "open a file", "read file"]:
            file_path = file_read_match.group(1).strip() if file_read_match else "notes.txt"
            return {
                "action": {
                    "tool": "read_file",
                    "parameters": {"path": file_path},
                    "description": f"Read and inspect file '{file_path}'",
                    "status": "pending"
                },
                "summary": f"read file {file_path}",
                "safety_level": "safe"
            }

        # 16. Delete File (Dangerous)
        delete_match = re.search(r'^(?:delete|remove|erase|rm|destroy|format|hata|hatao)\s+(?:the\s+)?(?:file|folder|directory)?\s*["\']?([^"\']+)["\']?$', low)
        if delete_match:
            target = delete_match.group(1).strip()
            return {
                "action": {
                    "tool": "delete_file",
                    "parameters": {"path": target, "permanent": False},
                    "description": f"Delete '{target}' (Requires user confirmation)",
                    "status": "pending"
                },
                "summary": f"delete {target}",
                "safety_level": "dangerous",
                "confirmation_payload": {
                    "action_title": f"Delete {target}",
                    "severity": "high",
                    "impact": f"This will move '{target}' to the Recycle Bin (recoverable).",
                    "tool": "delete_file",
                    "parameters": {"path": target}
                }
            }

        # 17. Organize Files
        if any(k in low for k in ["organize my files", "organize files", "clean my desktop", "clean downloads", "sort files", "organize folder", "clean up folder"]):
            target_folder = "Downloads"
            if "desktop" in low:
                target_folder = "Desktop"
            elif "project" in low:
                target_folder = "Projects"
            elif "documents" in low or "docs" in low:
                target_folder = "Documents"

            return {
                "action": {
                    "tool": "organize_files",
                    "parameters": {"directory": target_folder, "strategy": "by_category"},
                    "description": f"Categorize and organize files in {target_folder}",
                    "status": "pending"
                },
                "summary": f"organize files in {target_folder}",
                "safety_level": "moderate"
            }

        # 17b. Analyze Screen / Screenshot Vision (requires explicit request)
        analyze_screen_patterns = [
            "analyze the screen", "analyse the screen", "analyze my screen", "analyze the screenshot",
            "analyze the desktop", "what is on my screen", "what's on my screen", "whats on my screen",
            "what is on the screen", "what do you see", "screen pe kya hai", "screen par kya hai",
            "screen me kya hai", "dekho screen pe kya hai", "analyze screen"
        ]
        if any(k in low for k in analyze_screen_patterns):
            return {
                "action": {
                    "tool": "analyze_screenshot",
                    "parameters": {"save_path": "screenshot.png"},
                    "description": "Capture and analyze the current screen",
                    "status": "pending"
                },
                "summary": "analyze the screen",
                "safety_level": "safe"
            }

        # 18. Screenshot (Requires EXPLICIT imperative request to capture the screen)
        screenshot_conversational_indicators = [
            "took a screenshot", "taken a screenshot", "sent a screenshot", "sent you a screenshot",
            "has a bug", "shows the bug", "shows a bug", "shows that", "shows",
            "was looking at", "looking at a screenshot", "checking the screenshot",
            "what is a screenshot", "what a screenshot is", "kya hota hai", "kya hai",
            "is this a screenshot", "screenshot of google", "screenshot dekh", "dekho screenshot",
            "about screenshot", "about a screenshot"
        ]
        is_screenshot_conversational = any(sci in low for sci in screenshot_conversational_indicators)

        m_shot = None
        if not is_screenshot_conversational:
            # Explicit English & Hinglish imperatives
            m_shot = re.search(
                r'^(?:bhai\s+|bro\s+|please\s+|plz\s+|can\s+you\s+|could\s+you\s+)?(?:take\s+(?:a\s+|an\s+|the\s+)?screenshot(?:\s+of\s+(?:my\s+|the\s+|current\s+|the\s+current\s+|my\s+current\s+)?(?:screen|desktop))?|capture\s+(?:my\s+|the\s+|current\s+|the\s+current\s+|my\s+current\s+)?(?:screen|desktop)|(?:screen\s+ka\s+|desktop\s+ka\s+)?screenshot\s+(?:le|lo|le\s+lo|le\s+de|khich|khicho|lena\s+hai|capture\s+kar|capture\s+karo|nikal|nikalo)|snip\s+(?:the\s+|my\s+)?screen)$',
                low
            )
            if not m_shot:
                # Suffix form: e.g. "ek screenshot le", "screen capture kar", "desktop screenshot le lo", "screenshot please"
                m_shot = re.search(
                    r'^(?:bhai\s+|bro\s+|please\s+|plz\s+)?(?:ek\s+|a\s+)?(?:screen\s+|desktop\s+|current\s+screen\s+|the\s+current\s+screen\s+)?screenshot\s+(?:le|lo|le\s+lo|le\s+de|khicho|khich|nikalo|nikal|capture\s+kar|capture\s+karo|please)$',
                    low
                )

        if m_shot:
            return {
                "action": {
                    "tool": "take_screenshot",
                    "parameters": {"region": "fullscreen", "save_path": "screenshot.png"},
                    "description": "Capture current desktop screenshot",
                    "status": "pending"
                },
                "summary": "take screenshot",
                "safety_level": "safe"
            }

        # 19. Mouse Control
        mouse_match = re.search(r'^(?:move\s+mouse|click|mouse\s+click)\s+(?:at\s+)?(\d+)\s*,?\s*(\d+)?$', low)
        if mouse_match:
            x = int(mouse_match.group(1))
            y = int(mouse_match.group(2)) if mouse_match.group(2) else 500
            return {
                "action": {
                    "tool": "control_mouse",
                    "parameters": {"x": x, "y": y, "click": "left"},
                    "description": f"Move mouse to ({x}, {y}) and left click",
                    "status": "pending"
                },
                "summary": f"mouse click at ({x}, {y})",
                "safety_level": "safe"
            }

        # 20. Execute Command
        cmd_match = re.search(r'^(?:execute|exec)\s+(?:command\s+|shell\s+)?["\']?([^"\']+)["\']?$|^(?:run|terminal|bash|powershell|cmd)\s+(?:command\s+|script\s+)["\']?([^"\']+)["\']?$', low)
        if not cmd_match and re.match(r'^(?:execute|run|exec)\s+(?:command\s+)?(.+)$', low) and not any(k in low for k in ["window", "khol", "kholo", "open", "launch", "browser", "app", "application", "file", "folder", "aur"]):
            cmd_match = re.match(r'^(?:execute|run|exec)\s+(?:command\s+)?(.+)$', low)
        if cmd_match or low in ["run a program", "run program"]:
            cmd = ""
            if cmd_match:
                for g_idx in range(1, (cmd_match.lastindex or 0) + 1):
                    val = cmd_match.group(g_idx)
                    if val:
                        cmd = val.strip("\"' ")
                        break
            if not cmd:
                cmd = "echo 'Hello from Zevion! Running diagnostics...'"
            is_dangerous = any(d in cmd.lower() for d in ["rm -rf", "format", "del /f", "drop database", "mkfs", "dd if=", ":(){ :|:& };:"])
            return {
                "action": {
                    "tool": "execute_command",
                    "parameters": {"command": cmd, "cwd": workspace},
                    "description": f"Execute shell command: '{cmd}'",
                    "status": "pending"
                },
                "summary": f"execute command '{cmd}'",
                "safety_level": "dangerous" if is_dangerous else "moderate"
            }

        # 21. System Info / Diagnostics (English & Hinglish)
        diag_patterns = [
            "diagnose my pc", "diagnose my computer", "how is my pc", "how is my computer",
            "run a pc diagnosis", "pc diagnose", "pc diagnosis",
            "kaisa chal raha hai", "kaisa chal rha", "mera pc check kar", "pc check kar",
            "check cpu and ram", "check ram and cpu", "how much ram", "what is my cpu",
            "why is my pc slow", "my pc is slow", "pc is slow", "pc slow", "computer slow",
            "why is my computer lagging", "what's wrong with my pc",
            "dekh pc me koi problem", "get system info", "query system info", "system status"
        ]
        is_diag_query = any(k in low for k in diag_patterns) or low in ["diagnostics", "check my pc", "system info", "check pc", "check cpu", "check ram", "show system info", "view system info"]
        if is_diag_query and not any(k in low for k in ["open", "launch", "khol", "kholo", "chala", "start", "snap", "screenshot", "capture"]):
            return {
                "action": {
                    "tool": "get_system_info",
                    "parameters": {},
                    "description": "Gather system resource metrics, CPU, RAM, Disk, and PC health",
                    "status": "pending"
                },
                "summary": "diagnose PC and query system info",
                "safety_level": "safe"
            }

        # 22. Window Management (Minimize, Maximize, Restore, Close)
        current_window_tokens = ["this window", "the current window", "current window", "this", "it", "the window", "active window", "foreground window", "window", "isko", "ye", "yeh"]

        # A. Minimize (English & Hinglish: "bhai isko minimize kar", "isko chhota kar", "ye minimize kar", "isko hide kar")
        m_min = re.search(r'^(?:bhai\s+)?(?:minimize|hide|make\s+small|minimise|chhota\s+kar|minimize\s+kar|hide\s+kar)\s+(?:the\s+)?(.+?)(?:\s+(?:app|application|window|kar|de|do))?$', raw, re.IGNORECASE)
        m_min_target = None
        if m_min:
            m_min_target = m_min.group(1).strip()
        elif low in ["minimize", "minimise", "hide window", "minimize window", "make window small", "minimize the window", "minimize the current window", "minimize this window", "minimize current window", "minimize it", "isko minimize kar", "ye minimize kar", "isko chhota kar"]:
            m_min_target = "current"

        if m_min_target is not None:
            target_clean = m_min_target.lower().strip()
            if target_clean in current_window_tokens or target_clean == "":
                target_app_key = context.get("last_app", "current") if target_clean in ["it", "this", "isko", "ye", "yeh"] and context.get("last_app") else "current"
                disp_target = "current window" if target_app_key == "current" else target_app_key.title()
            else:
                m_key, m_info, m_score = self.resolve_fuzzy_app(target_clean)
                target_app_key = m_key if (m_key and m_score >= 0.55) else target_clean
                disp_target = m_info.get("display_name", m_info.get("name", target_clean.title())) if m_info else target_clean.title()

            return {
                "action": {
                    "tool": "minimize_window",
                    "parameters": {"app_name": target_app_key},
                    "description": f"Minimize {disp_target}",
                    "status": "pending"
                },
                "summary": f"minimize {disp_target}",
                "safety_level": "safe"
            }

        # B. Maximize (English & Hinglish: "bhai isko maximize kar", "bada kar", "fullscreen kar de")
        m_max = re.search(r'^(?:bhai\s+)?(?:maximize|maximise|fullscreen|make\s+(?:full\s*screen|fullscreen)|bada\s+kar|maximize\s+kar|fullscreen\s+kar)\s+(?:the\s+)?(.+?)(?:\s+(?:app|application|window|kar|de|do))?$', raw, re.IGNORECASE)
        if not m_max:
            m_max = re.search(r'^make\s+(.+?)\s+(?:full\s*screen|fullscreen)$', raw, re.IGNORECASE)
        m_max_target = None
        if m_max:
            m_max_target = m_max.group(1).strip()
        elif low in ["maximize", "maximise", "fullscreen", "maximize window", "make window fullscreen", "make full screen", "maximize the window", "maximize the current window", "maximize this window", "maximize current window", "maximize it", "make it full screen", "isko maximize kar", "bada kar", "fullscreen kar"]:
            m_max_target = "current"

        if m_max_target is not None:
            target_clean = m_max_target.lower().strip()
            if target_clean in current_window_tokens or target_clean == "":
                target_app_key = context.get("last_app", "current") if target_clean in ["it", "this", "isko", "ye", "yeh"] and context.get("last_app") else "current"
                disp_target = "current window" if target_app_key == "current" else target_app_key.title()
            else:
                m_key, m_info, m_score = self.resolve_fuzzy_app(target_clean)
                target_app_key = m_key if (m_key and m_score >= 0.55) else target_clean
                disp_target = m_info.get("display_name", m_info.get("name", target_clean.title())) if m_info else target_clean.title()

            return {
                "action": {
                    "tool": "maximize_window",
                    "parameters": {"app_name": target_app_key},
                    "description": f"Maximize {disp_target}",
                    "status": "pending"
                },
                "summary": f"maximize {disp_target}",
                "safety_level": "safe"
            }

        # C. Restore (English & Hinglish: "restore kar", "wapas la", "unminimize kar")
        m_rest = re.search(r'^(?:bhai\s+)?(?:restore|unminimize|un-minimize|bring\s+back|wapas\s+la|restore\s+kar)\s+(?:the\s+)?(.+?)(?:\s+(?:app|application|window|kar|de|do))?$', raw, re.IGNORECASE)
        m_rest_target = None
        if m_rest:
            m_rest_target = m_rest.group(1).strip()
        elif low in ["restore", "unminimize", "bring back", "restore window", "restore the window", "restore the current window", "restore this window", "restore current window", "restore it", "bring it back", "bring this window back", "isko restore kar", "wapas la"]:
            m_rest_target = "current"

        if m_rest_target is not None:
            target_clean = m_rest_target.lower().strip()
            if target_clean in current_window_tokens or target_clean == "":
                target_app_key = context.get("last_app", "current") if target_clean in ["it", "this", "isko", "ye", "yeh"] and context.get("last_app") else "current"
                disp_target = "current window" if target_app_key == "current" else target_app_key.title()
            else:
                m_key, m_info, m_score = self.resolve_fuzzy_app(target_clean)
                target_app_key = m_key if (m_key and m_score >= 0.55) else target_clean
                disp_target = m_info.get("display_name", m_info.get("name", target_clean.title())) if m_info else target_clean.title()

            return {
                "action": {
                    "tool": "restore_window",
                    "parameters": {"app_name": target_app_key},
                    "description": f"Restore {disp_target}",
                    "status": "pending"
                },
                "summary": f"restore {disp_target}",
                "safety_level": "safe"
            }

        # D. Close (English & Hinglish: "close kar", "band kar", "band karo", "ye window band kar de")
        m_close = re.search(r'^(?:bhai\s+)?(?:close|shut|exit|quit|band\s+kar|band\s+karo|close\s+kar)\s+(?:the\s+)?(.+?)(?:\s+(?:app|application|window|kar|de|do))?$', raw, re.IGNORECASE)
        m_close_target = None
        if m_close:
            m_close_target = m_close.group(1).strip()
        elif low in ["close", "shut", "close window", "shut window", "close the window", "close the current window", "close this window", "close current window", "close it", "shut this window", "shut the current window", "ye window band kar de", "isko band kar", "ye band kar"]:
            m_close_target = "current"

        if m_close_target is not None and not any(bad in low for bad in ["file", "folder", "directory", "dir", "tab"]):
            target_clean = m_close_target.lower().strip()
            if target_clean in current_window_tokens or target_clean == "":
                target_app_key = context.get("last_app", "current") if target_clean in ["it", "this", "isko", "ye", "yeh"] and context.get("last_app") else "current"
                disp_target = "current window" if target_app_key == "current" else target_app_key.title()
            else:
                m_key, m_info, m_score = self.resolve_fuzzy_app(target_clean)
                target_app_key = m_key if (m_key and m_score >= 0.55) else target_clean
                disp_target = m_info.get("display_name", m_info.get("name", target_clean.title())) if m_info else target_clean.title()

            return {
                "action": {
                    "tool": "close_window",
                    "parameters": {"app_name": target_app_key},
                    "description": f"Close {disp_target}",
                    "status": "pending"
                },
                "summary": f"close {disp_target}",
                "safety_level": "safe"
            }

        # 23. Universal Application Launcher & Explicit Open Intent System
        is_new_window = False
        candidate_app = None

        # Exclude conversational questions / statements / past tense indicators from triggering app launches
        conversational_indicators = [
            "se maine", "maine", "yesterday", "ka ui", "mein maine", "kya hai",
            "slow chal raha", "do you know", "is useful", "was using", "i was",
            "i installed", "i used", "what is", "tell me about", "accha hai",
            "about", "how to", "why is", "can i", "could you tell", "batao", "bata"
        ]
        is_conversational_statement = any(ci in low for ci in conversational_indicators)

        if not is_conversational_statement:
            # A. Explicit "New Window" / "Another Window" Intent Detection (English & Hinglish)
            # E.g. "bhai ek naya CMD khol", "ek aur CMD khol", "naya Notepad window khol", "PowerShell ki new window khol", "ek aur khol"
            m_new_win = re.search(
                r'^(?:bhai\s+|bro\s+|please\s+|plz\s+)?(?:open|launch|start|run|create|bring\s+up|khol|kholo)\s+(?:a\s+|an\s+|ek\s+)?(?:new|another|separate|naya|dusra|aur)\s+(?:window\s+(?:of|for|ki\s+)?|instance\s+(?:of|for|ki\s+)?|app\s+)?([a-zA-Z0-9\s_\-\.]+?)(?:\s+(?:window|instance|app|application|program|software|khol|kholo|chala|de))?$',
                low
            )
            if not m_new_win:
                m_new_win = re.search(
                    r'^(?:bhai\s+|bro\s+|please\s+|plz\s+)?(?:ek\s+|a\s+|an\s+)?(?:new|another|separate|naya|dusra)\s+(?:window\s+(?:of|for|ki\s+)?|instance\s+(?:of|for|ki\s+)?|app\s+)?([a-zA-Z0-9\s_\-\.]+?)(?:\s+(?:window|instance|app|application|program|software))?\s+(?:khol|kholo|chala|de|open|start)$',
                    low
                )
            if not m_new_win:
                m_new_win = re.search(
                    r'^(?:bhai\s+|bro\s+|please\s+|plz\s+)?([a-zA-Z0-9\s_\-\.]+?)\s+(?:ki\s+)?(?:new\s+window|naya\s+window|new\s+instance|another\s+window)(?:\s+(?:khol|kholo|chala|open|start))?$',
                    low
                )
            if not m_new_win:
                m_new_win = re.search(
                    r'^(?:new|another|separate|naya|dusra|ek\s+aur)\s+(?:window|instance)\s+(?:of|for|ki\s+)?([a-zA-Z0-9\s_\-\.]+?)$',
                    low
                )
            if not m_new_win:
                # Contextual "ek aur khol"
                if low in ["ek aur khol", "ek aur window khol", "open another", "open another window", "open a new one"]:
                    candidate_app = context.get("last_app", "chrome")
                    is_new_window = True

            if m_new_win:
                candidate_app = m_new_win.group(1).strip()
                is_new_window = True
            else:
                # B. Explicit Prefix Launch Match (English: open, launch, start, run, bring up; Hinglish: khol, kholo, chala, chalao)
                # MUST have the explicit launch verb at the beginning
                m_prefix = re.search(
                    r'^(?:bhai\s+|bro\s+|please\s+|plz\s+|can\s+you\s+|could\s+you\s+)?(?:open|launch|start|run|bring\s+up|khol|kholo|khol\s+de|khol\s+do|chala|chalao|chala\s+de|chala\s+do|chalu\s+kar|chalu\s+karo)\s+(?:the\s+|a\s+|an\s+|ek\s+)?([a-zA-Z0-9\s_\-\.]+?)(?:\s+(?:application|program|software|window))?$',
                    low
                )
                if m_prefix:
                    cand = m_prefix.group(1).strip()
                    if cand not in ["something", "it", "this", "a file", "the file", "file", "folder", "directory"]:
                        candidate_app = cand
                        is_new_window = False

                # C. Explicit Suffix Launch Match (Hinglish: khol, kholo, khol de, khol do, chala de, open kar, open karo, start kar, etc.)
                if not candidate_app:
                    m_suffix = re.search(
                        r'^(?:bhai\s+|bro\s+|please\s+|plz\s+)?(?:the\s+|ek\s+)?([a-zA-Z0-9\s_\-\.]+?)\s+(?:khol|kholo|khol\s+de|khol\s+do|kholna|kholna\s+hai|kholiye|chala|chalao|chala\s+de|chala\s+do|chalu\s+kar|chalu\s+karo|open\s+kar|open\s+karo|open\s+kijiye|open\s+karna\s+hai|open\s+de|open\s+do|start\s+kar|start\s+karo|launch\s+kar|launch\s+karo|open\s+please)$',
                        low
                    )
                    if m_suffix:
                        cand = m_suffix.group(1).strip()
                        if cand not in ["something", "it", "this", "file", "folder", "directory"]:
                            candidate_app = cand
                            is_new_window = False

        if candidate_app and candidate_app not in ["a conversation", "chat", "a joke", "help", "file", "folder", "directory", "dir", "bhai", "bro"]:
            matched_key, matched_info, match_score = self.resolve_fuzzy_app(candidate_app)
            if matched_info and match_score >= 0.70:
                resolved_key = matched_key
                resolved_display_name = matched_info.get("display_name", matched_info.get("name", matched_key.title()))
            else:
                # If cannot be confidently matched to a known alias/registry, preserve exact requested name
                resolved_key = candidate_app.strip()
                resolved_display_name = candidate_app.strip().title()

            # If user says "open youtube" (and not asking for a new window of Chrome), route to website
            if resolved_key in ["youtube", "yt"] and not is_new_window:
                return {
                    "action": {
                        "tool": "open_website",
                        "parameters": {"url": "https://www.youtube.com", "search_query": "", "playback": False},
                        "description": "Open YouTube homepage in Google Chrome",
                        "status": "pending"
                    },
                    "summary": "open YouTube",
                    "safety_level": "safe"
                }

            params = {"app_name": resolved_key}
            if is_new_window:
                params["new_window"] = True

            desc = f"Launch new {resolved_display_name} window" if is_new_window else f"Launch {resolved_display_name}"
            summary = f"open a new {resolved_display_name} window" if is_new_window else f"open {resolved_display_name}"

            return {
                "action": {
                    "tool": "open_application",
                    "parameters": params,
                    "description": desc,
                    "status": "pending"
                },
                "summary": summary,
                "safety_level": "safe"
            }

        # 24. Clipboard Control (copy / paste / read clipboard)
        if low in ["paste", "paste it", "paste kar", "paste karo", "paste kar de", "paste from clipboard", "clipboard se paste kar"]:
            return {
                "action": {
                    "tool": "clipboard_get",
                    "parameters": {},
                    "description": "Read text from the clipboard",
                    "status": "pending"
                },
                "summary": "read clipboard",
                "safety_level": "safe"
            }
        m_copy = re.search(r'^(?:copy|clipboard\s+(?:me|par|pe)?\s*)(?:the\s+|this\s+|text\s+)?["\']?(.+?)["\']?(?:\s+(?:to\s+(?:the\s+)?clipboard|clipboard\s+(?:me|par|pe)|kar\s+de|karo))?\s*$', raw, re.IGNORECASE)
        if m_copy and ("clipboard" in low or low.startswith("copy")):
            copied_text = m_copy.group(1).strip("'\" ")
            if not copied_text:
                m_copy = None
            return {
                "action": {
                    "tool": "clipboard_set",
                    "parameters": {"text": m_copy.group(1).strip('"\' ')},
                    "description": "Copy text to the clipboard",
                    "status": "pending"
                },
                "summary": f"copy '{m_copy.group(1).strip()[:40]}' to clipboard",
                "safety_level": "safe"
            }

        # 25. Find Files (search by name on Desktop/Downloads/Documents)
        m_find = re.search(r'(?:find|search|locate|dhundh|dhundho|dhund|kahan\s+hai|kha\s+hai|dhundo)\s+(?:me\s+)?(?:the\s+|files?\s+named\s+|file\s+named\s+|file\s+|for\s+)?(.+?)(?:\s+(?:file|files|folder|on\s+(?:the\s+)?desktop|desktop\s+(?:par|pe|mein)|in\s+desktop|in\s+downloads|in\s+documents))?$', raw, re.IGNORECASE)
        is_find_intent = (re.search(r'\b(?:find|search|locate|dhundh|dhundho|dhund|kahan\s+hai)\b', low) and re.search(r'\b(?:file|files|folder|document|photo|image|video|pdf)\b', low))
        if m_find and is_find_intent:
            pattern = m_find.group(1).strip()
            directory = None
            if "downloads" in low:
                directory = "Downloads"
            elif "documents" in low:
                directory = "Documents"
            return {
                "action": {
                    "tool": "find_files",
                    "parameters": {"pattern": pattern, "directory": directory},
                    "description": f"Search for files matching '{pattern}'",
                    "status": "pending"
                },
                "summary": f"find files matching '{pattern}'",
                "safety_level": "safe"
            }

        # 26. Media Control (play/pause/next/previous/volume/mute)
        media_map = {
            "pause": "play_pause", "play": "play_pause", "resume": "play_pause",
            "next": "next", "skip": "next", "previous": "previous", "prev": "previous",
            "stop": "stop"
        }
        m_media = re.search(r'^(?:bhai\s+)?(?:please\s+)?(play|pause|resume|stop)\s+(?:the\s+)?(?:music|song|video|audio|track|gaana|gana)\b', low)
        m_next = re.search(r'^(?:bhai\s+)?(?:next|skip)\s+(?:song|track|music|video|gaana|gana)\b', low)
        m_prev = re.search(r'^(?:bhai\s+)?(?:previous|prev)\s+(?:song|track|music|video|gaana|gana)\b', low)
        m_mute = re.search(r'^(?:bhai\s+)?(?:mute|unmute|volume\s+off|chup|silent)\b', low)
        m_volup = re.search(r'^(?:bhai\s+)?(?:volume\s+up|volume\s+badhao|volume\s+bada|awaz\s+badhao|awaz\s+bada|louder)\b', low)
        m_voldown = re.search(r'^(?:bhai\s+)?(?:volume\s+down|volume\s+ghatao|volume\s+kam|awaz\s+kam|awaz\s+ghatao|softer)\b', low)
        media_action = None
        if m_mute:
            media_action = "mute"
        elif m_volup:
            media_action = "volume_up"
        elif m_voldown:
            media_action = "volume_down"
        elif m_prev:
            media_action = "previous"
        elif m_next:
            media_action = "next"
        elif m_media:
            w = m_media.group(1)
            media_action = media_map.get(w, "play_pause")
        if media_action:
            return {
                "action": {
                    "tool": "media_control",
                    "parameters": {"action": media_action},
                    "description": f"Media control: {media_action}",
                    "status": "pending"
                },
                "summary": f"media {media_action}",
                "safety_level": "safe"
            }

        # 27. Keyboard Shortcuts (press key combos like Ctrl+C, Win+D, Alt+Tab)
        m_keys = re.search(r'^(?:bhai\s+)?(?:press|dabao|daba|hit|push|type\s+shortcut\s+)?\s*([a-z0-9]+(?:\s*[+\-]\s*[a-z0-9]+){1,3})$', low, re.IGNORECASE)
        is_keys_intent = bool(re.search(r'\b(?:press|dabao|daba|hit|push|shortcut|combo)\b', low)) and bool(re.search(r'[+\-]', low)) and len(low.split()) <= 6
        if m_keys and is_keys_intent:
            combo = re.sub(r'\s+', '', m_keys.group(1)).replace('-', '+')
            return {
                "action": {
                    "tool": "press_keys",
                    "parameters": {"keys": combo},
                    "description": f"Press keyboard shortcut {combo}",
                    "status": "pending"
                },
                "summary": f"press {combo}",
                "safety_level": "safe"
            }

        # 28. Battery Status (English & Hinglish)
        is_battery = any(k in low for k in [
            "battery status", "battery level", "battery percentage", "battery kitna",
            "battery kitni", "battery kya hai", "how much battery", "battery left",
            "charging", "battery charge", "battery health", "laptop battery"
        ]) or low in ["battery", "battery batao", "battery bata", "battery check kar"]
        if is_battery and not any(k in low for k in ["open", "launch", "app"]):
            return {
                "action": {
                    "tool": "get_battery",
                    "parameters": {},
                    "description": "Read laptop battery status and charge level",
                    "status": "pending"
                },
                "summary": "check battery status",
                "safety_level": "safe"
            }

        # 29. Quick Note Capture (English & Hinglish)
        m_note = re.search(r'^(?:(?:add\s+)?note(?!pad)(?:\s+(?:down|karo|kar\s+lo|kar\s+de|kar))?|yaad\s+rakh|yaad\s+rakho|remember|save\s+note|likh\s+lo|likh\s+kar|likh\s+de)\s*[:：\-]?\s*(.+)$', raw, re.IGNORECASE)
        if m_note and m_note.group(1).strip():
            note_text = m_note.group(1).strip()
            # Strip a leading "to" from "remember to X"
            if low.startswith("remember") and note_text.lower().startswith("to "):
                note_text = note_text[3:].strip()
            return {
                "action": {
                    "tool": "add_note",
                    "parameters": {"text": note_text},
                    "description": f"Save note: '{note_text[:50]}'",
                    "status": "pending"
                },
                "summary": f"save note '{note_text[:40]}'",
                "safety_level": "moderate"
            }

        # 30. List Directory / Show Files (English & Hinglish)
        dir_keys = ["desktop", "downloads", "documents", "projects", "workspace", "music", "pictures", "videos"]
        m_list_dir = re.search(r'\b(desktop|downloads|documents|projects|workspace|music|pictures|videos)\s+(?:me|mein|par|pe|folder|directory|ke\s+andar)\s+(?:kya\s+hai|kya\s+rakha|kya\s+pada|ky\s+hai|files?|folders?|items?|contents?|kya)\b', low)
        m_list_eng = re.search(r'^(?:show|list|display)\s+(?:me\s+)?(?:the\s+|my\s+)?(?:files|folders?|items|contents?)?\s*(?:in|on|inside|of)?\s*(?:the\s+|my\s+)?(desktop|downloads|documents|projects|workspace|music|pictures|videos)?\s*(?:folder|directory)?\s*$', raw, re.IGNORECASE)
        is_list_intent = bool(re.search(r'\b(?:show|list|display)\b', low))
        if m_list_dir or (m_list_eng and is_list_intent):
            directory = None
            g = (m_list_dir.group(1) if m_list_dir else (m_list_eng.group(1) if m_list_eng else None))
            if g:
                directory = g.capitalize()
            return {
                "action": {
                    "tool": "list_directory",
                    "parameters": {"directory": directory},
                    "description": f"List files in {directory or 'Desktop'}",
                    "status": "pending"
                },
                "summary": f"list files in {directory or 'Desktop'}",
                "safety_level": "safe"
            }

        return None

    def _parse_compound_command(self, text: str, workspace: str) -> Optional[Dict[str, Any]]:
        clauses = self._split_into_clauses(text)
        if len(clauses) < 2:
            return None

        parsed_clauses = []
        context: Dict[str, Any] = {}

        for clause in clauses:
            act_data = self._parse_single_clause(clause, context=context, workspace=workspace)
            if not act_data or not act_data.get("action"):
                return None

            action = act_data["action"]
            parsed_clauses.append(act_data)

            tool_name = action.get("tool")
            params = action.get("parameters", {})
            if tool_name == "open_application":
                context["last_app"] = params.get("app_name")
                if params.get("app_name") == "chrome":
                    context["last_site"] = "google"
            elif tool_name == "open_website":
                context["last_app"] = "chrome"
                url = params.get("url", "").lower()
                if "youtube" in url or "yt" in url:
                    context["last_site"] = "youtube"
                else:
                    context["last_site"] = "google"

        if len(parsed_clauses) < 2:
            return None

        first_act = parsed_clauses[0]["action"]
        second_act = parsed_clauses[1]["action"]

        is_first_yt_homepage = (
            first_act.get("tool") == "open_website" and
            first_act.get("parameters", {}).get("url") == "https://www.youtube.com" and
            not first_act.get("parameters", {}).get("search_query")
        )
        is_second_yt_action = (
            second_act.get("tool") == "open_website" and
            "youtube" in second_act.get("parameters", {}).get("url", "").lower()
        )

        if is_first_yt_homepage and is_second_yt_action:
            target_act_data = parsed_clauses[1]
            target_action = target_act_data["action"]
            summary = target_act_data.get("summary", target_action.get("description", ""))
            
            if target_action.get("parameters", {}).get("playback"):
                query = target_action["parameters"].get("search_query", "")
                resp = f"Opening YouTube and starting playback for \"{query}\"."
            else:
                query = target_action["parameters"].get("search_query", "")
                resp = f"Searching YouTube for \"{query}\" in your browser."

            return {
                "summary": summary,
                "reasoning": f"Optimized prerequisite navigation: Directly navigating to YouTube {'playback' if target_action.get('parameters', {}).get('playback') else 'search'} for '{query}' without opening a redundant homepage tab.",
                "actions": [target_action],
                "safety_level": "safe",
                "confirmation_required": False,
                "response": resp
            }

        actions = []
        action_descriptions = []
        has_dangerous = False
        confirmation_req = False
        confirmation_payload = None

        for act_data in parsed_clauses:
            action = act_data["action"]
            actions.append(action)
            action_descriptions.append(act_data.get("summary", action.get("description", "")))

            if act_data.get("safety_level") == "dangerous":
                has_dangerous = True
                confirmation_req = True
                confirmation_payload = act_data.get("confirmation_payload")

        if len(actions) >= 2:
            combined_summary = " and ".join(action_descriptions)
            combined_response = f"Executing compound command: {combined_summary}."
            return {
                "summary": combined_summary,
                "reasoning": f"Parsed multi-step compound command into {len(actions)} sequential actions.",
                "actions": actions,
                "safety_level": "dangerous" if has_dangerous else "safe",
                "confirmation_required": confirmation_req,
                "confirmation_payload": confirmation_payload,
                "response": combined_response
            }

        return None

    def _parse_intent_and_plan(self, text: str, workspace: str, conversation_context: Optional[List[Dict[str, Any]]] = None, attachments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        High-precision unified semantic parser & AI intent interpretation layer:
        1. Checks for casual conversation without desktop action.
        2. Executes fast deterministic multi-step compound intent pipeline for sequential actions.
        3. Executes fast deterministic single clause atomic command resolution.
        4. If local parser does not match and an external AI provider is active:
           delegates natural-language reasoning to the active AI provider (Gemini, Claude, ChatGPT, Kimi, DeepSeek, Qwen),
           normalizing the result into validated supported deterministic tool actions.
        5. Falls back to built-in conversational assistance if built-in or if AI fails.
        """
        raw_text = text.strip()

        # Step 1: Casual / Conversational Dialogue Check
        conv_reply = self._handle_conversational_response(raw_text, conversation_context=conversation_context, attachments=attachments)
        if conv_reply:
            return {
                "summary": "Conversational Dialogue",
                "reasoning": f"Processed conversational query ({self.providers[self.active_provider].display_name}). No desktop tools executed.",
                "actions": [],
                "safety_level": "safe",
                "confirmation_required": False,
                "response": conv_reply
            }

        # Step 2: Multi-step Compound Command Pipeline (Deterministic Priority)
        compound_plan = self._parse_compound_command(raw_text, workspace)
        if compound_plan and compound_plan.get("actions"):
            return compound_plan

        # Step 3: Single Intent Resolution (Deterministic Desktop Automation)
        single_res = self._parse_single_clause(raw_text, context={}, workspace=workspace)
        if single_res and single_res.get("action"):
            act = single_res["action"]
            safety_level = single_res.get("safety_level", "safe")
            conf_req = (safety_level == "dangerous")
            conf_payload = single_res.get("confirmation_payload")

            tool_name = act.get("tool")
            summary = single_res.get("summary", act.get("description", "Execute action"))
            resp = self._format_action_response(act, summary)

            return {
                "summary": summary,
                "reasoning": f"Parsed atomic intent into tool '{tool_name}'.",
                "actions": [act],
                "safety_level": safety_level,
                "confirmation_required": conf_req,
                "confirmation_payload": conf_payload,
                "response": resp
            }

        # Step 4: Active AI Provider Natural-Language Intent Reasoning (when local parser does not recognize)
        if self.active_provider != "builtin":
            ai_raw_output, telemetry = self._query_ai_for_intent(raw_text, workspace, conversation_context=conversation_context, attachments=attachments)
            if telemetry.get("request_failed"):
                # Provider failed: return provider unavailable message
                return {
                    "summary": f"{telemetry.get('active_provider_name', 'AI')} Unavailable",
                    "reasoning": f"Active AI provider {telemetry.get('active_provider_name')} failed to respond.",
                    "actions": [],
                    "safety_level": "safe",
                    "confirmation_required": False,
                    "response": ai_raw_output or f"{telemetry.get('active_provider_name', 'AI')} is currently unavailable."
                }
            
            if ai_raw_output:
                ai_plan = self._validate_and_normalize_ai_plan(ai_raw_output, raw_text, workspace)
                if ai_plan:
                    return ai_plan

                # If not JSON, treat as conversational response from AI
                return {
                    "summary": f"{telemetry.get('active_provider_name', 'AI')} Response",
                    "reasoning": f"Query interpreted by active provider {telemetry.get('active_provider_name')}.",
                    "actions": [],
                    "safety_level": "safe",
                    "confirmation_required": False,
                    "response": ai_raw_output
                }

        # Step 5: General Assistance Fallback for Built-in Engine (when no external AI is configured)
        if attachments:
            att_responses = []
            for att in attachments:
                att_name = att.get("filename", "file")
                att_cat = att.get("category", "text")
                att_size = att.get("size_formatted", "")
                att_id = att.get("id")

                if att_cat in ["text", "code", "document"]:
                    file_txt = self.attachment_manager.read_attachment_text(att_id, max_chars=1200)
                    line_count = len(file_txt.splitlines()) if file_txt else 0
                    preview_snip = file_txt[:350].strip() if file_txt else "Empty content"
                    att_responses.append(f"I've received and inspected **{att_name}** ({att_size}, {line_count} lines).\n\nContent preview:\n```{att.get('extension', '').lstrip('.')}\n{preview_snip}\n```")
                elif att_cat == "image":
                    att_responses.append(f"I received your image **{att_name}** ({att_size}). For visual object recognition and image understanding, connect a Gemini API key in Settings!")
            if att_responses:
                return {
                    "summary": "Attachment Inspection",
                    "reasoning": "Inspected attached file in built-in mode.",
                    "actions": [],
                    "safety_level": "safe",
                    "confirmation_required": False,
                    "response": "\n\n".join(att_responses)
                }

        is_hinglish = any(k in raw_text.lower() for k in ["bhai", "kya", "hai", "karo", "kar", "de", "khol", "chala", "bata", "kaise"])
        if is_hinglish:
            fallback_msg = ("Main desktop tasks to pura kar sakta hoon bhai (apps, files, games, web search...). "
                            "Lekin is detailed sawal ka jawab dene ke liye mujhe Gemini/Claude AI key chahiye — "
                            "Settings → AI Providers mein key daal de, phir main full answers dunga! 😄")
        else:
            fallback_msg = ("I can handle all your desktop tasks — opening apps, creating files, building games, "
                            "web search, and more. For detailed answers to questions like this, add a Gemini API key "
                            "in Settings → AI Providers, and I'll give you full, intelligent responses!")

        return {
            "summary": "General Assistance",
            "reasoning": "Input understood as general assistance query without direct computer control instruction.",
            "actions": [],
            "safety_level": "safe",
            "confirmation_required": False,
            "response": fallback_msg
        }
