"""
Build OMAN FOOD AI Dataset V2 from review_log.csv.

Run from project root:
    python ai-dataset/training/build_dataset_v2.py

Reads original split_data images and review decisions.
Includes approve + relabel; excludes reject + unsure.
For relabel decisions, the Notes field is interpreted as the intended class.
Two user-confirmed overrides:
  madrouba_023.jpg -> omani_mishkak
  marqooq_020.jpg  -> omani_shuwa

Creates a NEW dataset at ai-dataset/dataset_v2/split_data.
Does not modify V1, the original split_data, or the review log.
"""
from pathlib import Path
from collections import Counter
import csv
import random
import shutil
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = ROOT / "ai-dataset" / "curated_v2" / "review_log.csv"
OUTPUT_ROOT = ROOT / "ai-dataset" / "dataset_v2"
SPLIT_ROOT = OUTPUT_ROOT / "split_data"
REPORT_ROOT = OUTPUT_ROOT / "reports"

SEED = 42
TRAIN_RATIO = 0.70
VAL_RATIO = 0.15

CLASS_NAMES = {
    "halwa": "omani_halwa",
    "harees": "omani_harees",
    "luqaimat": "omani_luqaimat",
    "madrouba": "omani_madrouba",
    "majboos": "omani_majboos",
    "marqooq": "omani_marqooq",
    "mashuai": "omani_mashuai",
    "mishkak": "omani_mishkak",
    "ragag_bread": "omani_ragag_bread",
    "shuwa": "omani_shuwa",
}
OVERRIDES = {
    "madrouba_023.jpg": "omani_mishkak",
    "marqooq_020.jpg": "omani_shuwa",
}
VALID_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def normalize_label(value):
    value = (value or "").strip().lower().replace(" ", "_")
    if value.startswith("omani_"):
        value = value[6:]
    return CLASS_NAMES.get(value)


def image_is_readable(path):
    try:
        with Image.open(path) as im:
            im.verify()
        return True
    except Exception:
        return False


def main():
    if not LOG_PATH.is_file():
        sys.exit(f"Review log not found: {LOG_PATH}")

    with LOG_PATH.open("r", newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))

    if len(rows) != 946:
        print(f"WARNING: expected 946 review rows; found {len(rows)}.")

    accepted = []
    excluded = Counter()
    problems = []

    for row in rows:
        decision = (row.get("decision") or "").strip().lower()
        filename = Path(row.get("source_path", "")).name

        if decision not in ("approve", "relabel"):
            excluded[decision or "missing_decision"] += 1
            continue

        original_label = row.get("original_label", "")
        target_label = original_label

        if decision == "relabel":
            # User confirmed Notes contains intended destination category.
            target_label = normalize_label(row.get("notes", ""))
            if not target_label:
                target_label = normalize_label(row.get("final_label", ""))
            if not target_label:
                target_label = normalize_label(original_label)

        if filename in OVERRIDES:
            target_label = OVERRIDES[filename]

        if target_label not in CLASS_NAMES.values():
            problems.append(f"Unknown target class for {filename}: {target_label}")
            continue

        source = Path(row.get("source_path", ""))
        if not source.is_file():
            problems.append(f"Missing source image: {source}")
            continue

        if source.suffix.lower() not in VALID_EXTS or not image_is_readable(source):
            problems.append(f"Unreadable/unsupported image: {source}")
            continue

        accepted.append({
            "source_path": str(source.resolve()),
            "filename": filename,
            "original_split": row.get("original_split", ""),
            "original_label": original_label,
            "final_label": target_label,
            "decision": decision,
        })

    if problems:
        print("\nProblems found:")
        for item in problems[:30]:
            print(" -", item)
        if len(problems) > 30:
            print(f" ... and {len(problems)-30} more")
        sys.exit("\nBuild stopped. Fix missing/unreadable files before creating V2.")

    if not accepted:
        sys.exit("No approved/relabelled images found.")

    # Stratify into 70/15/15. Deterministic per class and then shuffle each split.
    by_class = {}
    for item in accepted:
        by_class.setdefault(item["final_label"], []).append(item)

    rng = random.Random(SEED)
    splits = {"train": [], "val": [], "test": []}
    for class_name, items in sorted(by_class.items()):
        rng.shuffle(items)
        n = len(items)
        n_train = int(n * TRAIN_RATIO)
        n_val = int(n * VAL_RATIO)
        # Ensure each class has at least one item in each split when possible.
        if n >= 3:
            n_train = max(1, min(n - 2, n_train))
            n_val = max(1, min(n - n_train - 1, n_val))
        train_items = items[:n_train]
        val_items = items[n_train:n_train + n_val]
        test_items = items[n_train + n_val:]
        splits["train"].extend(train_items)
        splits["val"].extend(val_items)
        splits["test"].extend(test_items)

    for split_items in splits.values():
        rng.shuffle(split_items)

    # Refuse to overwrite an existing output, preserving prior work.
    if SPLIT_ROOT.exists() and any(SPLIT_ROOT.iterdir()):
        sys.exit(
            f"Output already exists and is not empty:\n{SPLIT_ROOT}\n"
            "Rename/archive it before rebuilding; this script will not overwrite it."
        )

    manifest = []
    for split_name, split_items in splits.items():
        for index, item in enumerate(split_items, start=1):
            dest_dir = SPLIT_ROOT / split_name / item["final_label"]
            dest_dir.mkdir(parents=True, exist_ok=True)
            # Unique stable filename avoids collisions between source folders.
            dest_name = f"{index:04d}_{Path(item['filename']).name}"
            dest = dest_dir / dest_name
            shutil.copy2(item["source_path"], dest)
            manifest.append({
                "split": split_name,
                "class": item["final_label"],
                "output_path": str(dest.relative_to(OUTPUT_ROOT)),
                "source_path": item["source_path"],
                "original_label": item["original_label"],
                "decision": item["decision"],
            })

    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    with (REPORT_ROOT / "dataset_v2_manifest.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as f:
        fields = ["split", "class", "output_path", "source_path",
                  "original_label", "decision"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(manifest)

    with (REPORT_ROOT / "dataset_v2_summary.csv").open(
        "w", newline="", encoding="utf-8-sig"
    ) as f:
        writer = csv.writer(f)
        writer.writerow(["class", "total", "train", "val", "test"])
        for class_name in sorted(CLASS_NAMES.values()):
            counts = {
                split: sum(1 for x in splits[split] if x["final_label"] == class_name)
                for split in splits
            }
            writer.writerow([
                class_name, sum(counts.values()),
                counts["train"], counts["val"], counts["test"]
            ])

    print("\nDATASET V2 CREATED")
    print("Included images:", len(accepted))
    print("Excluded decisions:", dict(excluded))
    print("Relabel overrides applied:", OVERRIDES)
    print("Output:", SPLIT_ROOT)
    print("\nSplit totals:")
    for name, items in splits.items():
        print(f"  {name}: {len(items)}")
    print("\nClass totals:")
    for class_name in sorted(CLASS_NAMES.values()):
        print(f"  {class_name}: {sum(1 for x in accepted if x['final_label'] == class_name)}")
    print("\nReports:", REPORT_ROOT)
    print("V1 and original split_data were not changed.")


if __name__ == "__main__":
    main()
