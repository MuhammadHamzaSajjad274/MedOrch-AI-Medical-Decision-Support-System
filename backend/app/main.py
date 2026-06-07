"""FastAPI application: health, reset, chat."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

# Load backend/.env into os.environ first (LLM_*, TAVILY_*, etc.)
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    try:
        from dotenv import load_dotenv
        load_dotenv(_env_path, override=True)
    except ImportError:
        pass

import asyncio
import json
import re
import uuid

from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response, StreamingResponse
from langchain_core.messages import HumanMessage
from sqlalchemy import select

from app.core.auth import decode_token
from app.core.config import get_settings
from app.core.logger import setup_logger
from app.db.database import async_session_factory, init_db
from app.db.models import Consultation, PatientProfile
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    Citation,
    HealthResponse,
    RAGStatusResponse,
    VisionResult,
)
from app.agents.graph import get_graph
from app.agents.state import AgentState
from app.services.rag.qdrant_client import COLLECTION_NAME, get_client
from app.routers import auth, profile, consultations, voice

logger = setup_logger(__name__)
settings = get_settings()

app = FastAPI(
    title="Medical Assistant API",
    description="Multi-Agent Medical Assistant backend",
    version="0.1.0",
)
app.include_router(auth.router)
app.include_router(profile.router)
app.include_router(consultations.router)
app.include_router(voice.router)


@app.on_event("startup")
async def startup_event():
    """Create DB tables on startup."""
    try:
        await init_db()
    except Exception as e:
        logger.warning("DB init skipped or failed: %s", e)

    if os.getenv("VOICE_WARMUP_ON_STARTUP", "true").lower() in {"1", "true", "yes"}:
        async def _warm_voice() -> None:
            try:
                await voice.voice_warmup()
                logger.info("Voice models warmed up")
            except Exception as e:
                logger.warning("Voice warmup skipped: %s", e)

        asyncio.create_task(_warm_voice())

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _cuda_info() -> tuple[bool, str]:
    try:
        import torch
        cuda = torch.cuda.is_available()
        device = "cuda" if cuda else "cpu"
        return cuda, device
    except Exception:
        return False, "cpu"


@app.get("/")
async def root():
    """Redirect root to API docs."""
    return RedirectResponse(url="/docs", status_code=302)


def _qdrant_reachable() -> bool:
    try:
        client = get_client()
        client.get_collections()
        return True
    except Exception:
        return False


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """System status: Qdrant, CUDA/device."""
    cuda_available, device = _cuda_info()
    qdrant_ok = _qdrant_reachable()
    status = "ok" if qdrant_ok else "degraded"
    return HealthResponse(
        status=status,
        qdrant_reachable=qdrant_ok,
        cuda_available=cuda_available,
        device=device,
    )


# In-memory session for reset (optional; stateless per request is fine)
_session: dict[str, Any] = {}


@app.get("/api/rag/status", response_model=RAGStatusResponse)
async def rag_status() -> RAGStatusResponse:
    """Return RAG collection status (point count). Useful after ingesting PDFs."""
    try:
        client = get_client()
        info = client.get_collection(COLLECTION_NAME)
        count = info.points_count or 0
        return RAGStatusResponse(
            collection=COLLECTION_NAME,
            points_count=count,
            ready=count > 0,
        )
    except Exception:
        return RAGStatusResponse(collection=COLLECTION_NAME, points_count=0, ready=False)


@app.post("/api/reset")
async def reset() -> Response:
    """Clear in-memory session/history. Returns 204."""
    global _session
    _session.clear()
    return Response(status_code=204)


def _format_patient_context(profile: PatientProfile) -> str:
    """Build a short summary string for prompts."""
    parts = []
    if profile.name:
        parts.append(f"Name: {profile.name}")
    if profile.age is not None:
        parts.append(f"Age: {profile.age}")
    if profile.sex:
        parts.append(f"Sex: {profile.sex}")
    if profile.allergies:
        parts.append(f"Allergies: {profile.allergies}")
    if profile.conditions:
        parts.append(f"Conditions: {profile.conditions}")
    if profile.medications:
        parts.append(f"Medications: {profile.medications}")
    if profile.preferences:
        parts.append(f"Preferences: {profile.preferences}")
    return "\n".join(parts) if parts else ""


async def _save_consultation(
    user_id: str,
    user_message: str,
    assistant_message: str,
    citations: list[dict[str, Any]],
    vision_result: dict[str, Any] | None,
) -> None:
    """Persist one consultation (one exchange) for authenticated user."""
    title = (user_message[:50] + "…") if len(user_message) > 50 else user_message or "Consultation"
    messages = [
        {"role": "user", "content": user_message},
        {
            "role": "assistant",
            "content": assistant_message,
            "citations": citations,
            "vision_result": vision_result,
        },
    ]
    async with async_session_factory() as session:
        session.add(
            Consultation(
                id=str(uuid.uuid4()),
                user_id=user_id,
                title=title,
                messages=messages,
            )
        )
        await session.commit()


@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    authorization: str | None = Header(None, alias="Authorization"),
) -> ChatResponse:
    """Handle text + optional image; run graph; return message, citations, vision_result."""
    patient_context: str | None = None
    auth_user_id: str | None = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()
        auth_user_id = decode_token(token)
        if auth_user_id:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(PatientProfile).where(PatientProfile.user_id == auth_user_id)
                )
                profile = result.scalar_one_or_none()
                if profile:
                    patient_context = _format_patient_context(profile)
    initial: AgentState = {
        "messages": [HumanMessage(content=body.message)],
        "base64_image": body.image_base64,
        "modality": body.modality,
        "retrieved_docs": [],
        "next_step": "continue",
        "vision_result": None,
        "patient_context": patient_context,
    }
    try:
        graph = get_graph()
        final = graph.invoke(initial)
    except Exception as e:
        err_msg = str(e)
        logger.exception("Graph invoke failed")
        print(f"CHAT ERROR: {err_msg}", flush=True)
        raise HTTPException(
            status_code=500,
            detail=err_msg if err_msg else "Request failed. Please try again.",
        )

    messages = final.get("messages") or []
    last_ai = None
    for m in reversed(messages):
        if m.__class__.__name__ == "AIMessage":
            last_ai = m.content
            break
    message_text = last_ai if last_ai else "No response generated."

    citations: list[Citation] = []
    for d in final.get("retrieved_docs") or []:
        citations.append(
            Citation(
                source=d.get("source", ""),
                snippet=(d.get("text", ""))[:500],
                link=None,
            )
        )

    vision_result: VisionResult | None = final.get("vision_result")
    if vision_result is not None and not isinstance(vision_result, VisionResult):
        vision_result = VisionResult(
            modality=vision_result.get("modality", "brain_mri"),
            label=vision_result.get("label", ""),
            confidence=float(vision_result.get("confidence", 0)),
            class_names=vision_result.get("class_names") or [],
            heatmap_base64=vision_result.get("heatmap_base64"),
        )

    if auth_user_id:
        try:
            await _save_consultation(
                auth_user_id,
                body.message,
                message_text,
                [c.model_dump() for c in citations],
                vision_result.model_dump() if vision_result and hasattr(vision_result, "model_dump") else (vision_result if isinstance(vision_result, dict) else None),
            )
        except Exception as e:
            logger.warning("Failed to save consultation: %s", e)
    return ChatResponse(
        message=message_text,
        citations=citations,
        vision_result=vision_result,
    )


async def _chat_stream_generator(
    body: ChatRequest,
    authorization: str | None,
):
    """Yield SSE: status (thinking), chunk (sentence fragments), done (full payload)."""
    patient_context = None
    auth_user_id: str | None = None
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ", 1)[1].strip()
        auth_user_id = decode_token(token)
        if auth_user_id:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(PatientProfile).where(PatientProfile.user_id == auth_user_id)
                )
                profile = result.scalar_one_or_none()
                if profile:
                    patient_context = _format_patient_context(profile)
    initial = {
        "messages": [HumanMessage(content=body.message)],
        "base64_image": body.image_base64,
        "modality": body.modality,
        "retrieved_docs": [],
        "next_step": "continue",
        "vision_result": None,
        "patient_context": patient_context,
    }
    yield f"data: {json.dumps({'type': 'status', 'content': 'thinking'})}\n\n"
    try:
        graph = get_graph()
        final = await asyncio.to_thread(graph.invoke, initial)
    except Exception as e:
        yield f"data: {json.dumps({'type': 'error', 'detail': str(e)})}\n\n"
        return
    messages = final.get("messages") or []
    last_ai = None
    for m in reversed(messages):
        if m.__class__.__name__ == "AIMessage":
            last_ai = m.content
            break
    if isinstance(last_ai, str) and last_ai.strip():
        message_text = last_ai
    elif last_ai is not None:
        message_text = str(last_ai)
    else:
        message_text = "No response generated."
    citations = []
    for d in final.get("retrieved_docs") or []:
        citations.append({
            "source": d.get("source", ""),
            "snippet": (d.get("text", ""))[:500],
            "link": None,
        })
    vision_result = final.get("vision_result")
    if vision_result is not None and hasattr(vision_result, "model_dump"):
        vision_result = vision_result.model_dump()
    elif vision_result is not None and isinstance(vision_result, dict):
        vision_result = vision_result

    sentences = re.split(r"(?<=[.!?])\s+", message_text)
    for sentence in sentences:
        if sentence.strip():
            yield f"data: {json.dumps({'type': 'chunk', 'content': sentence + ' '})}\n\n"
            await asyncio.sleep(0)
    payload = {
        "type": "done",
        "message": message_text,
        "citations": citations,
        "vision_result": vision_result,
    }
    yield f"data: {json.dumps(payload)}\n\n"
    if auth_user_id:
        try:
            await _save_consultation(
                auth_user_id,
                body.message,
                message_text,
                citations,
                vision_result,
            )
        except Exception as e:
            logger.warning("Failed to save consultation: %s", e)
    return


@app.post("/api/chat/stream")
async def chat_stream(
    body: ChatRequest,
    authorization: str | None = Header(None, alias="Authorization"),
):
    """Stream chat response as SSE. Events: status, chunk (content), done (message, citations, vision_result)."""
    return StreamingResponse(
        _chat_stream_generator(body, authorization),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Content-Type": "text/event-stream",
            "Connection": "keep-alive",
        },
    )
