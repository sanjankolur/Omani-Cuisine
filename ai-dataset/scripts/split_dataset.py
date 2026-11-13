"""
Dataset Splitting Script for Oman Food AI
- Splits verified images from `ai-dataset/cleaned_data` into:
    • Train set (70% or 80%)
    • Validation set (15% or 10%)
    • Test set (15% or 10%)
- Ensures balanced, stratified representation across all Omani food categories
- Uses a fixed random seed (default: 42) for full reproducibility
- Generates a summary report in `reports/split_report.md` and `reports/dataset_manifest.csv`
"""

import os
import shutil
import random
import csv
import json
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
CLEAN_DIR = BASE_DIR / "cleaned_data"
SPLIT_DIR = BASE_DIR / "split_data"
REPORTS_DIR = BASE_DIR / "reports"

# Split Ratios (Train: 70%, Val: 15%, Test: 15%)
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

RANDOM_SEED = 42

def split_dataset(train_ratio=TRAIN_RATIO, val_ratio=VAL_RATIO, test_ratio=TEST_RATIO, seed=RANDOM_SEED):
    assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 1e-5, "Ratios must sum to 1.0"

    random.seed(seed)

    print("=" * 65)
    print("🇴🇲 Oman Food AI — Dataset Stratified Splitting")
    print(f"Source: {CLEAN_DIR}")
    print(f"Target: {SPLIT_DIR}")
    print(f"Ratios: Train {int(train_ratio*100)}% | Val {int(val_ratio*100)}% | Test {int(test_ratio*100)}%")
    print(f"Seed:   {seed} (reproducible)")
    print("=" * 65)

    # Prepare directories
    for split in ["train", "val", "test"]:
        split_path = SPLIT_DIR / split
        if split_path.exists():
            shutil.rmtree(split_path)
        split_path.mkdir(parents=True, exist_ok=True)

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    category_dirs = [d for d in CLEAN_DIR.iterdir() if d.is_dir()]
    if not category_dirs:
        print("Error: No categories found in cleaned_data.")
        return

    manifest_rows = []
    stats = {}
    total_train = 0
    total_val = 0
    total_test = 0

    valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}

    for cat_dir in sorted(category_dirs):
        category = cat_dir.name
        images = [f for f in cat_dir.iterdir() if f.is_file() and f.suffix.lower() in valid_extensions]
        random.shuffle(images)

        n = len(images)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        n_test = n - n_train - n_val  # Guarantee sum equals total

        train_imgs = images[:n_train]
        val_imgs = images[n_train:n_train + n_val]
        test_imgs = images[n_train + n_val:]

        # Create category subdirectories in each split
        (SPLIT_DIR / "train" / category).mkdir(parents=True, exist_ok=True)
        (SPLIT_DIR / "val" / category).mkdir(parents=True, exist_ok=True)
        (SPLIT_DIR / "test" / category).mkdir(parents=True, exist_ok=True)

        # Copy images and record in manifest
        for img in train_imgs:
            dest = SPLIT_DIR / "train" / category / img.name
            shutil.copy2(img, dest)
            manifest_rows.append({"image_name": img.name, "category": category, "split": "train", "path": str(dest.relative_to(BASE_DIR))})

        for img in val_imgs:
            dest = SPLIT_DIR / "val" / category / img.name
            shutil.copy2(img, dest)
            manifest_rows.append({"image_name": img.name, "category": category, "split": "val", "path": str(dest.relative_to(BASE_DIR))})

        for img in test_imgs:
            dest = SPLIT_DIR / "test" / category / img.name
            shutil.copy2(img, dest)
            manifest_rows.append({"image_name": img.name, "category": category, "split": "test", "path": str(dest.relative_to(BASE_DIR))})

        total_train += len(train_imgs)
        total_val += len(val_imgs)
        total_test += len(test_imgs)

        stats[category] = {
            "total": n,
            "train": len(train_imgs),
            "val": len(val_imgs),
            "test": len(test_imgs)
        }

        print(f"  ✓ {category:<20}: {len(train_imgs):>3} train | {len(val_imgs):>2} val | {len(test_imgs):>2} test (total {n})")

    # Write Manifest CSV
    manifest_path = REPORTS_DIR / "dataset_manifest.csv"
    with open(manifest_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image_name", "category", "split", "path"])
        writer.writeheader()
        writer.writerows(manifest_rows)

    # Write Markdown Report
    total_images = total_train + total_val + total_test
    md_content = f"""# Oman Food AI — Dataset Stratified Splitting Report

## Split Distribution Overview

- **Total Cleaned Images:** {total_images}
- **Training Set (Train):** {total_train} ({total_train/total_images*100:.1f}%)
- **Validation Set (Val):** {total_val} ({total_val/total_images*100:.1f}%)
- **Test Set (Test):** {total_test} ({total_test/total_images*100:.1f}%)
- **Random Seed:** `{seed}` (fully deterministic and reproducible)

---

## Category-by-Category Split Breakdown

| Category | Total Usable | Train (70%) | Val (15%) | Test (15%) |
|:---|:---:|:---:|:---:|:---:|
"""
    for cat, s in stats.items():
        md_content += f"| `{cat}` | {s['total']} | **{s['train']}** | {s['val']} | {s['test']} |\n"

    md_content += f"""| **Total** | **{total_images}** | **{total_train}** | **{total_val}** | **{total_test}** |

---

## Split Directory Layout

```text
ai-dataset/split_data/
├── train/          ({total_train} images)
│   ├── omani_halwa/
│   ├── omani_harees/
│   ├── ...
├── val/            ({total_val} images)
│   ├── omani_halwa/
│   └── ...
└── test/           ({total_test} images)
    ├── omani_halwa/
    └── ...
```

- Complete image-level manifest available at: [`ai-dataset/reports/dataset_manifest.csv`](file:///c:/Users/prana/Downloads/oman-food-ai-complete/oman-food-ai/ai-dataset/reports/dataset_manifest.csv)
"""

    md_path = REPORTS_DIR / "split_report.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print("\n" + "=" * 65)
    print("🎉 Dataset Splitting Completed!")
    print(f"  • Total Images:     {total_images}")
    print(f"  • Train Set:        {total_train} ({total_train/total_images*100:.1f}%)")
    print(f"  • Validation Set:   {total_val} ({total_val/total_images*100:.1f}%)")
    print(f"  • Test Set:         {total_test} ({total_test/total_images*100:.1f}%)")
    print(f"  • Split Output:     {SPLIT_DIR}")
    print(f"  • Split Report:     {md_path}")
    print(f"  • Manifest CSV:     {manifest_path}")
    print("=" * 65)

if __name__ == "__main__":
    split_dataset()

