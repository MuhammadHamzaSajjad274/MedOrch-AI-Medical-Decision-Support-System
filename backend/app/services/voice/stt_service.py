from __future__ import annotations

"""
Speech-to-text using faster-whisper, tuned for short UI utterances.
"""

import logging
import os
from functools import lru_cache
from typing import Tuple

import numpy as np
from faster_whisper import WhisperModel

from app.services.voice.audio_utils import (
    load_audio_mono_f32,
    normalize_peak,
    trim_leading_trailing_silence,
)

logger = logging.getLogger(__name__)

_STT_INITIAL_PROMPT = (
    "Hello. Hi. Yes. No. Thank you. Medical assistant conversation. "
    "Symptoms, pain, fever, cough, headache."
)


def _get_model_config() -> Tuple[str, str, int]:
    model = os.getenv("WHISPER_MODEL", "base.en").strip() or "base.en"
    device = os.getenv("WHISPER_DEVICE", "auto").lower()
    if device not in {"cuda", "cpu", "auto"}:
        device = "auto"
    try:
        beam_size = int(os.getenv("WHISPER_BEAM_SIZE", "5"))
    except ValueError:
        beam_size = 5
    beam_size = max(1, min(beam_size, 10))
    return model, device, beam_size


def _resolve_device(device: str) -> Tuple[str, str]:
    if device != "auto":
        resolved = device
    else:
        try:
            import torch

            resolved = "cuda" if torch.cuda.is_available() else "cpu"
        except Exception:
            resolved = "cpu"
    compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "").strip().lower()
    if not compute_type:
        compute_type = "float16" if resolved == "cuda" else "int8"
    return resolved, compute_type


@lru_cache
def get_stt_model() -> WhisperModel:
    """Load Whisper once per process."""
    model_name, device_pref, _ = _get_model_config()
    device, compute_type = _resolve_device(device_pref)
    logger.info(
        "Loading Whisper model=%s device=%s compute_type=%s",
        model_name,
        device,
        compute_type,
    )
    return WhisperModel(model_name, device=device, compute_type=compute_type)


def warmup_stt() -> None:
    """Prime model weights so first user request is fast."""
    model = get_stt_model()
    silent = np.zeros(16000, dtype=np.float32)
    segments, _ = model.transcribe(
        silent,
        beam_size=1,
        vad_filter=False,
        language="en",
    )
    list(segments)


def transcribe_bytes(data: bytes) -> str:
    """
    Transcribe a short utterance from WAV/FLAC/OGG bytes.
    Call from a worker thread when used inside async endpoints.
    """
    if not data or len(data) < 44:
        return ""

    audio, sample_rate = load_audio_mono_f32(data)
    audio = trim_leading_trailing_silence(audio, sample_rate)
    audio = normalize_peak(audio)

    min_samples = int(sample_rate * 0.25)
    if audio.size < min_samples:
        return ""

    _, _, beam_size = _get_model_config()
    model = get_stt_model()
    segments, _info = model.transcribe(
        audio,
        language="en",
        beam_size=beam_size,
        best_of=min(beam_size, 5),
        temperature=0.0,
        condition_on_previous_text=False,
        vad_filter=True,
        vad_parameters={
            "min_silence_duration_ms": 300,
            "speech_pad_ms": 120,
        },
        initial_prompt=_STT_INITIAL_PROMPT,
        without_timestamps=True,
    )
    texts = [seg.text.strip() for seg in segments if seg.text and seg.text.strip()]
    return " ".join(texts).strip()
