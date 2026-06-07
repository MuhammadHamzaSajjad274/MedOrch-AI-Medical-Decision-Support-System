"""Vision config: actionable labels, research query."""
import pytest

from app.agents.vision_config import (
    ACTIONABLE_LABELS,
    build_research_query,
    is_actionable,
)


def test_is_actionable_brain_mri():
    assert is_actionable("brain_mri", "Glioma", 0.8) is True
    assert is_actionable("brain_mri", "Glioma", 0.5) is False
    assert is_actionable("brain_mri", "Normal", 0.9) is False


def test_is_actionable_chest_xray():
    assert is_actionable("chest_xray", "Pneumonia", 0.75) is True
    assert is_actionable("chest_xray", "Normal", 0.9) is False


def test_is_actionable_skin_lesion():
    assert is_actionable("skin_lesion", "Malignant", 0.8) is True
    assert is_actionable("skin_lesion", "Benign", 0.9) is False


def test_build_research_query():
    q = build_research_query("brain_mri", "Glioma")
    assert "Glioma" in q
    assert "brain" in q.lower()
    assert "evidence" in q.lower()


def test_actionable_labels_keys():
    assert set(ACTIONABLE_LABELS.keys()) == {"brain_mri", "chest_xray", "skin_lesion"}
