"""Dispatcher: analyze(image, modality) -> VisionResult."""
from typing import Callable, Literal

from app.models.schemas import VisionResult

from app.services.vision.brain_mri.runner import run as run_brain_mri
from app.services.vision.chest_xray.runner import run as run_chest_xray
from app.services.vision.skin_lesion.runner import run as run_skin_lesion

Modality = Literal["brain_mri", "chest_xray", "skin_lesion"]
_RUNNERS: dict[Modality, Callable[[bytes], VisionResult]] = {
    "brain_mri": run_brain_mri,
    "chest_xray": run_chest_xray,
    "skin_lesion": run_skin_lesion,
}


def analyze(image: bytes, modality: Modality) -> VisionResult:
    """Run vision for the given modality. Loads only that modality (lazy)."""
    if modality not in _RUNNERS:
        raise ValueError(f"Unknown modality: {modality}. Use brain_mri, chest_xray, skin_lesion.")
    return _RUNNERS[modality](image)
