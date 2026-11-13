
import csv
import json
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from PIL import Image, ImageDraw
import matplotlib.pyplot as plt
from sklearn.metrics import confusion_matrix, classification_report


# --------------------------------------------------
# 1. PATHS AND SETTINGS
# --------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_ROOT = PROJECT_ROOT / "ai-dataset" / "dataset_v2" / "split_data"
RESULTS_DIR = (
    PROJECT_ROOT
    / "ai-dataset"
    / "training"
    / "training_results_v2"
)

OUTPUT_DIR = RESULTS_DIR / "error_analysis"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

CHECKPOINT_PATH = RESULTS_DIR / "best_model_v2.pth"

BATCH_SIZE = 4
IMAGE_SIZE = 224

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# --------------------------------------------------
# 2. IMAGE TRANSFORM
# --------------------------------------------------

transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(IMAGE_SIZE),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])


# --------------------------------------------------
# 3. LOAD TEST DATA
# --------------------------------------------------

test_dir = DATA_ROOT / "test"

if not test_dir.exists():
    raise FileNotFoundError(f"Test directory not found: {test_dir}")

dataset = datasets.ImageFolder(
    root=str(test_dir),
    transform=transform
)

class_names = dataset.classes
num_classes = len(class_names)

loader = DataLoader(
    dataset,
    batch_size=BATCH_SIZE,
    shuffle=False,
    num_workers=0
)

print("Device:", DEVICE)
print("Test images:", len(dataset))
print("Classes:", class_names)


# --------------------------------------------------
# 4. LOAD MODEL
# --------------------------------------------------

model = models.efficientnet_b0(weights=None)

model.classifier[1] = nn.Linear(
    model.classifier[1].in_features,
    num_classes
)

checkpoint = torch.load(
    CHECKPOINT_PATH,
    map_location=DEVICE
)

state_dict = checkpoint.get("model_state_dict", checkpoint)

model.load_state_dict(state_dict)
model.to(DEVICE)
model.eval()

print("V2 model loaded successfully.")


# --------------------------------------------------
# 5. PREDICT TEST IMAGES
# --------------------------------------------------

true_labels = []
predicted_labels = []
confidence_scores = []

with torch.no_grad():
    for images, labels in loader:

        images = images.to(DEVICE)

        outputs = model(images)
        probabilities = torch.softmax(outputs, dim=1)

        confidences, predictions = torch.max(
            probabilities,
            dim=1
        )

        true_labels.extend(labels.numpy().tolist())
        predicted_labels.extend(predictions.cpu().numpy().tolist())
        confidence_scores.extend(confidences.cpu().numpy().tolist())


# --------------------------------------------------
# 6. CLASSIFICATION REPORT
# --------------------------------------------------

report = classification_report(
    true_labels,
    predicted_labels,
    target_names=class_names,
    digits=4,
    zero_division=0
)

print("\nCLASSIFICATION REPORT")
print(report)

with open(
    OUTPUT_DIR / "classification_report_v2_analysis.txt",
    "w",
    encoding="utf-8"
) as f:
    f.write(report)


# --------------------------------------------------
# 7. CONFUSION MATRIX
# --------------------------------------------------

cm = confusion_matrix(
    true_labels,
    predicted_labels,
    labels=list(range(num_classes))
)

fig, ax = plt.subplots(figsize=(12, 10))

image = ax.imshow(cm, interpolation="nearest")
ax.figure.colorbar(image, ax=ax)

ax.set(
    xticks=range(num_classes),
    yticks=range(num_classes),
    xticklabels=class_names,
    yticklabels=class_names,
    xlabel="Predicted food",
    ylabel="Actual food",
    title="OMAN FOOD AI - V2 Confusion Matrix"
)

plt.setp(
    ax.get_xticklabels(),
    rotation=45,
    ha="right",
    rotation_mode="anchor"
)

threshold = cm.max() / 2 if cm.size else 0

