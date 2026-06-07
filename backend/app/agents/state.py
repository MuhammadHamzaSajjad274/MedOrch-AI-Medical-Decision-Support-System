"""LangGraph AgentState TypedDict."""
from typing import TypedDict

from langchain_core.messages import BaseMessage

from app.models.schemas import VisionResult


class AgentState(TypedDict, total=False):
    """State passed through the graph."""

    messages: list[BaseMessage]
    base64_image: str | None
    modality: str | None
    retrieved_docs: list[dict]
    next_step: str
    vision_result: VisionResult | None
    diagnosis_result: dict | None
    requires_research: bool
    research_query: str | None
    patient_context: str | None
