import torch
import torch.nn as nn
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader
from sklearn.metrics import accuracy_score, classification_report
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "ai-dataset" / "split_data"
TEST_DIR = DATA_DIR / "test"

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

def create_effnet(checkpoint_path, num_classes=10):
    weights = models.EfficientNet_B0_Weights.DEFAULT
    model = models.efficientnet_b0(weights=weights)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.35),
        nn.Linear(in_features, num_classes)
    )
    ckpt = torch.load(checkpoint_path, map_location="cpu")
    if "model_state_dict" in ckpt:
        model.load_state_dict(ckpt["model_state_dict"])
    else:
        model.load_state_dict(ckpt)
    model.eval()
    return model

def main():
    val_tf = transforms.Compose([
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)
    ])

    test_ds = datasets.ImageFolder(TEST_DIR, transform=val_tf)
    test_loader = DataLoader(test_ds, batch_size=16, shuffle=False)
    classes = test_ds.classes

    m1_path = ROOT / "ai-dataset" / "training" / "training_results" / "best_model.pth"
    m2_path = ROOT / "ai-dataset" / "training" / "enhanced_results" / "efficientnet_b0" / "best_model.pth"

    m1 = create_effnet(m1_path)
    m2 = create_effnet(m2_path)

    all_preds_m1, all_preds_m2, all_preds_ens, all_labels = [], [], [], []

    with torch.no_grad():
        for images, labels in test_loader:
            out1 = torch.softmax(m1(images), dim=1)
            out2 = torch.softmax(m2(images), dim=1)
            
            # Simple soft voting ensemble
            out_ens = (out1 * 0.5) + (out2 * 0.5)

            all_preds_m1.extend(out1.argmax(dim=1).tolist())
            all_preds_m2.extend(out2.argmax(dim=1).tolist())
            all_preds_ens.extend(out_ens.argmax(dim=1).tolist())
            all_labels.extend(labels.tolist())

    acc1 = accuracy_score(all_labels, all_preds_m1)
    acc2 = accuracy_score(all_labels, all_preds_m2)
    acc_ens = accuracy_score(all_labels, all_preds_ens)

    print("==================================================")
    print(f"Model 1 (Baseline V1) Test Accuracy: {acc1*100:.2f}%")
    print(f"Model 2 (Enhanced V3) Test Accuracy: {acc2*100:.2f}%")
    print(f"🔥 ENSEMBLE (V1 + V3)  Test Accuracy: {acc_ens*100:.2f}%")
    print("==================================================")
    print("\nEnsemble Classification Report:")
    print(classification_report(all_labels, all_preds_ens, target_names=classes, digits=4))

if __name__ == "__main__":
    main()

