"""Voice API: STT, TTS, warmup."""
from __future__ import annotations

import asyncio

from fastapi import APIRouter, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel, Field
from starlette.websockets import WebSocketState

from app.core.logger import setup_logger
from app.services.voice.stt_service import transcribe_bytes, warmup_stt
from app.services.voice.tts_service import (
    TTSNotConfiguredError,
    synthesize_wav_bytes,
    synthesize_wav_chunks,
    warmup_tts,
)

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/voice", tags=["voice"])


class TtsRequest(BaseModel):
    text: str = Field(default="", max_length=4000)


class VoiceStatusResponse(BaseModel):
    stt_ready: bool
    tts_ready: bool


@router.get("/status", response_model=VoiceStatusResponse)
async def voice_status() -> VoiceStatusResponse:
    stt_ready = False
    tts_ready = False
    try:
        from app.services.voice.stt_service import get_stt_model

        get_stt_model()
        stt_ready = True
    except Exception:
        pass
    try:
        from app.services.voice.tts_service import get_voice

        get_voice()
        tts_ready = True
    except Exception:
        pass
    return VoiceStatusResponse(stt_ready=stt_ready, tts_ready=tts_ready)


@router.post("/warmup")
async def voice_warmup() -> dict[str, str]:
    """Load STT/TTS models in background threads at startup or on demand."""
    errors: list[str] = []

    def _warm_stt() -> None:
        warmup_stt()

    def _warm_tts() -> None:
        warmup_tts()

    try:
        await asyncio.to_thread(_warm_stt)
    except Exception as e:
        logger.warning("STT warmup failed: %s", e)
        errors.append(f"stt:{e}")

    try:
        await asyncio.to_thread(_warm_tts)
    except Exception as e:
        logger.warning("TTS warmup failed: %s", e)
        errors.append(f"tts:{e}")

    if errors:
        return {"status": "partial", "detail": "; ".join(errors)}
    return {"status": "ok"}


@router.post("/stt")
async def stt_upload(file: UploadFile = File(...)) -> dict[str, str]:
    """Transcribe uploaded audio (WAV preferred). Faster than WebSocket for one-shot clips."""
    data = await file.read()
    if not data:
        return {"text": ""}
    try:
        text = await asyncio.to_thread(transcribe_bytes, data)
    except Exception as e:
        logger.exception("STT upload failed: %s", e)
        raise HTTPException(status_code=500, detail="STT failed") from e
    return {"text": text}


@router.websocket("/stt/stream")
async def stt_stream(ws: WebSocket) -> None:
    """Binary WAV in, JSON {type: final, text} out."""
    await ws.accept()
    try:
        message = await ws.receive()
        audio_bytes: bytes | None = None
        if message.get("bytes") is not None:
            audio_bytes = message["bytes"]
        transcript = await asyncio.to_thread(transcribe_bytes, audio_bytes or b"")
        await ws.send_json({"type": "final", "text": transcript})
    except WebSocketDisconnect:
        return
    except Exception as e:
        logger.exception("STT stream failed: %s", e)
        if ws.application_state == WebSocketState.CONNECTED:
            await ws.send_json({"type": "error", "detail": str(e)})
    finally:
        if ws.application_state != WebSocketState.DISCONNECTED:
            try:
                await ws.close()
            except RuntimeError:
                pass


@router.post("/tts")
async def tts(body: TtsRequest) -> Response:
    message = body.text.strip()
    if not message:
        return Response(status_code=400, content="Missing text")
    try:
        audio = await asyncio.to_thread(synthesize_wav_bytes, message)
    except TTSNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        logger.exception("TTS failed: %s", e)
        raise HTTPException(status_code=500, detail="TTS synthesis failed") from e
    return Response(content=audio, media_type="audio/wav")


@router.post("/tts/chunks")
async def tts_chunks(body: TtsRequest) -> Response:
    """Return newline-delimited base64 WAV chunks for low-latency sequential playback."""
    import base64

    message = body.text.strip()
    if not message:
        return Response(status_code=400, content="Missing text")
    try:
        wav_list = await asyncio.to_thread(synthesize_wav_chunks, message)
    except TTSNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except Exception as e:
        logger.exception("TTS chunks failed: %s", e)
        raise HTTPException(status_code=500, detail="TTS synthesis failed") from e

    encoded = [base64.b64encode(chunk).decode("ascii") for chunk in wav_list]
    payload = "\n".join(encoded).encode("utf-8")
    return Response(content=payload, media_type="text/plain")
