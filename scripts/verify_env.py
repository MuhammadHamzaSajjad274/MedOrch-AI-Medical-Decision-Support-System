#!/usr/bin/env python3
"""Verify backend env: import all libs and report CUDA/CPU. Exit 0 on success."""
import sys
from pathlib import Path

# Ensure backend is on path
backend = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend))

def main() -> int:
    errors: list[str] = []
    device = "cpu"
    cuda_available = False

    try:
        import fastapi  # noqa: F401
    except ImportError as e:
        errors.append(f"fastapi: {e}")

    try:
        import uvicorn  # noqa: F401
    except ImportError as e:
        errors.append(f"uvicorn: {e}")

    try:
        import langgraph  # noqa: F401
    except ImportError as e:
        errors.append(f"langgraph: {e}")

    try:
        import langchain_openai  # noqa: F401
    except ImportError as e:
        errors.append(f"langchain-openai: {e}")

    try:
        import qdrant_client  # noqa: F401
    except ImportError as e:
        errors.append(f"qdrant-client: {e}")

    try:
        import torch
        cuda_available = torch.cuda.is_available()
        device = "cuda" if cuda_available else "cpu"
    except ImportError as e:
        errors.append(f"torch: {e}")

    try:
        import torchvision  # noqa: F401
    except ImportError as e:
        errors.append(f"torchvision: {e}")

    try:
        import PIL  # noqa: F401
    except ImportError as e:
        errors.append(f"pillow: {e}")

    try:
        import pydantic  # noqa: F401
    except ImportError as e:
        errors.append(f"pydantic: {e}")

    try:
        import dotenv  # noqa: F401
    except ImportError as e:
        errors.append(f"python-dotenv: {e}")

    try:
        import sentence_transformers  # noqa: F401
    except ImportError as e:
        errors.append(f"sentence-transformers: {e}")

    try:
        import tavily  # noqa: F401
    except ImportError as e:
        errors.append(f"tavily-python: {e}")

    try:
        import kaggle  # noqa: F401
    except ImportError as e:
        errors.append(f"kaggle: {e}")

    if errors:
        print("FAILED imports:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print("All libraries imported successfully.")
    print(f"CUDA available: {cuda_available}")
    print(f"Device: {device}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
