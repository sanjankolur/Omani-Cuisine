import torch
import torch.nn as nn
from torchvision import datasets, models, transforms
from torch.utils.data import DataLoader
from pathlib import Path

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
    classes = test_ds.classes

    m1_path = ROOT / "ai-dataset" / "training" / "training_results" / "best_model.pth"
    m2_path = ROOT / "ai-dataset" / "training" / "enhanced_results" / "efficientnet_b0" / "best_model.pth"

    m1 = create_effnet(m1_path)
    m2 = create_effnet(m2_path)

    confusions = {}
    print(f"Total test samples: {len(test_ds)}")

    with torch.no_grad():
        for idx in range(len(test_ds)):
            img, label = test_ds[idx]
            img_path, _ = test_ds.samples[idx]
            fname = Path(img_path).name
            img_tensor = img.unsqueeze(0)

            out1 = torch.softmax(m1(img_tensor), dim=1)
            out2 = torch.softmax(m2(img_tensor), dim=1)
            out_ens = (out1 + out2) / 2.0
            pred = out_ens.argmax(dim=1).item()

            if pred != label:
                true_name = classes[label]
                pred_name = classes[pred]
                pair = f"{true_name} -> {pred_name}"
                confusions[pair] = confusions.get(pair, 0) + 1

    print("\nTop Confusions in Test Set (True -> Predicted):")
    for pair, count in sorted(confusions.items(), key=lambda x: x[1], reverse=True):
        print(f"  {pair}: {count}")

if __name__ == "__main__":
    main()

