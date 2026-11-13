import os
import shutil
import hashlib
import json
from pathlib import Path
import cv2
import numpy as np
from PIL import Image

# Path configurations as requested
SOURCE = "ai-dataset/raw_data"
OUTPUT = "ai-dataset/cleaned_data"
REVIEW = "ai-dataset/review_images"
REPORTS = "ai-dataset/reports"

# Quality thresholds
MIN_WIDTH = 200
MIN_HEIGHT = 200
BLUR_THRESHOLD = 80.0  # Laplacian variance threshold; lower means blurrier

def get_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash to detect exact duplicate images."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def calculate_blur(image_path: Path) -> float:
    """Calculate the focus measure of the image using Laplacian variance."""
    image = cv2.imread(str(image_path))
    if image is None:
        return 0.0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())

def clean_dataset():
    source_path = Path(SOURCE)
    output_path = Path(OUTPUT)
    review_path = Path(REVIEW)
    reports_path = Path(REPORTS)

    output_path.mkdir(parents=True, exist_ok=True)
    review_path.mkdir(parents=True, exist_ok=True)
    reports_path.mkdir(parents=True, exist_ok=True)

    # Categories in raw_data
    category_dirs = [d for d in source_path.iterdir() if d.is_dir() and d.name.endswith("_images")]
    if not category_dirs:
        # Check if subfolders are without _images suffix
        category_dirs = [d for d in source_path.iterdir() if d.is_dir()]

    print("=" * 60)
    print("🇴🇲 Oman Food AI — Dataset Cleaning & Quality Pipeline")
    print(f"Source Directory:  {source_path}")
    print(f"Cleaned Directory: {output_path}")
    print(f"Review Directory:  {review_path}")
    print(f"Reports Directory: {reports_path}")
    print(f"Thresholds: Min Res {MIN_WIDTH}x{MIN_HEIGHT}px | Blur Threshold: {BLUR_THRESHOLD}")
    print("=" * 60)

    seen_hashes = {}
    stats = {
        "total_scanned": 0,
        "total_cleaned": 0,
        "total_reviewed": 0,
        "reasons": {
            "blurry": 0,
            "low_resolution": 0,
            "corrupt": 0,
            "duplicate": 0
        },
        "by_category": {}
    }

    valid_extensions = {".jpg", ".jpeg", ".png", ".webp"}

    for cat_dir in sorted(category_dirs):
        category_name = cat_dir.name.replace("_images", "")
        cat_clean_dir = output_path / category_name
        cat_review_dir = review_path / category_name

        cat_clean_dir.mkdir(parents=True, exist_ok=True)
        cat_review_dir.mkdir(parents=True, exist_ok=True)

        cat_stats = {
            "scanned": 0,
            "cleaned": 0,
            "reviewed": 0,
            "blurry": 0,
            "low_res": 0,
            "duplicate": 0,
            "corrupt": 0
        }

        image_files = [f for f in cat_dir.iterdir() if f.is_file() and f.suffix.lower() in valid_extensions]

        for img_file in sorted(image_files):
            stats["total_scanned"] += 1
            cat_stats["scanned"] += 1

            # 1. Check if corrupt
            try:
                with Image.open(img_file) as pil_img:
                    pil_img.verify()

                with Image.open(img_file) as pil_img:
                    width, height = pil_img.size
            except Exception:
                stats["reasons"]["corrupt"] += 1
                stats["total_reviewed"] += 1
                cat_stats["corrupt"] += 1
                cat_stats["reviewed"] += 1
                shutil.copy2(img_file, cat_review_dir / f"corrupt_{img_file.name}")
                continue

            # 2. Check resolution
            if width < MIN_WIDTH or height < MIN_HEIGHT:
                stats["reasons"]["low_resolution"] += 1
                stats["total_reviewed"] += 1
                cat_stats["low_res"] += 1
                cat_stats["reviewed"] += 1
                shutil.copy2(img_file, cat_review_dir / f"lowres_{width}x{height}_{img_file.name}")
                continue

            # 3. Check duplicate
            fhash = get_file_hash(img_file)
            if fhash in seen_hashes:
                stats["reasons"]["duplicate"] += 1
                stats["total_reviewed"] += 1
                cat_stats["duplicate"] += 1
                cat_stats["reviewed"] += 1
                shutil.copy2(img_file, cat_review_dir / f"dup_{img_file.name}")
                continue
            seen_hashes[fhash] = img_file.name

            # 4. Check blurriness via OpenCV
            blur_score = calculate_blur(img_file)
            if blur_score < BLUR_THRESHOLD:
                stats["reasons"]["blurry"] += 1
                stats["total_reviewed"] += 1
                cat_stats["blurry"] += 1
                cat_stats["reviewed"] += 1
                shutil.copy2(img_file, cat_review_dir / f"blurry_{int(blur_score)}_{img_file.name}")
                continue

            # Passed all checks -> Copy to cleaned_data
            shutil.copy2(img_file, cat_clean_dir / img_file.name)
            stats["total_cleaned"] += 1
            cat_stats["cleaned"] += 1

        stats["by_category"][category_name] = cat_stats
        print(f"  ✓ {category_name:<20}: {cat_stats['cleaned']:>3} cleaned, {cat_stats['reviewed']:>2} sent to review")

    # Generate JSON Report
    json_report_path = reports_path / "cleaning_report.json"
    with open(json_report_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    # Generate Markdown Report
    md_report_path = reports_path / "cleaning_report.md"
    pass_pct = (stats["total_cleaned"] / (stats["total_scanned"] or 1)) * 100

    md_content = f"""# Oman Food AI — Dataset Cleaning & Quality Report

## Executive Summary

- **Total Images Scanned:** {stats['total_scanned']}
- **Cleaned (Usable Images):** {stats['total_cleaned']} ({pass_pct:.1f}%)
- **Review Images (Flagged):** {stats['total_reviewed']} ({(100 - pass_pct):.1f}%)
- **Raw Data Status:** Unchanged & preserved

### Quality Issues Breakdown

| Flag Type | Count | Description |
|---|---:|---|
| **Blurry** | {stats['reasons']['blurry']} | Laplacian variance < {BLUR_THRESHOLD} (insufficient visual sharpness) |
| **Low Resolution** | {stats['reasons']['low_resolution']} | Image dimension < {MIN_WIDTH}x{MIN_HEIGHT} pixels |
| **Duplicates** | {stats['reasons']['duplicate']} | Identical SHA-256 hash found |
| **Corrupt / Invalid** | {stats['reasons']['corrupt']} | Unreadable or broken image file |

---

## Category Breakdown

| Category | Total Scanned | Cleaned (Usable) | Blurry | Low Res | Duplicates | Corrupt |
|:---|:---:|:---:|:---:|:---:|:---:|:---:|
"""
    for cat, s in stats["by_category"].items():
        md_content += f"| `{cat}` | {s['scanned']} | **{s['cleaned']}** | {s['blurry']} | {s['low_res']} | {s['duplicate']} | {s['corrupt']} |\n"

    md_content += f"""
---
*Generated by `ai-dataset/scripts/clean_dataset.py`*
"""

    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print("\n" + "=" * 60)
    print(f"🎉 Cleaning Complete!")
    print(f"  • Total Scanned: {stats['total_scanned']}")
    print(f"  • Cleaned Images: {stats['total_cleaned']} ({pass_pct:.1f}%)")
    print(f"  • Review Images:  {stats['total_reviewed']}")
    print(f"  • Markdown Report: {md_report_path}")
    print(f"  • JSON Report:     {json_report_path}")
    print("=" * 60)

if __name__ == "__main__":
    clean_dataset()