for i in range(num_classes):
    for j in range(num_classes):
        ax.text(
            j,
            i,
            str(cm[i, j]),
            ha="center",
            va="center",
            color="white" if cm[i, j] > threshold else "black"
        )

fig.tight_layout()

plt.savefig(
    OUTPUT_DIR / "confusion_matrix_v2.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close(fig)


# --------------------------------------------------
# 8. SAVE MISCLASSIFIED IMAGES TO CSV
# --------------------------------------------------

errors = []

for index, (true_label, predicted_label, confidence) in enumerate(
    zip(true_labels, predicted_labels, confidence_scores)
):

    if true_label != predicted_label:

        image_path, _ = dataset.samples[index]

        errors.append({
            "image": Path(image_path).name,
            "image_path": image_path,
            "actual_class": class_names[true_label],
            "predicted_class": class_names[predicted_label],
            "confidence": round(float(confidence), 4)
        })


csv_path = OUTPUT_DIR / "misclassified_images_v2.csv"

with open(
    csv_path,
    "w",
    newline="",
    encoding="utf-8"
) as f:

    writer = csv.DictWriter(
        f,
        fieldnames=[
            "image",
            "image_path",
            "actual_class",
            "predicted_class",
            "confidence"
        ]
    )

    writer.writeheader()
    writer.writerows(errors)


# --------------------------------------------------
# 9. CREATE ERROR CONTACT SHEETS
# --------------------------------------------------

CONTACT_DIR = OUTPUT_DIR / "contact_sheets"
CONTACT_DIR.mkdir(exist_ok=True)

THUMB_WIDTH = 220
THUMB_HEIGHT = 220
LABEL_HEIGHT = 65
COLUMNS = 4

for actual_class in class_names:

    class_errors = [
        error for error in errors
        if error["actual_class"] == actual_class
    ]

    if not class_errors:
        continue

    rows = (len(class_errors) + COLUMNS - 1) // COLUMNS

    sheet = Image.new(
        "RGB",
        (
            COLUMNS * THUMB_WIDTH,
            rows * (THUMB_HEIGHT + LABEL_HEIGHT)
        ),
        "white"
    )

    draw = ImageDraw.Draw(sheet)

    for i, error in enumerate(class_errors):

        img = Image.open(error["image_path"]).convert("RGB")
        img.thumbnail((THUMB_WIDTH - 10, THUMB_HEIGHT - 10))

        x = (i % COLUMNS) * THUMB_WIDTH
        y = (i // COLUMNS) * (THUMB_HEIGHT + LABEL_HEIGHT)

        paste_x = x + (THUMB_WIDTH - img.width) // 2
        paste_y = y + (THUMB_HEIGHT - img.height) // 2

        sheet.paste(img, (paste_x, paste_y))

        label = (
            f"Predicted: {error['predicted_class']}\n"
            f"Confidence: {error['confidence']:.2f}"
        )

        draw.text(
            (x + 5, y + THUMB_HEIGHT + 3),
            label,
            fill="black"
        )

    sheet.save(
        CONTACT_DIR / f"{actual_class}_errors.jpg",
        quality=90
    )


# --------------------------------------------------
# 10. SUMMARY
# --------------------------------------------------

accuracy = sum(
    true_label == predicted_label
    for true_label, predicted_label
    in zip(true_labels, predicted_labels)
) / len(true_labels)

summary = {
    "test_images": len(dataset),
    "correct_predictions": len(dataset) - len(errors),
    "incorrect_predictions": len(errors),
    "accuracy": round(accuracy, 4),
    "error_rate": round(len(errors) / len(dataset), 4)
}

with open(
    OUTPUT_DIR / "error_analysis_summary_v2.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(summary, f, indent=4)

print("\nERROR ANALYSIS COMPLETE")
print(json.dumps(summary, indent=4))
print("\nResults saved to:")
print(OUTPUT_DIR)
