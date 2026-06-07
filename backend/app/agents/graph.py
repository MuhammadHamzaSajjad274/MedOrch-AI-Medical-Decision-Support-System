"""LangGraph: guardrail -> router -> (vision | rag | web | chat) -> response."""
from langgraph.graph import END, StateGraph

from app.agents.state import AgentState
from app.agents.guardrail_node import guardrail_node
from app.agents.router_node import router_node
from app.agents.vision_node import vision_node
from app.agents.rag_node import rag_node
from app.agents.web_node import web_node
from app.agents.chat_node import chat_node
from app.agents.response_node import response_node


def route_after_router(state: AgentState) -> str:
    """From router: vision | rag | web | chat; blocked -> response with block message."""
    step = state.get("next_step") or "chat"
    if step == "blocked":
        return "response"
    return step


def route_after_vision(state: AgentState) -> str:
    """After vision: if requires_research -> rag, else -> response."""
    if state.get("requires_research"):
        return "rag"
    return "response"


def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)
    graph.add_node("guardrail", guardrail_node)
    graph.add_node("router", router_node)
    graph.add_node("vision", vision_node)
    graph.add_node("rag", rag_node)
    graph.add_node("web", web_node)
    graph.add_node("chat", chat_node)
    graph.add_node("response", response_node)

    graph.set_entry_point("guardrail")
    graph.add_edge("guardrail", "router")
    graph.add_conditional_edges("router", route_after_router)
    graph.add_conditional_edges(
        "vision", route_after_vision, {"rag": "rag", "response": "response"}
    )
    graph.add_edge("rag", "response")
    graph.add_edge("web", "response")
    graph.add_edge("chat", "response")
    graph.add_edge("response", END)

    return graph


def get_graph():
    """Compiled graph."""
    return build_graph().compile()
