"""Chest X-ray modality config. Set MODEL_PATH for Kaggle-downloaded weights."""
from pathlib import Path

from app.core.config import get_settings

_settings = get_settings()
_MODALITY_DIR = Path(__file__).resolve().parent

USE_MOCK: bool = _settings.USE_MOCK_MODELS
MODEL_PATH: str | None = "weights/model.pth"
# NOTE: The chest X-ray training script uses two classes (NORMAL, PNEUMONIA).
# The saved MobileNet head therefore has output dimension 2. To avoid size
# mismatch when loading the checkpoint, CLASS_NAMES must also have length 2.
CLASS_NAMES: list[str] = ["Normal", "Pneumonia"]
device: str = "cuda"
