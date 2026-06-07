"""RAG node: retrieve + medical LLM with full history; doctor-like prompt; cite sources."""
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.llm import get_llm
from app.agents.prompts import get_rag_system_prompt
from app.agents.state import AgentState
from app.services.rag.retriever import retrieve


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


def rag_node(state: AgentState) -> AgentState:
    """Retrieve top-k, then medical LLM with full history and context; append AIMessage."""
    query = state.get("research_query") or _last_user_text(state)
    docs = retrieve(query, k=5)
    state = {**state, "retrieved_docs": docs}
    messages = state.get("messages") or []
    if not docs:
        context = "No retrieved documents. Answer briefly from general knowledge."
    else:
        context = "\n\n".join(
            f"[{i+1}] {d.get('text', '')} (source: {d.get('source', '')})"
            for i, d in enumerate(docs)
        )
    llm = get_llm()
    patient_context = state.get("patient_context")
    system = get_rag_system_prompt(patient_context)
    vision_result = state.get("vision_result")
    # If we already ran vision, anchor the RAG answer to that finding so the LLM
    # does not "forget" the image analysis and incorrectly claim no image was provided.
    if vision_result is not None:
        modality = getattr(vision_result, "modality", "unknown")
        label = getattr(vision_result, "label", "unknown")
        confidence = float(getattr(vision_result, "confidence", 0.0))
        context_block = (
            "An image has already been analyzed by the vision model.\n"
            f"Vision finding: modality={modality}, label={label}, confidence={confidence:.1%}.\n"
            "Use this finding as factual input and provide concise, evidence-based guidance.\n"
            "Do NOT say that you cannot see the image.\n\n"
            f"Retrieved medical context:\n{context}"
        )
    else:
        # Full history + RAG context for the latest question (question already in messages)
        context_block = f"Context for the user's latest question:\n{context}"
    chain = (
        [SystemMessage(content=system)]
        + list(messages)
        + [HumanMessage(content=context_block)]
    )
    try:
        out = llm.invoke(chain)
        reply = out.content if hasattr(out, "content") else str(out)
    except Exception:
        reply = "I couldn't generate a response. Please try again."
    return {**state, "messages": messages + [AIMessage(content=reply)]}
