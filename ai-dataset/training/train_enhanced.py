"""
Oman Food AI — Enhanced Model Training Pipeline (Targeting Higher Accuracy)
Incorporates:
1. RandAugment & Cutout (RandomErasing) for robust visual invariance
2. Label Smoothing Cross-Entropy (prevents logit overconfidence on subtle differences)
3. Two-Stage Fine-Tuning with Differential Learning Rates:
   - Stage 1: Freeze backbone, warm up classifier head
   - Stage 2: Unfreeze with small backbone LR + Cosine Annealing schedule
4. Test-Time Augmentation (TTA) for evaluation & inference boost
5. Supports both EfficientNet-B0 and ConvNeXt-Tiny architectures
"""

import os
import sys
import copy
import json
import time
import argparse
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms
from sklearn.metrics import accuracy_score, precision_recall_fscore_support, classification_report, confusion_matrix

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "ai-dataset" / "split_data"
OUT_DIR = ROOT / "ai-dataset" / "training" / "enhanced_results"

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

def seed_everything(seed=42):
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_transforms(img_size=224):
    train_tf = transforms.Compose([
        transforms.RandomResizedCrop(img_size, scale=(0.7, 1.0)),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomRotation(degrees=15),
        transforms.ColorJitter(brightness=0.18, contrast=0.18, saturation=0.15, hue=0.03),
        transforms.RandAugment(num_ops=2, magnitude=7),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        transforms.RandomErasing(p=0.2, scale=(0.02, 0.2), value="random")
    ])

    val_tf = transforms.Compose([
        transforms.Resize(int(img_size * 1.14)),
        transforms.CenterCrop(img_size),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)
    ])

    return train_tf, val_tf

def create_model(arch="efficientnet_b0", num_classes=10, dropout=0.35):
    if arch == "convnext_tiny":
        weights = models.ConvNeXt_Tiny_Weights.DEFAULT
        model = models.convnext_tiny(weights=weights)
        in_features = model.classifier[2].in_features
        model.classifier[2] = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(in_features, num_classes)
        )
    else:  # default efficientnet_b0
        weights = models.EfficientNet_B0_Weights.DEFAULT
        model = models.efficientnet_b0(weights=weights)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(dropout),
            nn.Linear(in_features, num_classes)
        )
    return model

def predict_with_tta(model, images, device):
    """Test-Time Augmentation: average predictions over original and flipped views."""
    model.eval()
    with torch.no_grad():
        # 1. Original
        logits1 = model(images.to(device))
        probs1 = torch.softmax(logits1, dim=1)

        # 2. Horizontal Flip
        flipped = torch.flip(images, dims=[3])
        logits2 = model(flipped.to(device))
        probs2 = torch.softmax(logits2, dim=1)

        # Average probabilities
        avg_probs = (probs1 + probs2) / 2.0
        return avg_probs

def evaluate(model, loader, device, use_tta=True):
    model.eval()
    all_preds, all_labels = [], []
    with torch.no_grad():
        for images, labels in loader:
            if use_tta:
                probs = predict_with_tta(model, images, device)
                preds = probs.argmax(dim=1).cpu().tolist()
            else:
                logits = model(images.to(device))
                preds = logits.argmax(dim=1).cpu().tolist()
            all_preds.extend(preds)
            all_labels.extend(labels.tolist())

    acc = accuracy_score(all_labels, all_preds)
    p, r, f1, _ = precision_recall_fscore_support(all_labels, all_preds, average="macro", zero_division=0)
    return acc, p, r, f1, all_labels, all_preds

