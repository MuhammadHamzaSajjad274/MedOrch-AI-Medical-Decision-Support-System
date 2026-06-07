#!/usr/bin/env python3
"""
Train vision models on downloaded Kaggle data and save weights/model.pth per modality.
Run after: python scripts/download_vision_weights.py

Expects data in backend/app/services/vision/<modality>/data/ with structure:
  train/<class1>/, train/<class2>/  (or Training/ for brain MRI)
"""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND = PROJECT_ROOT / "backend"
sys.path.insert(0, str(BACKEND))

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.datasets import ImageFolder
from torchvision.models import mobilenet_v3_small

VISION_BASE = BACKEND / "app" / "services" / "vision"

# Modality -> (data subdir pattern, num_classes, class names for mapping)
MODALITY_CONFIG = {
    "brain_mri": {
        "train_dirs": ["Training", "train"],  # try these
        "num_classes": 4,
        "class_names": ["no_tumor", "glioma", "meningioma", "pituitary"],
    },
    "chest_xray": {
        "train_dirs": ["train", "chest_xray/train", "chest-xray-pneumonia/chest_xray/train"],
        "num_classes": 2,
        "class_names": ["NORMAL", "PNEUMONIA"],
    },
    "skin_lesion": {
        "train_dirs": ["train", "train_images"],  # HAM10000 may use train_images
        "num_classes": 2,  # Benign vs Malignant (map from 7 HAM classes if needed)
        "class_names": ["benign", "malignant"],
    },
}


def find_train_root(modality: str) -> Path | None:
    data_dir = VISION_BASE / modality / "data"
    if not data_dir.exists():
        return None
    cfg = MODALITY_CONFIG[modality]
    for name in cfg["train_dirs"]:
        candidate = data_dir / name
        if candidate.exists():
            # Check for class subdirs
            subdirs = [d for d in candidate.iterdir() if d.is_dir()]
            if len(subdirs) >= 2:
                return candidate
        # Try nested (e.g. after unzip)
        for sub in data_dir.rglob(name):
            if sub.is_dir():
                subdirs = [d for d in sub.iterdir() if d.is_dir()]
                if len(subdirs) >= 2:
                    return sub
    return None


def train_modality(modality: str, epochs: int = 2, batch_size: int = 32) -> bool:
    train_root = find_train_root(modality)
    if train_root is None:
        print(f"[{modality}] No train data found in {VISION_BASE / modality / 'data'}")
        return False

    cfg = MODALITY_CONFIG[modality]
    num_classes = cfg["num_classes"]
    device = "cuda" if torch.cuda.is_available() else "cpu"

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    try:
        dataset = ImageFolder(str(train_root), transform=transform)
    except Exception as e:
        print(f"[{modality}] ImageFolder failed: {e}")
        return False

    if len(dataset.classes) != num_classes and modality == "skin_lesion":
        # HAM10000: 7 classes (akiec, bcc, bkl, df, mel, nv, vasc). Map mel -> Malignant(1), rest -> Benign(0)
        if "mel" in [c.lower() for c in dataset.classes]:
            class_to_idx = dataset.class_to_idx
            mel_idx = next((class_to_idx[c] for c in dataset.classes if c.lower() == "mel"), None)
            if mel_idx is not None:
                # Binary targets: 0 = Benign, 1 = Malignant (melanoma)
                class_map = {i: 1 if i == mel_idx else 0 for i in range(len(dataset.classes))}
                from torch.utils.data import Subset
                from torch.utils.data import Dataset
                class _BinaryWrapper(Dataset):
                    def __init__(self, parent, mapping):
                        self.parent = parent
                        self.mapping = mapping
                    def __len__(self): return len(self.parent)
                    def __getitem__(self, i):
                        x, y = self.parent[i]
                        return x, self.mapping[y]
                dataset = _BinaryWrapper(dataset, class_map)
                num_classes = 2
            else:
                num_classes = min(len(dataset.classes), num_classes)
        else:
            num_classes = min(len(dataset.classes), num_classes)

    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, num_workers=0, pin_memory=False)
    model = mobilenet_v3_small(weights="DEFAULT")
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, num_classes)
    model = model.to(device)

    opt = torch.optim.Adam(model.parameters(), lr=1e-4)
    model.train()
    for epoch in range(epochs):
        total, correct = 0, 0
        for xs, ys in loader:
            xs, ys = xs.to(device), ys.to(device)
            opt.zero_grad()
            logits = model(xs)
            loss = nn.functional.cross_entropy(logits, ys)
            loss.backward()
            opt.step()
            total += ys.size(0)
            correct += (logits.argmax(1) == ys).sum().item()
        print(f"[{modality}] Epoch {epoch+1}/{epochs} loss={loss.item():.4f} acc={correct/total:.4f}")

    weights_dir = VISION_BASE / modality / "weights"
    weights_dir.mkdir(parents=True, exist_ok=True)
    out_path = weights_dir / "model.pth"
    torch.save(model.state_dict(), out_path)
    print(f"[{modality}] Saved {out_path}")
    return True


def main() -> int:
    epochs = 2
    if "--epochs" in sys.argv:
        i = sys.argv.index("--epochs")
        if i + 1 < len(sys.argv):
            epochs = int(sys.argv[i + 1])

    trained = 0
    for modality in ["brain_mri", "chest_xray", "skin_lesion"]:
        if train_modality(modality, epochs=epochs):
            trained += 1

    if trained == 0:
        print("No modality had data. Run: python scripts/download_vision_weights.py")
        return 1
    print(f"Trained {trained} model(s). Set USE_MOCK_MODELS=false and MODEL_PATH='weights/model.pth' in each config.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
