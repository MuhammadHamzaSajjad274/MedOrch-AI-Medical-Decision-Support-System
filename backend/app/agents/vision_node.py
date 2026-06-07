"""Vision node: call VisionService, then LLM for doctor-like explanation."""
import base64
import logging

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.prompts import get_vision_explanation_prompt
from app.agents.state import AgentState
from app.agents.vision_config import (
    build_research_query,
    is_actionable,
)
from app.services.vision.vision_service import analyze


logger = logging.getLogger(__name__)


def _doctor_like_summary(result, patient_context: str | None = None) -> str:
    """Get a short doctor-like explanation via LLM; fallback to template if LLM fails."""
    modality_label = result.modality.replace("_", " ").title()
    user_msg = (
        f"The imaging analysis ({modality_label}) suggests: {result.label} "
        f"(confidence: {result.confidence:.1%}). "
        f"Explain this in one short, empathetic paragraph for the patient."
    )
    try:
        llm = get_llm()
        chain = [
            SystemMessage(content=get_vision_explanation_prompt(patient_context)),
            HumanMessage(content=user_msg),
        ]
        out = llm.invoke(chain)
        return out.content if hasattr(out, "content") else str(out)
    except Exception:
        return (
            f"Based on the {modality_label} image, the reading suggests {result.label} "
            f"(confidence: {result.confidence:.1%}). This is not a diagnosis. "
            "Please discuss the result and any formal report with your doctor."
        )


def vision_node(state: AgentState) -> AgentState:
    """Run vision for image + modality; set vision_result and append doctor-like message."""
    base64_image = state.get("base64_image")
    modality = state.get("modality")
    messages = state.get("messages") or []
    if not base64_image or not modality:
        return {
            **state,
            "vision_result": None,
            "requires_research": False,
        }
    try:
        raw = base64.b64decode(base64_image, validate=True)
        result = analyze(raw, modality)
        summary = _doctor_like_summary(result, state.get("patient_context"))
        diagnosis_result = {
            "modality": result.modality,
            "label": result.label,
            "confidence": result.confidence,
        }
        requires_research = is_actionable(
            result.modality, result.label, result.confidence
        )
        research_query = (
            build_research_query(result.modality, result.label)
            if requires_research
            else None
        )
        return {
            **state,
            "vision_result": result,
            "diagnosis_result": diagnosis_result,
            "requires_research": requires_research,
            "research_query": research_query,
            "messages": messages + [AIMessage(content=summary)],
        }
    except Exception:
        # Log full traceback so we can debug why vision is failing.
        logger.exception("Vision node failed for modality %s", modality)
        # Also append a fallback message instead of returning an empty response.
        fallback = (
            "I had trouble analyzing this image for that modality. "
            "Please make sure you uploaded a clear JPEG/PNG of the right type and try again."
        )
        return {
            **state,
            "vision_result": None,
            "diagnosis_result": None,
            "requires_research": False,
            "research_query": None,
            "messages": messages + [AIMessage(content=fallback)],
        }
