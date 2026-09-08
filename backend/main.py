"""
FastAPI Main Application for Zevion
Provides REST endpoints for real-time Windows control,
intelligent chat reasoning, universal application launching, AI Provider Management, and safety guardrails.
"""

import os
import sys
import time
import asyncio
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse

from ai_brain import (
    AIBrain,
    MAX_ATTACHMENTS_PER_MESSAGE,
    MAX_ATTACHMENT_SIZE_MB,
    MAX_TOTAL_ATTACHMENT_SIZE_MB,
    MAX_ATTACHMENT_SIZE_BYTES,
    MAX_TOTAL_ATTACHMENT_SIZE_BYTES,
    SUPPORTED_EXTENSIONS,
    format_file_size
)
from desktop_controller import DesktopController
from safety_guard import SafetyGuard

app = FastAPI(
    title="Zevion API",
    description="Zevion — Next-Generation AI Desktop Copilot & Provider Management System",
    version="2.0.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Initialize singletons
brain = AIBrain()
controller = DesktopController()
safety = SafetyGuard(mode=brain.safety_mode)

# Pydantic Request Models
class ChatRequest(BaseModel):
    message: str = ""
    auto_execute_safe: bool = True
    conversation_id: Optional[str] = None
    attachments: Optional[List[Dict[str, Any]]] = []

class CreateConversationRequest(BaseModel):
    title: Optional[str] = "New Chat"

class RenameConversationRequest(BaseModel):
    title: str

class ConfirmActionRequest(BaseModel):
    token_id: str
    approved: bool

class DirectToolRequest(BaseModel):
    tool: str
    parameters: Dict[str, Any]

class PlanApproveRequest(BaseModel):
    plan_token: str
    approved: bool

class MemoryCreateRequest(BaseModel):
    key: str
    value: str
    text: Optional[str] = None

class MemoryToggleRequest(BaseModel):
    enabled: bool

class OnboardingRequest(BaseModel):
    api_key: Optional[str] = ""
    skip: bool = False

class ProviderKeyRequest(BaseModel):
    provider_id: str
    api_key: Optional[str] = ""
    enabled: bool = True

class ActiveProviderRequest(BaseModel):
    provider_id: str

class SettingsUpdateRequest(BaseModel):
    active_provider: Optional[str] = None
    provider: Optional[str] = None
    api_key: Optional[str] = None
    safety_mode: Optional[str] = None
    dry_run: Optional[bool] = None
    plan_mode: Optional[bool] = None
    onboarding_completed: Optional[bool] = None

@app.get("/")
def read_root():
    return {
        "status": "online",
        "service": "Zevion Automation Backend",
        "version": "2.0.0",
        "os": controller.os_type,
        "installed_apps_count": len(controller.app_registry_cache),
        "onboarding_completed": brain.onboarding_completed,
        "active_provider": brain.active_provider
    }

@app.get("/api/conversations")
def get_conversations():
    """
    Returns list of saved conversation summaries.
    """
    return {
        "conversations": brain.list_conversations(),
        "active_conversation_id": brain.active_conversation_id
    }

@app.post("/api/conversations")
def create_conversation_endpoint(req: CreateConversationRequest):
    """
    Creates a new conversation session.
    """
    conv = brain.create_conversation(title=req.title or "New Chat")
    return {"success": True, "conversation": conv}

@app.get("/api/conversations/{conv_id}")
def get_conversation_endpoint(conv_id: str):
    """
    Returns full conversation with messages.
    """
    conv = brain.get_conversation(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"success": True, "conversation": conv}

@app.put("/api/conversations/{conv_id}")
def rename_conversation_endpoint(conv_id: str, req: RenameConversationRequest):
    """
    Renames a conversation.
    """
    ok = brain.rename_conversation(conv_id, req.title)
    if not ok:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return {"success": True, "message": "Conversation renamed successfully."}

@app.delete("/api/conversations/{conv_id}")
def delete_conversation_endpoint(conv_id: str):
    """
    Deletes a conversation.
    """
    ok = brain.delete_conversation(conv_id)
    return {"success": ok, "message": "Conversation deleted."}

@app.post("/api/chat/stop")
def stop_chat_endpoint():
    """
    Signals cancellation / stop of in-flight generation.
    """
    return {"status": "stopped", "message": "Generation stopped by user."}

@app.get("/api/memory")
def get_memories_endpoint():
    """
    Returns Level 2 primary / global persistent memories.
    """
    return {
        "enabled": brain.memory_manager.enabled,
        "memories": brain.memory_manager.list_memories(),
        "count": len(brain.memory_manager.list_memories())
    }

@app.post("/api/memory")
def add_memory_endpoint(req: MemoryCreateRequest):
    """
    Saves a persistent memory across conversations.
    """
    mem = brain.memory_manager.add_memory(req.key, req.value, req.text or f"{req.key}: {req.value}")
    return {"success": True, "memory": mem}

@app.delete("/api/memory/{memory_id}")
def delete_memory_endpoint(memory_id: str):
    """
    Deletes an individual persistent memory.
    """
    ok = brain.memory_manager.delete_memory(memory_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Memory not found.")
    return {"success": True, "message": "Memory deleted."}

@app.delete("/api/memory")
def clear_memories_endpoint():
    """
    Clears all persistent global memories.
    """
    brain.memory_manager.clear_memories()
    return {"success": True, "message": "All memories cleared."}

@app.post("/api/memory/toggle")
def toggle_memory_endpoint(req: MemoryToggleRequest):
    """
    Toggles global memory enabled / disabled.
    """
    brain.memory_manager.enabled = req.enabled
    brain.memory_manager._save_memory()
    return {"success": True, "enabled": brain.memory_manager.enabled}

@app.get("/api/attachments/config")
def get_attachment_config():
    """
    Returns attachment limits, rolling rate-limit status, and supported file types.
    """
    rl_status = brain.attachment_manager.get_rate_limit_status()
    return {
        "max_attachments": MAX_ATTACHMENTS_PER_MESSAGE,
        "max_size_mb": MAX_ATTACHMENT_SIZE_MB,
        "max_total_size_mb": MAX_TOTAL_ATTACHMENT_SIZE_MB,
        "max_size_bytes": MAX_ATTACHMENT_SIZE_BYTES,
        "max_total_size_bytes": MAX_TOTAL_ATTACHMENT_SIZE_BYTES,
        "rate_limit_count": 20,
        "rate_limit_window_seconds": 600,
        "current_used": rl_status["current_used"],
        "remaining_slots": rl_status["remaining_slots"],
        "cooldown_remaining_seconds": rl_status["cooldown_remaining_seconds"],
        "next_reset_timestamp": rl_status["next_reset_timestamp"],
        "supported_extensions": sorted(list(SUPPORTED_EXTENSIONS))
    }

@app.post("/api/attachments/upload")
async def upload_attachments_endpoint(files: List[UploadFile] = File(...)):
    """
    Validates and securely saves uploaded file attachments with rolling rate limit enforcement.
    Returns safe metadata array for frontend display and chat messaging.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    if len(files) > MAX_ATTACHMENTS_PER_MESSAGE:
        raise HTTPException(status_code=400, detail=f"You can attach at most {MAX_ATTACHMENTS_PER_MESSAGE} files per message.")

    # Validate rolling rate limit before reading large data
    ok_rl, err_rl, rl_status = brain.attachment_manager.validate_rate_limit(len(files))
    if not ok_rl:
        raise HTTPException(status_code=400, detail=err_rl)

    read_files = []
    for f in files:
        content = await f.read()
        read_files.append((f.filename or "unknown", content, f.content_type))

    batch_info = [(fname, len(cnt)) for fname, cnt, _ in read_files]
    ok, err = brain.attachment_manager.validate_batch(batch_info)
    if not ok:
        raise HTTPException(status_code=400, detail=err)

    saved_attachments = []
    for fname, cnt, mime in read_files:
        try:
            meta = brain.attachment_manager.save_attachment(fname, cnt, mime)
            saved_attachments.append(meta)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Record successful upload count towards rate limit rolling window
    brain.attachment_manager.record_successful_uploads(len(saved_attachments))

    return {
        "success": True,
        "attachments": saved_attachments,
        "count": len(saved_attachments),
        "rate_limit": brain.attachment_manager.get_rate_limit_status()
    }

@app.get("/api/attachments/{attachment_id}")
def get_attachment_endpoint(attachment_id: str):
    """
    Serves stored attachment file safely with proper content-type headers.
    """
    meta = brain.attachment_manager.get_attachment_metadata(attachment_id)
    path = brain.attachment_manager.get_attachment_path(attachment_id)
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Attachment not found.")
    
    media_type = meta.get("mime_type", "application/octet-stream") if meta else "application/octet-stream"
    filename = meta.get("filename", os.path.basename(path)) if meta else os.path.basename(path)
    return FileResponse(path, media_type=media_type, filename=filename)

@app.delete("/api/attachments/{attachment_id}")
def delete_attachment_endpoint(attachment_id: str):
    """
    Deletes an attachment file and its metadata.
    """
    ok = brain.attachment_manager.delete_attachment(attachment_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Attachment not found or already deleted.")
    return {"success": True, "message": "Attachment deleted."}

@app.post("/api/chat")
async def process_chat(req: ChatRequest):
    """
    Core AI Chat endpoint:
    1. AI Brain parses intent and creates plan + safety rating using active AI provider.
    2. Supports multimodal image, code, text, and PDF attachments.
    3. If actions are safe and auto_execute_safe is True, executes immediately.
    4. If action is dangerous, generates confirmation token.
    5. Saves user and assistant messages to persistent conversation history.
    6. Returns thoughts, actions with execution results, and natural response.
    """
    user_msg_text = (req.message or "").strip()
    user_attachments = req.attachments or []
    if not user_msg_text and not user_attachments:
        raise HTTPException(status_code=400, detail="Empty command message.")

    start_time = time.time()
    brain_result = brain.process_message(
        user_msg_text,
        current_workspace=str(controller.workspace_root),
        conversation_id=req.conversation_id,
        attachments=user_attachments
    )
    
    actions_to_execute = brain_result.get("actions", [])
    executed_results = []

    # PLAN-THEN-DO: when enabled and there are 2+ actions, hold execution and
    # require a single explicit approval before running the whole plan.
    if safety.plan_mode and len(actions_to_execute) >= 2:
        plan_token = f"plan_{int(time.time() * 1000)}"
        safety.pending_plans[plan_token] = {
            "actions": actions_to_execute,
            "created_at": time.time(),
            "expires_at": time.time() + 300
        }
        brain_result["plan_required"] = True
        brain_result["plan_token"] = plan_token
        plan_lines = [f"{i+1}. {a.get('description', a.get('tool'))}" for i, a in enumerate(actions_to_execute)]
        brain_result["response"] = "Here's my plan:\n" + "\n".join(plan_lines) + "\n\nApprove to run it?"
        brain_result["confirmation_required"] = True
        # Do not execute now; return the plan.
        brain_result["executed_results"] = []
        brain_result["total_latency_ms"] = round((time.time() - start_time) * 1000, 2)
        brain_result["active_windows"] = [controller.active_window_title]
        brain_result["mouse_position"] = controller.mouse_position
        return brain_result
    
    # Process actions sequentially with readiness waiting
    for i, act in enumerate(actions_to_execute):
        tool_name = act.get("tool")
        params = act.get("parameters", {})
        
        # DRY-RUN MODE: show the plan but never execute anything.
        if safety.dry_run:
            act["status"] = "dry_run"
            act["warning_message"] = "DRY-RUN: action planned but not executed."
            executed_results.append({
                "tool": tool_name,
                "status": "dry_run",
                "warning": "DRY-RUN: not executed."
            })
            if len(actions_to_execute) == 1:
                brain_result["response"] = f"(dry-run) I would execute: {tool_name} — but dry-run mode is on, so nothing was run."
            continue

        # Check safety guard
        risk_level, requires_approval, warning_msg = safety.evaluate_action(tool_name, params)
        act["risk_level"] = risk_level
        act["requires_approval"] = requires_approval

        # HARD BLOCKED: never execute, never create an approval token. Defense-in-depth.
        if risk_level == "blocked":
            act["status"] = "blocked"
            act["warning_message"] = warning_msg
            executed_results.append({
                "tool": tool_name,
                "status": "blocked",
                "warning": warning_msg
            })
            # Log the blocked attempt to the audit trail
            safety.log_execution(tool_name, params, {"success": False, "error": warning_msg}, "blocked", confirmed_by_user=False)
            if len(actions_to_execute) == 1:
                brain_result["response"] = f"\u26d4 {warning_msg}"
            continue

        if requires_approval and not brain_result.get("user_confirmed", False):
            # Create pending approval
            approval_req = safety.create_approval_request(tool_name, params, risk_level, warning_msg or "Dangerous action requires manual approval.")
            act["status"] = "pending_confirmation"
            act["approval_token"] = approval_req["token_id"]
            act["warning_message"] = warning_msg
            executed_results.append({
                "tool": tool_name,
                "status": "awaiting_user_approval",
                "approval_token": approval_req["token_id"],
                "warning": warning_msg
            })
        else:
            # Propagate target instance from previous new-window action in compound sequences
            if i > 0 and controller.last_new_window and controller.last_target_app:
                if tool_name == "type_text" and "target_hwnd" not in params:
                    params["target_hwnd"] = controller.last_target_hwnd
                    params["target_pid"] = controller.last_target_pid

            # Wait for previous action readiness if in a multi-step sequence
            if i > 0:
                prev_act = actions_to_execute[i - 1]
                controller._wait_for_action_readiness(prev_act.get("tool"), prev_act.get("parameters", {}))

            # Safe to execute immediately
            act["status"] = "executing"
            exec_res = controller.execute_action(tool_name, params)
            is_success = exec_res.get("success", True)
            act["status"] = "completed" if is_success else "failed"
            act["execution_result"] = exec_res
            executed_results.append(exec_res)
            
            # Log to safety audit (with sanitized parameters to prevent API key leaks)
            safety.log_execution(tool_name, params, exec_res, risk_level)

            # Update final user-facing response based on real execution result
            if len(actions_to_execute) == 1:
                if not is_success:
                    brain_result["response"] = exec_res.get("error") or exec_res.get("message") or f"Could not execute {tool_name}."
                else:
                    if tool_name == "open_application":
                        app_disp = exec_res.get("matched_app", params.get("app_name", "Application"))
                        brain_result["response"] = f"{app_disp} opened."
                    elif tool_name == "create_folder":
                        folder_disp = exec_res.get("folder_name", params.get("folder_path", "Folder"))
                        path_disp = exec_res.get("path", "")
                        brain_result["response"] = f"Folder **{folder_disp}** created at `{path_disp}`." if path_disp else f"Folder **{folder_disp}** created."
                    elif tool_name in ["create_file", "write_file"]:
                        file_disp = exec_res.get("filename", params.get("path", "file"))
                        path_disp = exec_res.get("path", "")
                        brain_result["response"] = f"File **{file_disp}** created at `{path_disp}`." if path_disp else f"File **{file_disp}** created."
                    elif tool_name == "create_project":
                        brain_result["response"] = exec_res.get("message") or f"Project **{exec_res.get('project_name')}** created at `{exec_res.get('path')}` with {exec_res.get('files_count', 0)} source files verified."
                    elif tool_name == "delete_file":
                        brain_result["response"] = exec_res.get("message") or f"Deleted {params.get('path')}."
            elif len(actions_to_execute) > 1:
                if all(r.get("success", False) for r in executed_results):
                    summaries = [r.get("message") or f"Executed {actions_to_execute[idx].get('tool')}" for idx, r in enumerate(executed_results)]
                    brain_result["response"] = "Successfully completed all requested actions:\n" + "\n".join(f"- {s}" for s in summaries)
                else:
                    failed_summaries = [r.get("error") or f"Failed {actions_to_execute[idx].get('tool')}" for idx, r in enumerate(executed_results) if not r.get("success", False)]
                    brain_result["response"] = "Some actions could not be completed:\n" + "\n".join(f"- {s}" for s in failed_summaries)

    # Persist message pair to active conversation
    user_msg_obj = {
        "id": f"msg_u_{int(start_time * 1000)}",
        "role": "user",
        "content": user_msg_text,
        "attachments": user_attachments,
        "timestamp": start_time
    }
    ai_msg_obj = {
        "id": brain_result.get("id") or f"msg_a_{int(time.time() * 1000)}",
        "role": "assistant",
        "content": brain_result.get("response", ""),
        "thoughts": brain_result.get("thoughts", []),
        "actions": brain_result.get("actions", []),
        "safety_level": brain_result.get("safety_level", "safe"),
        "confirmation_required": brain_result.get("confirmation_required", False),
        "confirmation_payload": brain_result.get("confirmation_payload", None),
        "timestamp": time.time()
    }
    conv_id = brain.add_message_pair_to_conversation(req.conversation_id, user_msg_obj, ai_msg_obj)
    brain_result["conversation_id"] = conv_id

    # Attach final execution summary
    brain_result["executed_results"] = executed_results
    brain_result["total_latency_ms"] = round((time.time() - start_time) * 1000, 2)
    brain_result["active_windows"] = [controller.active_window_title]
    brain_result["mouse_position"] = controller.mouse_position

    # Reflect any per-action approval requirement at the top level so the UI can
    # reliably show the confirmation modal (covers moderate shell commands too).
    any_pending = any(a.get("status") == "pending_confirmation" and a.get("approval_token") for a in actions_to_execute)
    if any_pending:
        brain_result["confirmation_required"] = True

    return brain_result

def execute_tool_internally(tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executes a tool on DesktopController and returns the structured result.
    """
    # Inject the configured Gemini API key for vision analysis so screenshot
    # analysis works through the normal Settings flow (not just env vars).
    if tool_name == "analyze_screenshot" and isinstance(parameters, dict) and not parameters.get("api_key"):
        gemini = brain.providers.get("gemini")
        key = (getattr(gemini, "api_key", "") or "").strip() if gemini else ""
        if key:
            parameters["api_key"] = key
    return controller.execute_action(tool_name, parameters)

@app.post("/api/plan/approve")
async def approve_plan(req: PlanApproveRequest):
    """
    Endpoint for Plan-Then-Do: user approves (or rejects) a multi-step plan.
    On approval, executes all held actions sequentially with safety checks.
    """
    plan = safety.pending_plans.get(req.plan_token)
    if not plan:
        raise HTTPException(status_code=400, detail="Invalid or expired plan token.")
    if time.time() > plan.get("expires_at", 0):
        safety.pending_plans.pop(req.plan_token, None)
        raise HTTPException(status_code=400, detail="Plan token expired.")
    safety.pending_plans.pop(req.plan_token, None)

    if not req.approved:
        return {"status": "plan_rejected", "message": "Plan cancelled by user."}

    results = []
    for act in plan["actions"]:
        tool_name = act.get("tool")
        params = act.get("parameters", {})
        risk_level, requires_approval, warning_msg = safety.evaluate_action(tool_name, params)
        if risk_level == "blocked":
            results.append({"tool": tool_name, "status": "blocked", "warning": warning_msg})
            continue
        if requires_approval:
            # Individual destructive steps still need their own confirmation.
            approval_req = safety.create_approval_request(tool_name, params, risk_level, warning_msg or "Requires approval.")
            results.append({"tool": tool_name, "status": "awaiting_user_approval", "approval_token": approval_req["token_id"], "warning": warning_msg})
            continue
        exec_res = execute_tool_internally(tool_name, params)
        safety.log_execution(tool_name, params, exec_res, risk_level)
        results.append({"tool": tool_name, "status": "completed" if exec_res.get("success", True) else "failed", "result": exec_res})

    return {
        "status": "plan_executed",
        "results": results,
        "message": f"Executed {len(results)} plan step(s)."
    }


@app.post("/api/action/confirm")
async def confirm_action(req: ConfirmActionRequest):
    """
    Endpoint called when user clicks 'Approve' or 'Deny' on a dangerous action dialog.
    """
    if req.approved:
        approval = safety.approve_request(req.token_id)
        if not approval:
            raise HTTPException(status_code=400, detail="Invalid or expired approval token.")
        
        tool_name = approval["tool_name"]
        params = approval["parameters"]

        # Defense-in-depth: refuse to execute HARD BLOCKED commands even if a
        # stale/invalid approval token somehow exists.
        if tool_name == "execute_command" and safety.is_hard_blocked(params.get("command", "")):
            return {
                "token_id": req.token_id,
                "status": "blocked",
                "result": {"success": False, "blocked": True, "error": "HARD BLOCKED command."},
                "message": "This command is hard blocked and can never be executed."
            }

        exec_res = execute_tool_internally(tool_name, params)
        safety.log_execution(tool_name, params, exec_res, approval["risk_level"], confirmed_by_user=True)
        
        return {
            "token_id": req.token_id,
            "status": "approved_and_executed",
            "result": exec_res,
            "message": f"Successfully authorized and executed {tool_name}."
        }
    else:
        safety.reject_request(req.token_id)
        return {
            "token_id": req.token_id,
            "status": "rejected_by_user",
            "message": "Action was safely cancelled by the user."
        }

@app.post("/api/action/execute")
async def direct_tool_execution(req: DirectToolRequest):
    """
    Direct tool test/invocation endpoint for UI buttons & workflows.
    """
    res = execute_tool_internally(req.tool, req.parameters)
    return res

@app.get("/api/apps")
def get_installed_applications():
    """
    Returns detected apps list.
    """
    return controller.get_installed_apps()

@app.get("/api/system")
def get_system_metrics():
    """
    Returns real-time system stats.
    """
    return controller.get_system_info()

@app.get("/api/system/status")
def get_system_status():
    """
    Returns real-time measured system status for periodic monitoring.
    """
    return controller.get_system_info()

@app.get("/api/system/diagnose")
def get_system_diagnose():
    """
    Returns real, safe, read-only PC diagnosis data.
    """
    return controller.get_pc_diagnosis()

@app.get("/api/files")
def get_workspace_files(path: str = ""):
    """
    Returns workspace directory listing.
    """
    return controller.list_files(path)

@app.get("/api/logs")
def get_action_audit_logs(limit: int = 50):
    """
    Returns sanitized action logs for the safety history.
    """
    return safety.get_audit_logs(limit)


@app.get("/api/export/conversation/{conv_id}")
def export_conversation(conv_id: str):
    """
    Exports a conversation as a Markdown document (downloadable .md).
    """
    conv = brain.conversations.get(conv_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    title = conv.get("title", "Conversation")
    lines = [f"# {title}", ""]
    for m in conv.get("messages", []):
        role = m.get("role", "unknown")
        content = str(m.get("content", "")).strip()
        if not content:
            continue
        if role == "user":
            lines.append(f"## 🙋 You\n\n{content}\n")
        else:
            lines.append(f"## 🤖 Zevion\n\n{content}\n")

    markdown = "\n".join(lines)
    return {
        "success": True,
        "filename": f"{title.replace(' ', '_')}.md",
        "content": markdown,
        "format": "markdown"
    }


@app.get("/api/export/audit")
def export_audit_log():
    """
    Exports the full safety audit log as a downloadable JSON / text file.
    """
    logs = safety.get_audit_logs(1000)
    text_lines = ["# Zevion Safety Audit Log", ""]
    for log in logs:
        text_lines.append(
            f"- [{log.get('timestamp', 0)}] {log.get('tool_name')} "
            f"(risk: {log.get('risk_level')}, confirmed: {log.get('confirmed_by_user')}) "
            f"-> {log.get('result_summary')}"
        )
    return {
        "success": True,
        "filename": "zevion_audit_log.md",
        "content": "\n".join(text_lines),
        "format": "markdown",
        "log_count": len(logs)
    }

@app.get("/api/settings")
def get_settings():
    """
    Returns safe settings with simple AI names ONLY (no technical model IDs or version strings).
    """
    settings = brain.get_settings()
    settings["safety_mode"] = safety.mode
    settings["dry_run"] = safety.dry_run
    settings["plan_mode"] = safety.plan_mode
    return settings


@app.get("/api/usage")
def get_usage():
    """
    Returns AI usage stats: today + last 7 days + per-provider breakdown.
    """
    return brain.get_usage_stats()

@app.get("/api/providers")
def get_providers():
    """
    Returns clean list of configured and available AI providers.
    """
    return {
        "active_provider": brain.active_provider,
        "providers": brain.get_providers_list(),
        "nvidia_choices": ["Kimi", "DeepSeek", "Qwen"]
    }

@app.post("/api/providers/active")
def set_active_provider(req: ActiveProviderRequest):
    """
    Switches the active AI provider.
    """
    res = brain.set_active_provider(req.provider_id)
    if not res.get("success", True):
        raise HTTPException(status_code=400, detail=res.get("error", "Cannot activate provider."))
    return res

@app.post("/api/providers/key")
def update_provider_key(req: ProviderKeyRequest):
    """
    Sets or updates an API key for a provider and configures its enablement.
    """
    clean_key = (req.api_key or "").strip()
    p_id = req.provider_id.lower().strip()
    
    # If key is empty and toggling enable/disable on an already configured provider:
    if not clean_key and p_id in brain.providers:
        provider = brain.providers[p_id]
        if provider.is_configured:
            res = brain.set_provider_enabled(p_id, req.enabled)
            return res

    res = brain.configure_provider(p_id, api_key=clean_key, enabled=req.enabled)
    return res

@app.delete("/api/providers/key")
def remove_provider_key(provider_id: str):
    """
    Removes an API key from a provider, automatically disabling it.
    """
    res = brain.remove_provider_key(provider_id)
    return res

@app.post("/api/onboarding")
def complete_onboarding_endpoint(req: OnboardingRequest):
    """
    First-launch onboarding endpoint:
    Connects Gemini if key provided or skips setup to run locally with zero API key.
    """
    res = brain.complete_onboarding(api_key=req.api_key, skip=req.skip)
    return res

@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    """
    Updates AI provider, Gemini/NVIDIA keys, active provider, and safety mode.
    """
    if req.active_provider:
        brain.set_active_provider(req.active_provider)
    elif req.provider:
        if req.api_key and req.api_key.strip():
            brain.configure_provider(req.provider, api_key=req.api_key.strip(), enabled=True)
        brain.set_active_provider(req.provider)
    
    if req.safety_mode:
        safety.set_mode(req.safety_mode)
        brain.set_safety_mode(req.safety_mode)
    if req.dry_run is not None:
        safety.set_dry_run(req.dry_run)
    if req.plan_mode is not None:
        safety.set_plan_mode(req.plan_mode)
    if req.onboarding_completed is not None:
        brain.onboarding_completed = req.onboarding_completed
    
    active_p = brain.providers.get(brain.active_provider, brain.providers["builtin"])
    return {
        "status": "updated",
        "active_provider": brain.active_provider,
        "active_provider_name": active_p.display_name,
        "safety_mode": safety.mode,
        "dry_run": safety.dry_run,
        "plan_mode": safety.plan_mode,
        "onboarding_completed": brain.onboarding_completed
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
