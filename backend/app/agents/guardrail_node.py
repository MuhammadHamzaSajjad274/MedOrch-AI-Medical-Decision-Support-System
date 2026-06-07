"""Guardrail: validate input, block unsafe or crisis prompts."""
from langchain_core.messages import AIMessage

from app.agents.state import AgentState


BLOCKED_PATTERNS = [
    # Harm and violence
    "dangerous chemical",
    "make explosives",
    "how to harm",
    "kill someone",
    "poison someone",
    "illegal drug synthesis",
    # Self-harm / suicide
    "kill myself",
    "suicide",
    "commit suicide",
    "end my life",
    "hurt myself",
    "self harm",
    "self-harm",
    # Drug misuse / overdose
    "how much should i take to overdose",
    "overdose on",
]

SELF_HARM_KEYWORDS = [
    "kill myself",
    "suicide",
    "commit suicide",
    "end my life",
    "hurt myself",
    "self harm",
    "self-harm",
]


def guardrail_node(state: AgentState) -> AgentState:
    """Validate and set next_step to blocked or continue."""
    messages = state.get("messages") or []
    if not messages:
        return {**state, "next_step": "continue"}
    last = messages[-1]
    content = getattr(last, "content", "") or ""
    if isinstance(content, list):
        text = " ".join(
            p.get("text", "") for p in content if isinstance(p, dict) and "text" in p
        )
    else:
        text = str(content)
    lowered = text.lower()

    # Self-harm / crisis handling
    if any(k in lowered for k in SELF_HARM_KEYWORDS):
        crisis_msg = AIMessage(
            content=(
                "I'm really sorry that you're feeling this way. I can't provide the help you "
                "deserve in a crisis, but you are not alone.\n\n"
                "If you are in immediate danger or think you might hurt yourself, please contact "
                "your local emergency number right away, or reach out to a crisis hotline or a "
                "trusted person near you.\n\n"
                "You deserve support from trained professionals who can help you in this moment."
            )
        )
        return {
            **state,
            "next_step": "blocked",
            "messages": list(messages) + [crisis_msg],
        }

    # Other unsafe requests (violence, illegal advice, etc.)
    for p in BLOCKED_PATTERNS:
        if p in lowered:
            blocked_msg = AIMessage(
                content=(
                    "I can't help with that. I'm here for general health information and support. "
                    "If you have a medical concern or are worried about your safety or someone "
                    "else's, please speak to a healthcare provider or contact emergency services."
                )
            )
            return {
                **state,
                "next_step": "blocked",
                "messages": list(messages) + [blocked_msg],
            }

    return {**state, "next_step": "continue"}

