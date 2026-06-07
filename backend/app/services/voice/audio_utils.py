"""Shared audio helpers for voice services."""
from __future__ import annotations

import io
from typing import Tuple

import numpy as np
import soundfile as sf


def load_audio_mono_f32(data: bytes) -> Tuple[np.ndarray, int]:
    """Decode audio bytes to mono float32 waveform and sample rate."""
    with io.BytesIO(data) as buf:
        audio, samplerate = sf.read(buf, always_2d=False)
    if audio.ndim == 2:
        audio = np.mean(audio, axis=1)
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)
    return audio, int(samplerate)


def normalize_peak(audio: np.ndarray, peak: float = 0.95) -> np.ndarray:
    """Normalize waveform so short clips are not too quiet for Whisper."""
    if audio.size == 0:
        return audio
    max_abs = float(np.max(np.abs(audio)))
    if max_abs < 1e-6:
        return audio
    return (audio * (peak / max_abs)).astype(np.float32)


def trim_leading_trailing_silence(
    audio: np.ndarray,
    sample_rate: int,
    threshold: float = 0.012,
    pad_ms: int = 120,
) -> np.ndarray:
    """Trim silence at start/end to reduce false transcriptions."""
    if audio.size == 0:
        return audio
    abs_audio = np.abs(audio)
    idx = np.where(abs_audio > threshold)[0]
    if idx.size == 0:
        return audio
    pad = int(sample_rate * pad_ms / 1000)
    start = max(0, int(idx[0]) - pad)
    end = min(audio.size, int(idx[-1]) + pad)
    return audio[start:end]
