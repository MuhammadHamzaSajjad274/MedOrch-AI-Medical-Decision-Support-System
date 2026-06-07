"""Chest X-ray runner: mock or load model, return VisionResult."""
from typing import Union

import numpy as np

from app.models.schemas import VisionResult

from app.services.vision.chest_xray import config as chest_config
from app.services.vision.chest_xray.mock import predict as mock_predict
from app.services.vision.gradcam_utils import run_gradcam_overlay


def run(image: Union[bytes, "bytes"]) -> VisionResult:
    """Run Chest X-ray analysis."""
    if chest_config.USE_MOCK:
        return mock_predict(image)

    import io
    import torch
    from PIL import Image
    from torchvision import transforms
    from torchvision.models import mobilenet_v3_small

    device = "cuda" if torch.cuda.is_available() else "cpu"
    num_classes = len(chest_config.CLASS_NAMES)
    model = mobilenet_v3_small(weights="DEFAULT")
    model.classifier[3] = torch.nn.Linear(model.classifier[3].in_features, num_classes)
    if chest_config.MODEL_PATH:
        from pathlib import Path
        p = Path(chest_config.__file__).resolve().parent / chest_config.MODEL_PATH
        state = torch.load(p, map_location=device)
        if isinstance(state, dict) and "state_dict" in state:
            model.load_state_dict(state["state_dict"], strict=False)
        elif isinstance(state, dict):
            model.load_state_dict(state, strict=False)
    model = model.to(device)

    if isinstance(image, bytes):
        img = Image.open(io.BytesIO(image)).convert("RGB")
    else:
        img = image
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
        modality="chest_xray",
        label=chest_config.CLASS_NAMES[idx],
        confidence=float(probs[idx]),
        class_names=chest_config.CLASS_NAMES,
        heatmap_base64=heatmap_base64,
    )
