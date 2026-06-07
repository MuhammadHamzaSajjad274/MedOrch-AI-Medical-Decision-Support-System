"""Actionable findings per modality: trigger diagnosis-specific RAG when detected."""

# Labels that warrant automatic literature lookup (evidence-based management)
ACTIONABLE_LABELS: dict[str, set[str]] = {
    "brain_mri": {"Glioma", "Meningioma", "Pituitary"},
    "chest_xray": {"Pneumonia"},
    "skin_lesion": {"Malignant"},
}

RESEARCH_CONFIDENCE_THRESHOLD = 0.7


def is_actionable(modality: str, label: str, confidence: float) -> bool:
    """True if we should run RAG for this finding."""
    labels = ACTIONABLE_LABELS.get(modality)
    if not labels:
        return False
    return label in labels and confidence >= RESEARCH_CONFIDENCE_THRESHOLD


def build_research_query(modality: str, label: str) -> str:
    """Build a query for evidence-based management / literature."""
    modality_label = modality.replace("_", " ").title()
    return f"evidence-based management and guidelines for {label} in {modality_label}"
