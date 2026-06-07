"""Response node: format final message (vision result + citations)."""
from app.agents.state import AgentState


def response_node(state: AgentState) -> AgentState:
    """Pass through; API layer will read messages + vision_result + retrieved_docs."""
    return state
