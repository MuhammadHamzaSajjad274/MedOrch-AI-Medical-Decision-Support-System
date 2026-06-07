"""Grad-CAM heatmap overlay for vision models. Returns base64 PNG."""
from __future__ import annotations

import base64
import io
from typing import Any

import numpy as np


def run_gradcam_overlay(
    model: Any,
    input_tensor: Any,
    target_class_idx: int,
    rgb_img: np.ndarray,
    target_layers: list[Any],
) -> str | None:
    """
    Run Grad-CAM and overlay on rgb_img. Return base64-encoded PNG, or None on error.
    rgb_img: float [0,1] HWC.
    """
    try:
        from pytorch_grad_cam import GradCAM
        from pytorch_grad_cam.utils.image import show_cam_on_image
        from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget
    except ImportError:
        return None
    try:
        with GradCAM(model=model, target_layers=target_layers) as cam:
            targets = [ClassifierOutputTarget(target_class_idx)]
            grayscale_cam = cam(input_tensor=input_tensor, targets=targets)
            grayscale_cam = grayscale_cam[0, :]
            visualization = show_cam_on_image(rgb_img, grayscale_cam, use_rgb=True)
        # visualization is uint8 RGB; encode as PNG
        from PIL import Image
        img = Image.fromarray(visualization)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return base64.b64encode(buf.getvalue()).decode("ascii")
    except Exception:
        return None
