"""Deterministic mock predictions for Chest X-ray when USE_MOCK_MODELS=True."""
from app.models.schemas import VisionResult


def predict(_image: bytes | None = None) -> VisionResult:
    """Return a fixed mock result."""
    return VisionResult(
        modality="chest_xray",
        label="Normal",
        confidence=0.95,
        class_names=["Normal", "Pneumonia", "COVID-19"],
    )
