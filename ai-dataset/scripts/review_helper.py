"""
Manual Review Helper Script for Oman Food AI
- Inspects flagged images inside `ai-dataset/review_images`
- Categorizes flagged items by reason: Blurry, Low-Res, Duplicates
- Allows moving an approved image into `cleaned_data`
"""

import sys
import shutil
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
REVIEW_DIR = BASE_DIR / "review_images"
CLEAN_DIR = BASE_DIR / "cleaned_data"

def list_flagged_images():
    print("=" * 65)
    print("🔍 Oman Food AI — Flagged Review Images Summary")
    print(f"Directory: {REVIEW_DIR}")
    print("=" * 65)

    categories = [d for d in REVIEW_DIR.iterdir() if d.is_dir()]
    total_flagged = 0

    for cat_dir in sorted(categories):
        files = list(cat_dir.iterdir())
        if not files:
            continue
        total_flagged += len(files)
        print(f"\n📂 {cat_dir.name} ({len(files)} flagged):")
        for f in sorted(files):
            # Print reason prefix and name
            print(f"   • {f.name}")

    print("\n" + "=" * 65)
    print(f"Total Flagged for Manual Review: {total_flagged} images")
    print("To approve an image and move it into cleaned_data:")
    print("  python ai-dataset/scripts/review_helper.py approve <category> <filename>")
    print("=" * 65)

def approve_image(category: str, filename: str):
    src = REVIEW_DIR / category / filename
    if not src.exists():
        print(f"Error: {src} does not exist.")
        return

    # Strip prefix like blurry_xx_, lowres_xx_, dup_
    cleaned_name = filename
    for prefix in ["dup_", "corrupt_"]:
        if cleaned_name.startswith(prefix):
            cleaned_name = cleaned_name[len(prefix):]
    if cleaned_name.startswith("blurry_"):
        parts = cleaned_name.split("_", 2)
        if len(parts) == 3:
            cleaned_name = parts[2]
    if cleaned_name.startswith("lowres_"):
        parts = cleaned_name.split("_", 2)
        if len(parts) == 3:
            cleaned_name = parts[2]

    dest_dir = CLEAN_DIR / category
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / cleaned_name

    shutil.move(src, dest)
    print(f"✅ Approved and moved: {filename} ➔ {dest}")

if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1].lower() == "approve":
        approve_image(sys.argv[2], sys.argv[3])
    else:
        list_flagged_images()

