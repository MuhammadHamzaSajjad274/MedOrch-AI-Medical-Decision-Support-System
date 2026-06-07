#!/usr/bin/env python3
"""
Download vision datasets from Kaggle into modality data/ folders.
After download, run: python scripts/train_vision_models.py
to train and save weights/model.pth per modality.

Usage:
  python scripts/download_vision_weights.py              # download all (skip if data present)
  python scripts/download_vision_weights.py chest_xray   # download only chest_xray
  python scripts/download_vision_weights.py skin_lesion # download only skin_lesion
  python scripts/download_vision_weights.py brain_mri   # download only brain_mri

If you don't see download progress in the terminal, run with unbuffered output:
  python -u scripts/download_vision_weights.py chest_xray

Requires: pip install kaggle, and ~/.kaggle/kaggle.json (or KAGGLE_USERNAME/KAGGLE_KEY).
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
VISION_BASE = PROJECT_ROOT / "backend" / "app" / "services" / "vision"

# Load backend/.env so KAGGLE_USERNAME and KAGGLE_KEY are available
_env_path = (PROJECT_ROOT / "backend" / ".env").resolve()
import os

def _load_env_file(path: Path) -> None:
    """Load .env from path; set KAGGLE_USERNAME and KAGGLE_KEY in os.environ."""
    if not path.exists():
        return
    try:
        from dotenv import load_dotenv
        load_dotenv(path, override=True)
    except ImportError:
        pass
    # Always parse .env for KAGGLE_* so we get them even if dotenv didn't
    raw = path.read_text(encoding="utf-8-sig", errors="ignore")
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip("'\"")
        if key in ("KAGGLE_USERNAME", "KAGGLE_KEY") and val:
            os.environ[key] = val

_load_env_file(_env_path)
# Fallback: try project root .env
if not os.environ.get("KAGGLE_USERNAME") or not os.environ.get("KAGGLE_KEY"):
    _load_env_file(PROJECT_ROOT / ".env")

# Modality -> (Kaggle dataset slug, expected zip name or None)
KAGGLE_DATASETS: dict[str, tuple[str, str | None]] = {
    "brain_mri": ("sartajbhuvaji/brain-tumor-classification-mri", None),
    "chest_xray": ("paultimothymooney/chest-xray-pneumonia", None),
    "skin_lesion": ("kmader/skin-cancer-mnist-ham10000", None),
}


def _load_kaggle_env() -> None:
    """Load backend/.env and write ~/.kaggle/kaggle.json from KAGGLE_USERNAME/KAGGLE_KEY."""
    import json
    _load_env_file(_env_path)
    username = os.environ.get("KAGGLE_USERNAME")
    key = os.environ.get("KAGGLE_KEY")
    if username and key:
        kaggle_dir = Path.home() / ".kaggle"
        kaggle_dir.mkdir(mode=0o700, exist_ok=True)
        kaggle_json = kaggle_dir / "kaggle.json"
        kaggle_json.write_text(json.dumps({"username": username, "key": key}), encoding="utf-8")
        try:
            kaggle_json.chmod(0o600)
        except OSError:
            pass


def main() -> int:
    # Show output and progress bar immediately in terminal (no buffering)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(line_buffering=True)
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(line_buffering=True)
    sys.stdout.flush()
    sys.stderr.flush()

    _load_kaggle_env()
    username = os.environ.get("KAGGLE_USERNAME")
    key = os.environ.get("KAGGLE_KEY")
    if not username or not key:
        print("Kaggle credentials not found.", flush=True)
        print("Add to backend/.env (create from backend/.env.example):", flush=True)
        print("  KAGGLE_USERNAME=your_username", flush=True)
        print("  KAGGLE_KEY=your_api_key", flush=True)
        print("Get an API key: https://www.kaggle.com/settings -> Create New API Token", flush=True)
        return 1
    try:
        import kaggle.api
    except ImportError:
        print("Install kaggle: pip install kaggle", flush=True)
        return 1
    except OSError:
        print("Kaggle credentials not found (invalid key or kaggle.json not written).", flush=True)
        print("Check KAGGLE_USERNAME and KAGGLE_KEY in backend/.env.", flush=True)
        return 1

    def _has_data(d: Path) -> bool:
        if not d.exists():
            return False
        # Has subdirs (e.g. Training/Testing) or many files
        subdirs = [x for x in d.iterdir() if x.is_dir()]
        if subdirs:
            return True
        files = list(d.glob("**/*.jpg")) + list(d.glob("**/*.jpeg")) + list(d.glob("**/*.png"))
        return len(files) >= 20

    # Optional: download one modality only (e.g. python download_vision_weights.py chest_xray)
    modalities_to_run = KAGGLE_DATASETS
    if len(sys.argv) >= 2:
        one = sys.argv[1].strip().lower()
        if one in KAGGLE_DATASETS:
            modalities_to_run = {one: KAGGLE_DATASETS[one]}
            print(f"Downloading single modality: {one}", flush=True)
        else:
            print(f"Unknown modality: {one}. Use one of: {list(KAGGLE_DATASETS.keys())}", flush=True)
            return 1

    for modality, (slug, _) in modalities_to_run.items():
        out_dir = VISION_BASE / modality / "data"
        out_dir.mkdir(parents=True, exist_ok=True)
        if _has_data(out_dir):
            print(f"Skipping {modality} (data already present)", flush=True)
            continue
        print(f"Downloading {slug} -> {out_dir}", flush=True)
        print("(Progress will appear below; large datasets may take several minutes.)", flush=True)
        try:
            kaggle.api.dataset_download_files(slug, path=str(out_dir), unzip=True, quiet=False)
            print(f"Downloaded and extracted {modality}", flush=True)
        except Exception as e:
            print(f"Failed: {modality}. {e}", flush=True)
            # If API left a zip, try extracting it
            zip_name = slug.split("/")[-1] + ".zip"
            zip_path = out_dir / zip_name
            if zip_path.exists():
                try:
                    with zipfile.ZipFile(zip_path, "r") as z:
                        z.extractall(out_dir)
                    zip_path.unlink(missing_ok=True)
                    print(f"Extracted {modality} from zip", flush=True)
                except Exception as e2:
                    print(f"Extract failed: {e2}", flush=True)

    print("Done. Next: python scripts/train_vision_models.py", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
