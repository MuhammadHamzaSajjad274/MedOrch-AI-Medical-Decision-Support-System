"""Deterministic mock predictions for Brain MRI when USE_MOCK_MODELS=True."""
from app.models.schemas import VisionResult


def predict(_image: bytes | None = None) -> VisionResult:
    """Return a fixed mock result."""
    return VisionResult(
        modality="brain_mri",
        label="Glioma",
        confidence=0.98,
        class_names=["No tumor", "Glioma", "Meningioma", "Pituitary"],
    )
