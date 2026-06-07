"""Deterministic mock predictions for Skin Lesion when USE_MOCK_MODELS=True."""
from app.models.schemas import VisionResult


def predict(_image: bytes | None = None) -> VisionResult:
    """Return a fixed mock result."""
    return VisionResult(
        modality="skin_lesion",
        label="Benign",
        confidence=0.92,
        class_names=["Benign", "Malignant"],
    )
