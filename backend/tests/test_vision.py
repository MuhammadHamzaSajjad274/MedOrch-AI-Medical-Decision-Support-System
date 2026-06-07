"""Phase 2 verification: dummy image -> VisionService -> structured VisionResult."""
from __future__ import annotations

import io
import sys
from pathlib import Path

# Add backend to path
backend = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend))

# Minimal PNG 1x1 red pixel (valid image bytes)
DUMMY_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_vision_brain_mri() -> None:
    from app.services.vision.vision_service import analyze

    result = analyze(DUMMY_PNG, "brain_mri")
    assert result.modality == "brain_mri"
    assert result.label
    assert 0 <= result.confidence <= 1
    assert isinstance(result.class_names, list)


def test_vision_chest_xray() -> None:
    from app.services.vision.vision_service import analyze

    result = analyze(DUMMY_PNG, "chest_xray")
    assert result.modality == "chest_xray"
    assert result.label
    assert 0 <= result.confidence <= 1


def test_vision_skin_lesion() -> None:
    from app.services.vision.vision_service import analyze

    result = analyze(DUMMY_PNG, "skin_lesion")
    assert result.modality == "skin_lesion"
    assert result.label
    assert 0 <= result.confidence <= 1


if __name__ == "__main__":
    test_vision_brain_mri()
    test_vision_chest_xray()
    test_vision_skin_lesion()
    print("All vision tests passed.")
