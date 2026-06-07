from __future__ import annotations

"""
Text-to-speech using Piper with sentence chunking support.
"""

import io
import logging
import os
import re
import wave
from functools import lru_cache
from pathlib import Path

from piper.voice import PiperVoice

logger = logging.getLogger(__name__)

_MAX_TTS_CHARS = int(os.getenv("TTS_MAX_CHARS", "1200"))


class TTSNotConfiguredError(RuntimeError):
    """Raised when no TTS model is configured."""


def _project_root() -> Path:
    return Path(__file__).resolve().parents[4]


def _default_piper_path() -> Path:
    return _project_root() / "models" / "piper" / "en_US-lessac-medium.onnx"


def _get_model_path() -> str:
    model_path = os.getenv("PIPER_MODEL_PATH", "").strip()
    if not model_path:
        candidate = _default_piper_path()
        if candidate.exists():
            return str(candidate)
        raise TTSNotConfiguredError(
            "PIPER_MODEL_PATH is not set and default model was not found at "
            f"{candidate}. Download a Piper .onnx voice or set PIPER_MODEL_PATH."
        )
    if not Path(model_path).exists():
        raise TTSNotConfiguredError(f"Piper model not found: {model_path}")
    return model_path


@lru_cache
def get_voice() -> PiperVoice:
    """Lazily load Piper voice from disk."""
    model_path = _get_model_path()
    logger.info("Loading Piper model from %s", model_path)
    return PiperVoice.load(model_path)


def warmup_tts() -> None:
    """Prime Piper so first playback is faster."""
    synthesize_wav_bytes("Voice system ready.")


def split_sentences(text: str, max_len: int = 220) -> list[str]:
    """Split text into speakable chunks for lower latency playback."""
    cleaned = re.sub(r"\s+", " ", (text or "").strip())
    if not cleaned:
        return []
    if len(cleaned) <= max_len:
        return [cleaned]
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    chunks: list[str] = []
    buf = ""
    for part in parts:
        candidate = f"{buf} {part}".strip() if buf else part
        if len(candidate) <= max_len:
            buf = candidate
            continue
        if buf:
            chunks.append(buf)
        if len(part) <= max_len:
            buf = part
        else:
            for i in range(0, len(part), max_len):
                chunks.append(part[i : i + max_len])
            buf = ""
    if buf:
        chunks.append(buf)
    return chunks


def synthesize_wav_bytes(text: str) -> bytes:
    """Synthesize text into one WAV byte stream."""
    cleaned = (text or "").strip()[:_MAX_TTS_CHARS]
    if not cleaned:
        return b""

    voice = get_voice()
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        voice.synthesize_wav(cleaned, wav_file)
    return buffer.getvalue()


def synthesize_wav_chunks(text: str) -> list[bytes]:
    """Synthesize each sentence chunk as separate WAV payloads."""
    chunks = split_sentences(text)
    if not chunks:
        return []
    return [synthesize_wav_bytes(chunk) for chunk in chunks if chunk.strip()]
