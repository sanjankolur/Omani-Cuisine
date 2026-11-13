from pathlib import Path
import csv, math, sys
import torch
import torch.nn as nn
from PIL import Image, ImageOps, ImageDraw
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader

ROOT = Path(__file__).resolve().parents[2]
TEST_DIR = ROOT / "ai-dataset" / "split_data" / "test"
RESULTS_DIR = ROOT / "ai-dataset" / "training" / "training_results"
CHECKPOINT_PATH = RESULTS_DIR / "best_model.pth"
OUTPUT_DIR = RESULTS_DIR / "error_analysis"

def read_checkpoint(path, device):
    try:
        ckpt = torch.load(path, map_location=device, weights_only=False)
    except TypeError:
        ckpt = torch.load(path, map_location=device)
    state = ckpt
    if isinstance(ckpt, dict):
        for key in ("model_state_dict", "state_dict", "model", "net"):
            if isinstance(ckpt.get(key), dict):
                state = ckpt[key]
                break
    cleaned = {}
    for k, v in state.items():
        if torch.is_tensor(v):
            while k.startswith(("module.", "model.")):
                k = k.split(".", 1)[1]
            cleaned[k] = v
    return cleaned

def main():
    if not TEST_DIR.is_dir():
        sys.exit(f"Test folder not found: {TEST_DIR}")
    if not CHECKPOINT_PATH.is_file():
        sys.exit(f"Checkpoint not found: {CHECKPOINT_PATH}")

    device = torch.device("cuda" if torch.cuda.is_available() else
        "mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available() else "cpu")
    print("Device:", device)

    transform = transforms.Compose([
        transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])
    ds = datasets.ImageFolder(TEST_DIR, transform=transform)
    classes = ds.classes
    model = models.efficientnet_b0(weights=None)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(classes))
    model.load_state_dict(read_checkpoint(CHECKPOINT_PATH, device), strict=True)
    model.to(device).eval()

    loader = DataLoader(ds, batch_size=8, shuffle=False, num_workers=0)
    rows, offset = [], 0
    with torch.inference_mode():
        for x, y in loader:
            probs = torch.softmax(model(x.to(device)), dim=1)
            conf, pred = probs.max(dim=1)
            for j in range(len(y)):
                path, true_idx = ds.samples[offset + j]
                pi, ti = int(pred[j].cpu()), int(true_idx)
                rows.append({
                    "image_path": str(Path(path).resolve()),
                    "filename": Path(path).name,
                    "actual_label": classes[ti],
                    "predicted_label": classes[pi],
                    "confidence": float(conf[j].cpu()),
                    "correct": pi == ti
                })
            offset += len(y)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    sheet_dir = OUTPUT_DIR / "contact_sheets"
    sheet_dir.mkdir(exist_ok=True)
    errors = [r for r in rows if not r["correct"]]

    with (OUTPUT_DIR / "misclassified_images.csv").open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(errors[0].keys()) if errors else
            ["image_path", "filename", "actual_label", "predicted_label", "confidence", "correct"])
        w.writeheader()
        w.writerows(errors)

    with (OUTPUT_DIR / "summary_by_class.csv").open("w", newline="", encoding="utf-8-sig") as f:
        fields = ["class", "total_test_images", "correct", "incorrect", "recall"]
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for name in classes:
            group = [r for r in rows if r["actual_label"] == name]
            good = sum(r["correct"] for r in group)
            w.writerow({"class": name, "total_test_images": len(group), "correct": good,
                "incorrect": len(group)-good, "recall": round(good/len(group), 4) if group else 0})

    groups = {}
    for r in errors:
        groups.setdefault((r["actual_label"], r["predicted_label"]), []).append(r)

    tw, th, cols = 240, 285, 3
    for (actual, predicted), group in sorted(groups.items()):
        tiles = []
        for r in group:
            try:
                with Image.open(r["image_path"]) as src:
                    im = ImageOps.exif_transpose(src).convert("RGB")
                    im.thumbnail((tw-12, 190))
                    tile = Image.new("RGB", (tw, th), "white")
                    tile.paste(im, ((tw-im.width)//2, 6+(190-im.height)//2))
                    d = ImageDraw.Draw(tile)
                    d.text((8, 202), f"Actual: {actual}", fill="black")
                    d.text((8, 222), f"Predicted: {predicted}", fill="black")
                    d.text((8, 242), f"Confidence: {r['confidence']:.1%}", fill="black")
                    d.text((8, 262), r["filename"][:32], fill="black")
                    tiles.append(tile)
            except Exception as e:
                print("Skipping unreadable image:", r["image_path"], e)
        if tiles:
            sheet = Image.new("RGB", (cols*tw, math.ceil(len(tiles)/cols)*th), "#dddddd")
            for i, tile in enumerate(tiles):
                sheet.paste(tile, ((i%cols)*tw, (i//cols)*th))
            safe = f"{actual}__to__{predicted}".replace("/", "_").replace("\\", "_")
            sheet.save(sheet_dir / f"{safe}.jpg", quality=90)

    print("\nERROR ANALYSIS COMPLETE")
    print(f"Images evaluated: {len(rows)} | Incorrect: {len(errors)} | Accuracy: {1-len(errors)/len(rows):.2%}")
    print("CSV files:", OUTPUT_DIR)
    print("Contact sheets:", sheet_dir)
    print("This script only reads the test images and checkpoint; it does not alter either.")

if __name__ == "__main__":
    main()
