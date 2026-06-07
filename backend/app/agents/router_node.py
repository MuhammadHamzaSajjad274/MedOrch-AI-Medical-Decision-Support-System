"""Agentic controller: decide next_step = vision | rag | web | chat."""
from __future__ import annotations

import json
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.state import AgentState


CONTROLLER_SYSTEM_PROMPT = """
You are the controller agent for a medical assistant system.

Your ONLY job is to decide which specialist tool to call next.
You never answer the user's question directly.

Available tools:
- "vision": analyze an uploaded medical image when both base64_image and modality
  (one of "brain_mri", "chest_xray", "skin_lesion") are present.
- "rag": consult curated medical documents and guidelines (the RAG corpus).
- "web": search the web for the latest medical information.
- "chat": general medical conversation and reasoning using existing context only.

Guidelines:
- If the state indicates the conversation is blocked for safety, keep next_step as "blocked".
- If an image and modality are present and vision has not yet run, choose "vision".
- After vision, if requires_research is true, prefer "rag".
- If the user explicitly asks for "latest", "recent", "new study", "recent guideline",
  or similar, prefer "web".
- For most clinical questions that refer to conditions, treatments, or guidelines,
  prefer "rag" first, then "chat".
- If nothing matches strongly, default to "rag".

Respond ONLY with a compact JSON object on a single line, e.g.:
{"next_step": "rag", "reason": "User asked about management guidelines"}
"""


def _last_user_text(state: AgentState) -> str:
    """Extract last human message text for routing context."""
    messages = state.get("messages") or []
    for m in reversed(messages):
        # LangChain HumanMessage type name check without importing it directly
        if m.__class__.__name__ == "HumanMessage":
            content: Any = getattr(m, "content", "") or ""
            if isinstance(content, str):
                return content
            if isinstance(content, list):
                return " ".join(
                    p.get("text", "")
                    for p in content
                    if isinstance(p, dict) and "text" in p
                )
    return ""


def _is_image_sharing_intent(text: str) -> bool:
    """Detect requests like share/upload image or asking model to scan image before upload."""
    t = (text or "").lower()
    share_words = ("share", "upload", "send", "attach", "give", "provide", "show")
    analysis_words = ("scan", "analyze", "analyse", "interpret", "read", "review", "check", "look at")
    image_words = (
        "image",
        "scan",
        "mri",
        "xray",
        "x-ray",
        "chest xray",
        "chest x-ray",
        "photo",
        "pic",
        "picture",
    )
    has_image_ref = any(w in t for w in image_words)
    return has_image_ref and (
        any(w in t for w in share_words) or any(w in t for w in analysis_words)
    )


def router_node(state: AgentState) -> AgentState:
    """Agentic controller: call LLM to decide which tool to run next."""
    # Respect prior safety decision
    if state.get("next_step") == "blocked":
        return state

    base64_image = state.get("base64_image")
    modality = state.get("modality")
    has_vision_result = state.get("vision_result") is not None
    requires_research = bool(state.get("requires_research"))
    last_user = _last_user_text(state)

    summary = {
        "has_image": bool(base64_image),
        "modality": modality,
        "has_vision_result": has_vision_result,
        "requires_research": requires_research,
        "last_user_message": last_user,
    }

    # If user asks to share/upload/scan an image but no image is attached yet,
    # always route to chat for an affirmative upload instruction.
    if not summary["has_image"] and _is_image_sharing_intent(last_user):
        return {**state, "next_step": "chat"}

    # Fast path: clear image+modality and vision not yet run
    if summary["has_image"] and summary["modality"] and not summary["has_vision_result"]:
        return {**state, "next_step": "vision"}

    llm = get_llm()
    messages = [
        SystemMessage(content=CONTROLLER_SYSTEM_PROMPT),
        HumanMessage(content=f"Current state summary:\n{json.dumps(summary)}"),
    ]

    next_step = "rag"
    try:
        out = llm.invoke(messages)
        raw = out.content if hasattr(out, "content") else str(out)
        data = json.loads(raw) if raw else {}
        candidate = str(data.get("next_step", "")).strip().lower()
        if candidate in {"vision", "rag", "web", "chat", "blocked"}:
            next_step = candidate
    except Exception:
        # Fallback: heuristic similar to previous router
        text_lower = (last_user or "").lower()
        if any(k in text_lower for k in ("document", "pdf", "ingested", "according to")):
            next_step = "rag"
        elif any(k in text_lower for k in ("search", "latest", "recent", "pubmed")):
            next_step = "web"
        else:
            next_step = "rag"

    # Safety guard: never route to vision unless an image is actually present.
    if next_step == "vision" and not summary["has_image"]:
        next_step = "chat"

    return {**state, "next_step": next_step}

