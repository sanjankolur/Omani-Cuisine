"""
OMAN FOOD AI — EfficientNet-B0 V2 staged fine-tuning

Run from project root:
    python ai-dataset/training/train_model_v2.py --stage1-epochs 5 --stage2-epochs 12 --batch-size 4

Reads only:
    ai-dataset/dataset_v2/split_data/{train,val,test}

Writes to:
    ai-dataset/training/training_results_v2/

V1 checkpoint and dataset are not modified.
"""
from pathlib import Path
import argparse
import copy
import json
import random
import time
import sys

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report

ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "ai-dataset" / "dataset_v2" / "split_data"
OUT_DIR = ROOT / "ai-dataset" / "training" / "training_results_v2"
MEAN = [0.485, 0.456, 0.406]
STD = [0.229, 0.224, 0.225]


def seed_everything(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def make_loaders(batch_size, workers):
    train_tf = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.75, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(12),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.12),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])
    eval_tf = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(MEAN, STD),
    ])

    train_ds = datasets.ImageFolder(DATA_ROOT / "train", transform=train_tf)
    val_ds = datasets.ImageFolder(DATA_ROOT / "val", transform=eval_tf)
    test_ds = datasets.ImageFolder(DATA_ROOT / "test", transform=eval_tf)

    if train_ds.classes != val_ds.classes or train_ds.classes != test_ds.classes:
        raise RuntimeError("Class folders differ between train, val and test.")
    if len(train_ds.classes) != 10:
        raise RuntimeError(f"Expected 10 classes, found {len(train_ds.classes)}.")

    pin = torch.cuda.is_available()
    loaders = {
        "train": DataLoader(train_ds, batch_size=batch_size, shuffle=True,
                            num_workers=workers, pin_memory=pin),
        "val": DataLoader(val_ds, batch_size=batch_size, shuffle=False,
                          num_workers=workers, pin_memory=pin),
        "test": DataLoader(test_ds, batch_size=batch_size, shuffle=False,
                           num_workers=workers, pin_memory=pin),
    }
    return loaders, train_ds.classes, {k: len(v.dataset) for k, v in loaders.items()}


def build_model(num_classes, pretrained=True):
    weights = models.EfficientNet_B0_Weights.DEFAULT if pretrained else None
    model = models.efficientnet_b0(weights=weights)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
    return model


def run_epoch(model, loader, criterion, device, optimizer=None):
    training = optimizer is not None
    model.train(training)
    total_loss = 0.0
    all_true, all_pred = [], []

    context = torch.enable_grad if training else torch.no_grad
    with context():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            if training:
                optimizer.zero_grad(set_to_none=True)

            logits = model(images)
            loss = criterion(logits, labels)

            if training:
                loss.backward()
                optimizer.step()

            total_loss += loss.item() * labels.size(0)
            predictions = logits.argmax(dim=1)
            all_true.extend(labels.detach().cpu().tolist())
            all_pred.extend(predictions.detach().cpu().tolist())

    avg_loss = total_loss / len(loader.dataset)
    accuracy = accuracy_score(all_true, all_pred)
    _, _, macro_f1, _ = precision_recall_fscore_support(
        all_true, all_pred, average="macro", zero_division=0
    )
    return avg_loss, accuracy, macro_f1, all_true, all_pred


def set_stage(model, stage):
    # Stage 1: classifier only.
    for parameter in model.features.parameters():
        parameter.requires_grad = False
    for parameter in model.classifier.parameters():
        parameter.requires_grad = True

    if stage == 2:
        # Fine-tune the final EfficientNet feature blocks, plus the classifier.
        for parameter in model.features[-2:].parameters():
            parameter.requires_grad = True


