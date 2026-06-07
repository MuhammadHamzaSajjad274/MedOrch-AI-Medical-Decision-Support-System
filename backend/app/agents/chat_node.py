"""Chat node: medical LLM with full conversation history; doctor-like system prompt."""
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.prompts import get_doctor_system_prompt
from app.agents.state import AgentState


def _last_user_text(state: AgentState) -> str:
    messages = state.get("messages") or []
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            c: Any = getattr(m, "content", "") or ""
            if isinstance(c, str):
                return c
            if isinstance(c, list):
                return " ".join(
                    p.get("text", "") for p in c if isinstance(p, dict) and "text" in p
                )
    return ""


def _is_image_sharing_intent(text: str) -> bool:
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


def chat_node(state: AgentState) -> AgentState:
    """General chat via medical LLM with full message history; append AIMessage."""
    messages = state.get("messages") or []

    # Deterministic, friendly response for image-intent prompts without an attached image.
    # This avoids dead-ends and keeps UX conversational.
    last_user = _last_user_text(state)
    if not state.get("base64_image") and _is_image_sharing_intent(last_user):
        modality = state.get("modality")
        if modality == "brain_mri":
            modality_hint = "Brain MRI"
        elif modality == "chest_xray":
            modality_hint = "Chest X-ray"
        elif modality == "skin_lesion":
            modality_hint = "Skin Lesion"
        else:
            modality_hint = None
        if modality_hint:
            reply = (
                f"Yes, you can upload it. Please share a clear {modality_hint} image and I can analyze it. "
                "If possible, include the area you are most concerned about."
            )
        else:
            reply = (
                "Yes, you can upload the image and I can analyze it. "
                "Please select the correct modality first (Brain MRI, Chest X-ray, or Skin Lesion), "
                "then upload a clear image."
            )
        return {**state, "messages": messages + [AIMessage(content=reply)]}

    llm = get_llm()
    patient_context = state.get("patient_context")
    system = get_doctor_system_prompt(patient_context)
    # Full conversation history so the model can ask follow-ups and refer back
    chain = [SystemMessage(content=system)] + list(messages)
    try:
        out = llm.invoke(chain)
        reply = out.content if hasattr(out, "content") else str(out)
    except Exception:
        reply = "I could not generate a response. Please try again."
    return {**state, "messages": messages + [AIMessage(content=reply)]}
