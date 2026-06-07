"""Brain MRI runner: mock or load model, return VisionResult."""
from typing import Union

import numpy as np

from app.models.schemas import VisionResult

from app.services.vision.brain_mri import config as brain_config
from app.services.vision.brain_mri.mock import predict as mock_predict
from app.services.vision.gradcam_utils import run_gradcam_overlay


def run(image: Union[bytes, "bytes"]) -> VisionResult:
    """Run Brain MRI analysis. Uses mock if USE_MOCK else torchvision placeholder."""
    if brain_config.USE_MOCK:
        return mock_predict(image)

    import io
    import torch
    from PIL import Image
    from torchvision import transforms

    device = "cuda" if torch.cuda.is_available() else "cpu"
    if brain_config.MODEL_PATH:
        model = _load_custom_model(brain_config.MODEL_PATH, device)
    else:
        model = _load_placeholder_model(device)

    img = Image.open(io.BytesIO(image)).convert("RGB")
    t = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    x = t(img).unsqueeze(0).to(device)
    model.eval()
    with torch.no_grad():
        logits = model(x)
    probs = torch.softmax(logits, dim=1).cpu().numpy()[0]
    idx = int(probs.argmax())

    heatmap_base64 = None
    try:
        rgb_np = np.array(img.resize((224, 224))) / 255.0
        heatmap_base64 = run_gradcam_overlay(
            model, x, idx, rgb_np, [model.features[-1]]
        )
    except Exception:
        pass

    return VisionResult(
        modality="brain_mri",
        label=brain_config.CLASS_NAMES[idx],
        confidence=float(probs[idx]),
        class_names=brain_config.CLASS_NAMES,
        heatmap_base64=heatmap_base64,
    )


def _load_placeholder_model(device: str):
    """Torchvision mobilenet_v3_small adapted for num_classes."""
    import torch
    from torchvision.models import mobilenet_v3_small
    num_classes = len(brain_config.CLASS_NAMES)
    model = mobilenet_v3_small(weights="DEFAULT")
    model.classifier[3] = torch.nn.Linear(model.classifier[3].in_features, num_classes)
    return model.to(device)


def _load_custom_model(path: str, device: str):
    """Load user model from Kaggle .pth. Override in this module with your architecture."""
    import torch
    from pathlib import Path
    p = Path(brain_config.__file__).resolve().parent / path
    state = torch.load(p, map_location=device)
    # User replaces this with their model class + load_state_dict
    model = _load_placeholder_model(device)
    if isinstance(state, dict) and "state_dict" in state:
        model.load_state_dict(state["state_dict"], strict=False)
    elif isinstance(state, dict):
        model.load_state_dict(state, strict=False)
    return model