def train_stage(model, loaders, criterion, device, stage, epochs, patience,
                head_lr, backbone_lr, history, best_state, best_f1):
    set_stage(model, stage)
    if stage == 1:
        params = [{"params": model.classifier.parameters(), "lr": head_lr}]
    else:
        params = [
            {"params": model.features[-2:].parameters(), "lr": backbone_lr},
            {"params": model.classifier.parameters(), "lr": head_lr},
        ]
    optimizer = torch.optim.AdamW(params, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.5, patience=2
    )
    stale = 0

    for epoch in range(1, epochs + 1):
        started = time.time()
        train_loss, train_acc, train_f1, _, _ = run_epoch(
            model, loaders["train"], criterion, device, optimizer
        )
        val_loss, val_acc, val_f1, _, _ = run_epoch(
            model, loaders["val"], criterion, device
        )
        scheduler.step(val_f1)
        record = {
            "stage": stage, "epoch": epoch,
            "train_loss": train_loss, "train_accuracy": train_acc,
            "train_macro_f1": train_f1, "val_loss": val_loss,
            "val_accuracy": val_acc, "val_macro_f1": val_f1,
            "seconds": round(time.time() - started, 1)
        }
        history.append(record)
        print(
            f"Stage {stage} Epoch {epoch}/{epochs} "
            f"train_loss={train_loss:.4f} train_acc={train_acc:.3f} "
            f"val_loss={val_loss:.4f} val_acc={val_acc:.3f} "
            f"val_macro_f1={val_f1:.3f} ({record['seconds']}s)",
            flush=True
        )

        if val_f1 > best_f1:
            best_f1 = val_f1
            best_state = copy.deepcopy(model.state_dict())
            stale = 0
            OUT_DIR.mkdir(parents=True, exist_ok=True)
            torch.save({
                "model_state_dict": best_state,
                "class_names": class_names_global,
                "best_val_macro_f1": best_f1,
                "stage": stage,
                "epoch": epoch,
            }, OUT_DIR / "best_model_v2.pth")
        else:
            stale += 1

        if stale >= patience:
            print(f"Early stopping stage {stage}: no validation macro-F1 improvement for {patience} epochs.")
            break

    if best_state is not None:
        model.load_state_dict(best_state)
    return model, history, best_state, best_f1


class_names_global = []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage1-epochs", type=int, default=5)
    parser.add_argument("--stage2-epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--workers", type=int, default=0)
    parser.add_argument("--patience", type=int, default=4)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if not DATA_ROOT.is_dir():
        sys.exit(f"Dataset V2 not found: {DATA_ROOT}")
    for split in ("train", "val", "test"):
        if not (DATA_ROOT / split).is_dir():
            sys.exit(f"Missing split folder: {DATA_ROOT / split}")

    seed_everything(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else
        "mps" if hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
        else "cpu")
    print("Device:", device)
    print("Dataset:", DATA_ROOT)

    loaders, class_names, sizes = make_loaders(args.batch_size, args.workers)
    global class_names_global
    class_names_global = class_names
    print("Classes:", class_names)
    print("Split sizes:", sizes)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / "class_mapping.json").open("w", encoding="utf-8") as f:
        json.dump({i: name for i, name in enumerate(class_names)}, f, indent=2)

    model = build_model(len(class_names), pretrained=True).to(device)
    criterion = nn.CrossEntropyLoss()
    history = []
    best_state = None
    best_f1 = -1.0

    model, history, best_state, best_f1 = train_stage(
        model, loaders, criterion, device, 1, args.stage1_epochs,
        args.patience, 1e-3, 1e-5, history, best_state, best_f1
    )
    model, history, best_state, best_f1 = train_stage(
        model, loaders, criterion, device, 2, args.stage2_epochs,
        args.patience, 1e-4, 1e-5, history, best_state, best_f1
    )

    if best_state is None:
        sys.exit("No checkpoint was selected. Check the validation data.")

    model.load_state_dict(best_state)
    test_loss, test_acc, test_f1, y_true, y_pred = run_epoch(
        model, loaders["test"], criterion, device
    )
    precision, recall, macro_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="macro", zero_division=0
    )
    report = classification_report(
        y_true, y_pred, target_names=class_names, zero_division=0
    )
    metrics = {
        "test_loss": test_loss,
        "test_accuracy": test_acc,
        "macro_precision": precision,
        "macro_recall": recall,
        "macro_f1": macro_f1,
        "best_validation_macro_f1": best_f1,
        "train_images": sizes["train"],
        "validation_images": sizes["val"],
        "test_images": sizes["test"],
    }
    with (OUT_DIR / "training_history_v2.json").open("w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)
    with (OUT_DIR / "test_metrics_v2.json").open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    (OUT_DIR / "classification_report_v2.txt").write_text(report, encoding="utf-8")

    print("\nV2 TEST METRICS")
    print(json.dumps(metrics, indent=2))
    print("\nCLASSIFICATION REPORT")
    print(report)
    print("Saved artifacts:", OUT_DIR)


if __name__ == "__main__":
    main()
