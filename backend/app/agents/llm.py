"""Medical LLM client (Mistral-7B fine-tuned, OpenAI-compatible API)."""
from __future__ import annotations

from langchain_openai import ChatOpenAI

from app.core.config import get_settings

_settings = get_settings()
_llm: ChatOpenAI | None = None


def get_llm(model: str | None = None) -> ChatOpenAI:
    """
    Lazy LLM client for local or hosted Mistral inference.

    Compatible with:
    - Ollama: LLM_BASE_URL=http://localhost:11434/v1
    - vLLM / TGI: LLM_BASE_URL=http://localhost:8001/v1
  - Hosted OpenAI-compatible APIs
    """
    global _llm
    if _llm is None:
        _llm = ChatOpenAI(
            model=model or _settings.LLM_MODEL,
            api_key=_settings.LLM_API_KEY or "not-needed",
            base_url=_settings.LLM_BASE_URL,
            temperature=_settings.LLM_TEMPERATURE,
            max_tokens=_settings.LLM_MAX_TOKENS,
        )
    return _llm
