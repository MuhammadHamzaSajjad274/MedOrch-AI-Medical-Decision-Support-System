"""Brain MRI modality config. Set MODEL_PATH for Kaggle-downloaded weights."""
from pathlib import Path

from app.core.config import get_settings

_settings = get_settings()
_MODALITY_DIR = Path(__file__).resolve().parent

USE_MOCK: bool = _settings.USE_MOCK_MODELS
MODEL_PATH: str | None = "weights/model.pth"
CLASS_NAMES: list[str] = ["No tumor", "Glioma", "Meningioma", "Pituitary"]
device: str = "cuda"  # Set in runner from torch availability
