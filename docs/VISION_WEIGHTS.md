# Real pretrained vision models (from Kaggle)

## 1. Download data from Kaggle

You need a Kaggle account and API credentials:

1. Kaggle → Account → Create New API Token (downloads `kaggle.json`).
2. Place `kaggle.json` in `~/.kaggle/` (Linux/Mac) or `C:\Users\<you>\.kaggle\` (Windows).

Then from project root:

```bash
python scripts/download_vision_weights.py
```

This downloads:

- **Brain MRI:** `sartajbhuvaji/brain-tumor-classification-mri` → `backend/app/services/vision/brain_mri/data/`
- **Chest X-ray:** `paultimothymooney/chest-xray-pneumonia` → `backend/app/services/vision/chest_xray/data/`
- **Skin lesion:** `kmader/skin-cancer-mnist-ham10000` → `backend/app/services/vision/skin_lesion/data/`

## 2. Train and save weights

```bash
python scripts/train_vision_models.py
```

Optional: `python scripts/train_vision_models.py --epochs 5`

This trains a small model (MobileNet V3) per modality and saves:

- `backend/app/services/vision/brain_mri/weights/model.pth`
- `backend/app/services/vision/chest_xray/weights/model.pth`
- `backend/app/services/vision/skin_lesion/weights/model.pth`

## 3. Use real models in the app

1. In **backend/.env** set:
   ```env
   USE_MOCK_MODELS=false
   ```

2. In each modality’s **config.py** set:
   - **brain_mri:** `MODEL_PATH = "weights/model.pth"` (already 4 classes).
   - **chest_xray:** `MODEL_PATH = "weights/model.pth"` and set `CLASS_NAMES = ["Normal", "Pneumonia"]` (2 classes; Mooney dataset has no COVID-19).
   - **skin_lesion:** `MODEL_PATH = "weights/model.pth"` (2 classes: Benign, Malignant; HAM10000 may need 7→2 mapping in the training script).

Restart the backend; vision will use the trained weights instead of mocks.
