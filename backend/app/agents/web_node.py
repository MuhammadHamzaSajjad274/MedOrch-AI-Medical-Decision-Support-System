"""Web node: Tavily + medical LLM with full history; doctor-like prompt; mention sources."""
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.prompts import get_web_system_prompt
from app.agents.state import AgentState
from app.core.config import get_settings


def _last_user_text(state: AgentState) -> str:
    messages = state.get("messages") or []
    for m in reversed(messages):
        if isinstance(m, HumanMessage):
            c = getattr(m, "content", "") or ""
            if isinstance(c, str):
                return c
            if isinstance(c, list):
                return " ".join(
                    p.get("text", "") for p in c if isinstance(p, dict) and "text" in p
                )
    return ""


def _tavily_search(query: str, max_results: int = 3) -> list[dict]:
    try:
        from tavily import TavilyClient
        key = get_settings().TAVILY_API_KEY
        if not key:
            return []
        client = TavilyClient(api_key=key)
        r = client.search(query, max_results=max_results)
        return [
            {"title": x.get("title", ""), "url": x.get("url", ""), "content": x.get("content", "")}
            for x in (r.get("results") or [])
        ]
    except Exception:
        return []


def web_node(state: AgentState) -> AgentState:
    """Search web, then medical LLM with full history; append AIMessage."""
    query = _last_user_text(state)
    results = _tavily_search(query)
    messages = state.get("messages") or []
    if not results:
        context = "No web results. Answer briefly from general knowledge."
    else:
        context = "\n\n".join(
            f"- {r.get('title', '')}: {r.get('content', '')} (URL: {r.get('url', '')})"
            for r in results
        )
    llm = get_llm()
    patient_context = state.get("patient_context")
    system = get_web_system_prompt(patient_context)
    context_block = f"Search results for the user's latest question:\n{context}"
    chain = (
        [SystemMessage(content=system)]
        + list(messages)
        + [HumanMessage(content=context_block)]
    )
    try:
        out = llm.invoke(chain)
        reply = out.content if hasattr(out, "content") else str(out)
    except Exception:
        reply = "I could not complete the search. Please try again."
    return {**state, "messages": messages + [AIMessage(content=reply)]}
