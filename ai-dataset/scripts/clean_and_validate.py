"""
Data cleaning, validation, and audit script for Oman Food AI dataset.
- Verifies image integrity and format (JPEG/PNG/WEBP)
- Filters out corrupted or unreadable images
- Flags low-resolution images (< 150x150)
- Identifies exact duplicate files via SHA-256 hash
- Copies verified images to `cleaned_data/`
- Places flagged images in `review_images/`
- Generates a summary report in `reports/dataset_report.md` and `reports/dataset_audit.json`
"""

import os
import hashlib
import json
from pathlib import Path
from PIL import Image

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "raw_data"
CLEAN_DIR = BASE_DIR / "cleaned_data"
REVIEW_DIR = BASE_DIR / "review_images"
REPORTS_DIR = BASE_DIR / "reports"

MIN_WIDTH = 150
MIN_HEIGHT = 150

def get_file_hash(filepath: Path) -> str:
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()

def process_dataset():
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)
    REVIEW_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    category_dirs = [d for d in RAW_DIR.iterdir() if d.is_dir() and d.name.endswith("_images")]
    
    total_scanned = 0
    total_valid = 0
    total_duplicates = 0
    total_corrupt = 0
    total_low_res = 0

    seen_hashes = {}
    stats_by_category = {}

    for cat_dir in sorted(category_dirs):
        category_name = cat_dir.name.replace("_images", "")
        clean_cat_dir = CLEAN_DIR / category_name
        review_cat_dir = REVIEW_DIR / category_name

        clean_cat_dir.mkdir(parents=True, exist_ok=True)
        review_cat_dir.mkdir(parents=True, exist_ok=True)

        cat_stats = {
            "scanned": 0,
            "valid": 0,
            "duplicates": 0,
            "corrupt": 0,
            "low_res": 0
        }

        image_files = [f for f in cat_dir.iterdir() if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]

        for img_path in sorted(image_files):
            total_scanned += 1
            cat_stats["scanned"] += 1

            # 1. Check integrity & resolution
            try:
                with Image.open(img_path) as img:
                    img.verify()
                
                # Re-open for size (verify closes or invalidates image pointer)
                with Image.open(img_path) as img:
                    width, height = img.size
                    img_format = img.format

                if width < MIN_WIDTH or height < MIN_HEIGHT:
                    total_low_res += 1
                    cat_stats["low_res"] += 1
                    dest = review_cat_dir / f"lowres_{img_path.name}"
                    dest.write_bytes(img_path.read_bytes())
                    continue

            except Exception:
                total_corrupt += 1
                cat_stats["corrupt"] += 1
                dest = review_cat_dir / f"corrupt_{img_path.name}"
                dest.write_bytes(img_path.read_bytes())
                continue

            # 2. Check duplicate hash
            file_hash = get_file_hash(img_path)
            if file_hash in seen_hashes:
                total_duplicates += 1
                cat_stats["duplicates"] += 1
                dest = review_cat_dir / f"dup_{img_path.name}"
                dest.write_bytes(img_path.read_bytes())
                continue
            
            seen_hashes[file_hash] = img_path.name

            # 3. Valid image -> copy to cleaned_data
            dest = clean_cat_dir / img_path.name
            dest.write_bytes(img_path.read_bytes())
            total_valid += 1
            cat_stats["valid"] += 1

        stats_by_category[category_name] = cat_stats
        print(f"Processed {category_name}: {cat_stats['valid']}/{cat_stats['scanned']} valid")

    # Generate JSON audit report
    audit_data = {
        "summary": {
            "total_scanned": total_scanned,
            "total_valid": total_valid,
            "total_duplicates": total_duplicates,
            "total_low_res": total_low_res,
            "total_corrupt": total_corrupt
        },
        "by_category": stats_by_category
    }

    with open(REPORTS_DIR / "dataset_audit.json", "w", encoding="utf-8") as f:
        json.dump(audit_data, f, indent=2)

    # Generate Markdown report
    md_lines = [
        "# Oman Food AI — Dataset Validation & Audit Report\n",
        f"**Date:** {Path().cwd()}\n",
        "## Summary Overview\n",
        f"- **Total Images Scanned:** {total_scanned}",
        f"- **Verified Valid Images:** {total_valid} ({total_valid / (total_scanned or 1) * 100:.1f}%)",
        f"- **Duplicates Flagged:** {total_duplicates}",
        f"- **Low-Resolution Flagged (< {MIN_WIDTH}x{MIN_HEIGHT}):** {total_low_res}",
        f"- **Corrupt Files:** {total_corrupt}\n",
        "## Category Breakdown\n",
        "| Category | Scanned | Valid Cleaned | Duplicates | Low Res | Corrupt |",
        "|:---|:---:|:---:|:---:|:---:|:---:|"
    ]

    for cat, s in stats_by_category.items():
        md_lines.append(f"| `{cat}` | {s['scanned']} | **{s['valid']}** | {s['duplicates']} | {s['low_res']} | {s['corrupt']} |")

    with open(REPORTS_DIR / "dataset_report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines) + "\n")

    print(f"\n✅ Audit complete! Reports saved to {REPORTS_DIR}")

if __name__ == "__main__":
    process_dataset()
