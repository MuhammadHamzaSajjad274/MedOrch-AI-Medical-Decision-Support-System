#!/usr/bin/env python3
"""
Prepare the HAM10000 (skin lesion) dataset for training.

This project expects skin lesion training data in:
  backend/app/services/vision/skin_lesion/data/train_images/{benign,malignant}/

We map:
  - dx == "mel" (melanoma) -> malignant
  - all other dx labels -> benign

Source files (as downloaded) are expected under:
  backend/app/services/vision/skin_lesion/HAM10000_images_part_1/
  backend/app/services/vision/skin_lesion/HAM10000_images_part_2/
  backend/app/services/vision/skin_lesion/HAM10000_metadata.csv
"""

from __future__ import annotations

import csv
import shutil
from pathlib import Path


def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    skin_dir = project_root / "backend" / "app" / "services" / "vision" / "skin_lesion"

    meta_path = skin_dir / "HAM10000_metadata.csv"
    part1 = skin_dir / "HAM10000_images_part_1"
    part2 = skin_dir / "HAM10000_images_part_2"

    if not meta_path.exists():
        print(f"Missing metadata CSV: {meta_path}")
        return 1
    if not part1.exists() and not part2.exists():
        print("Missing image folders. Expected HAM10000_images_part_1/ and/or HAM10000_images_part_2/")
        return 1

    out_root = skin_dir / "data" / "train_images"
    benign_dir = out_root / "benign"
    mal_dir = out_root / "malignant"
    benign_dir.mkdir(parents=True, exist_ok=True)
    mal_dir.mkdir(parents=True, exist_ok=True)

    # Build a fast lookup from image_id -> file path
    lookup: dict[str, Path] = {}
    for d in (part1, part2):
        if not d.exists():
            continue
        for p in d.glob("*.jpg"):
            lookup[p.stem] = p

    copied_benign = 0
    copied_mal = 0
    missing = 0

    with meta_path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if "image_id" not in (reader.fieldnames or []) or "dx" not in (reader.fieldnames or []):
            print(f"Unexpected metadata columns: {reader.fieldnames}")
            print("Expected at least: image_id, dx")
            return 1

        for row in reader:
            image_id = (row.get("image_id") or "").strip()
            dx = (row.get("dx") or "").strip().lower()
            if not image_id:
                continue
            src = lookup.get(image_id)
            if src is None:
                missing += 1
                continue

            is_malignant = dx == "mel"
            dst_dir = mal_dir if is_malignant else benign_dir
            dst = dst_dir / src.name
            if dst.exists():
                continue
            shutil.copy2(src, dst)
            if is_malignant:
                copied_mal += 1
            else:
                copied_benign += 1

    print("Prepared HAM10000 -> binary folders")
    print(f"Output: {out_root}")
    print(f"Copied benign: {copied_benign}")
    print(f"Copied malignant: {copied_mal}")
    print(f"Missing images (metadata referenced, file not found): {missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