def train_enhanced(arch="efficientnet_b0", epochs_stage1=5, epochs_stage2=20, batch_size=16, data_dir=DATA_DIR):
    seed_everything(42)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    out_path = OUT_DIR / arch
    out_path.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print(f"🚀 Enhanced Model Training: {arch.upper()}")
    print(f"Device: {device} | Data: {data_dir}")
    print(f"Strategy: Stage 1 ({epochs_stage1} ep) Head Warmup + Stage 2 ({epochs_stage2} ep) Fine-Tuning")
    print(f"Enhancements: RandAugment + Cutout + Label Smoothing (0.1) + TTA")
    print("=" * 65)

    train_tf, val_tf = get_transforms(224)
    train_ds = datasets.ImageFolder(data_dir / "train", transform=train_tf)
    val_ds = datasets.ImageFolder(data_dir / "val", transform=val_tf)
    test_ds = datasets.ImageFolder(data_dir / "test", transform=val_tf)

    classes = train_ds.classes
    num_classes = len(classes)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False, num_workers=0)

    model = create_model(arch, num_classes=num_classes).to(device)
    criterion = nn.CrossEntropyLoss(label_smoothing=0.1)

    # -------------------------------------------------------------
    # STAGE 1: Train Head Only
    # -------------------------------------------------------------
    print("\n--- STAGE 1: Classifier Head Warmup (Backbone Frozen) ---")
    if arch == "convnext_tiny":
        for p in model.features.parameters(): p.requires_grad = False
        head_params = model.classifier.parameters()
    else:
        for p in model.features.parameters(): p.requires_grad = False
        head_params = model.classifier.parameters()

    opt_stage1 = torch.optim.AdamW(head_params, lr=1e-3, weight_decay=1e-2)

    best_val_f1 = 0.0
    best_weights = None

    for ep in range(1, epochs_stage1 + 1):
        model.train()
        losses = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            opt_stage1.zero_grad()
            out = model(images)
            loss = criterion(out, labels)
            loss.backward()
            opt_stage1.step()
            losses += loss.item() * len(labels)

        val_acc, _, _, val_f1, _, _ = evaluate(model, val_loader, device, use_tta=False)
        print(f"Stage 1 [Epoch {ep}/{epochs_stage1}] Loss: {losses/len(train_ds):.4f} | Val Acc: {val_acc*100:.2f}% | Val F1: {val_f1*100:.2f}%")
        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_weights = copy.deepcopy(model.state_dict())

    # -------------------------------------------------------------
    # STAGE 2: Full Network Fine-Tuning with Differential LRs
    # -------------------------------------------------------------
    print("\n--- STAGE 2: Full Network Fine-Tuning (Differential LRs + Cosine Decay) ---")
    if best_weights:
        model.load_state_dict(best_weights)

    # Unfreeze all parameters
    for p in model.parameters():
        p.requires_grad = True

    if arch == "convnext_tiny":
        backbone_params = model.features.parameters()
        head_params = model.classifier.parameters()
    else:
        backbone_params = model.features.parameters()
        head_params = model.classifier.parameters()

    opt_stage2 = torch.optim.AdamW([
        {"params": backbone_params, "lr": 3e-5},
        {"params": head_params, "lr": 3e-4}
    ], weight_decay=1e-3)

    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(opt_stage2, T_max=epochs_stage2, eta_min=1e-6)

    for ep in range(1, epochs_stage2 + 1):
        model.train()
        losses = 0.0
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            opt_stage2.zero_grad()
            out = model(images)
            loss = criterion(out, labels)
            loss.backward()
            opt_stage2.step()
            losses += loss.item() * len(labels)

        scheduler.step()
        val_acc, _, _, val_f1, _, _ = evaluate(model, val_loader, device, use_tta=True)
        print(f"Stage 2 [Epoch {ep}/{epochs_stage2}] Loss: {losses/len(train_ds):.4f} | Val Acc (TTA): {val_acc*100:.2f}% | Val F1: {val_f1*100:.2f}%")

        if val_f1 > best_val_f1:
            best_val_f1 = val_f1
            best_weights = copy.deepcopy(model.state_dict())

    # -------------------------------------------------------------
    # FINAL EVALUATION ON UNSEEN TEST SET
    # -------------------------------------------------------------
    print("\n" + "=" * 65)
    print("🏆 FINAL EVALUATION ON UNSEEN TEST SET")
    print("=" * 65)
    model.load_state_dict(best_weights)

    # 1. Standard evaluation
    test_acc_std, test_p_std, test_r_std, test_f1_std, _, _ = evaluate(model, test_loader, device, use_tta=False)
    print(f"Standard Test Accuracy: {test_acc_std*100:.2f}% | Macro F1: {test_f1_std*100:.2f}%")

    # 2. Test-Time Augmentation (TTA) evaluation
    test_acc_tta, test_p_tta, test_r_tta, test_f1_tta, y_true, y_pred = evaluate(model, test_loader, device, use_tta=True)
    print(f"🌟 TTA Test Accuracy:    {test_acc_tta*100:.2f}% | Macro F1: {test_f1_tta*100:.2f}%")

    # Save best model checkpoint
    checkpoint_path = out_path / "best_model.pth"
    torch.save({
        "arch": arch,
        "classes": classes,
        "model_state_dict": best_weights,
        "test_accuracy": test_acc_tta,
        "test_macro_f1": test_f1_tta
    }, checkpoint_path)

    # Save classification report
    report_text = classification_report(y_true, y_pred, target_names=classes, digits=4)
    (out_path / "classification_report.txt").write_text(report_text, encoding="utf-8")
    print("\nPer-Class Classification Report:\n")
    print(report_text)

    # Save metrics JSON
    metrics_data = {
        "architecture": arch,
        "test_accuracy_standard": test_acc_std,
        "test_accuracy_tta": test_acc_tta,
        "test_macro_f1": test_f1_tta,
        "test_macro_precision": test_p_tta,
        "test_macro_recall": test_r_tta
    }
    with open(out_path / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics_data, f, indent=2)

    print(f"✅ Checkpoint and report saved to {out_path}")
    return metrics_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--arch", type=str, default="efficientnet_b0", choices=["efficientnet_b0", "convnext_tiny"])
    parser.add_argument("--stage1-epochs", type=int, default=5)
    parser.add_argument("--stage2-epochs", type=int, default=15)
    parser.add_argument("--batch-size", type=int, default=16)
    args = parser.parse_args()

    train_enhanced(
        arch=args.arch,
        epochs_stage1=args.stage1_epochs,
        epochs_stage2=args.stage2_epochs,
        batch_size=args.batch_size
    )

