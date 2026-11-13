"""
Oman Food AI — Local PyTorch Computer Vision Classifier
Provides fast, offline deep learning food recognition using trained EfficientNet-B0 weights.
"""

from io import BytesIO
from pathlib import Path
from typing import Dict, Any, List, Optional
import torch
import torch.nn as nn
from torchvision import models, transforms
from PIL import Image

ROOT = Path(__file__).resolve().parents[3]

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

CLASS_NAMES = [
    "omani_halwa",
    "omani_harees",
    "omani_luqaimat",
    "omani_madrouba",
    "omani_majboos",
    "omani_marqooq",
    "omani_mashuai",
    "omani_mishkak",
    "omani_ragag_bread",
    "omani_shuwa"
]

CLASS_META: Dict[str, Dict[str, Any]] = {
    "omani_halwa": {
        "display_name": "Omani Halwa",
        "description": "Luxurious Omani gelatinous sweet infused with saffron, cardamom, rose water, clarified butter (ghee), and toasted almonds.",
        "ingredients": ["sugar", "tapioca starch", "ghee", "rose water", "saffron", "cardamom", "toasted almonds"]
    },
    "omani_harees": {
        "display_name": "Harees",
        "description": "Slow-cooked velvety porridge made from cracked wheat grains and shredded chicken or meat, beaten smooth and drizzled with warm ghee.",
        "ingredients": ["cracked wheat", "chicken or beef", "clarified butter (ghee)", "salt", "cinnamon"]
    },
    "omani_luqaimat": {
        "display_name": "Omani Luqaimat",
        "description": "Crispy golden fried dough dumplings with a soft pillowy center, drenched in sticky date syrup (Dibs) and toasted sesame seeds.",
        "ingredients": ["flour", "yeast", "cardamom", "saffron", "date syrup", "sesame seeds", "oil for frying"]
    },
    "omani_madrouba": {
        "display_name": "Madrouba",
        "description": "A comforting, savory beaten porridge prepared by braising rice, shredded chicken, tomatoes, onions, dried black lime (Loomi), and warm spices.",
        "ingredients": ["rice", "chicken", "dried black lime", "tomatoes", "onions", "ginger", "garlic", "turmeric"]
    },
    "omani_majboos": {
        "display_name": "Majboos",
        "description": "Signature Omani spiced rice dish layered with tender meat or chicken, infused with dried lime (Loomi), saffron, cardamom, cloves, and cinnamon.",
        "ingredients": ["basmati rice", "meat or chicken", "dried black lime", "saffron", "cardamom", "cinnamon", "cloves", "onions"]
    },
    "omani_marqooq": {
        "display_name": "Omani Marqooq",
        "description": "Traditional savory stew of tender thin dough discs simmered in a spiced tomato broth loaded with seasonal vegetables and lamb or chicken.",
        "ingredients": ["unleavened dough", "lamb or chicken", "zucchini", "potatoes", "tomatoes", "loomi", "bizar spice blend"]
    },
    "omani_mashuai": {
        "display_name": "Mashuai",
        "description": "Whole spit-roasted or baked Kingfish seasoned with ground spices, served alongside fragrant turmeric-lemon rice with Loomi gravy.",
        "ingredients": ["kingfish", "basmati rice", "turmeric", "fresh lemon", "dried black lime", "coriander", "garlic"]
    },
    "omani_mishkak": {
        "display_name": "Mishkak",
        "description": "Beloved Omani charcoal-grilled skewers of marinated beef, chicken, or mutton, brushed continuously with a tangy, spicy tamarind glaze.",
        "ingredients": ["beef or mutton cubes", "tamarind sauce", "garlic", "chili powder", "black pepper", "vinegar", "cumin"]
    },
    "omani_ragag_bread": {
        "display_name": "Khubz Ragag",
        "description": "Paper-thin, ultra-crisp unleavened flatbread freshly baked on an iron convex plate (Tawa), often folded with cheese, honey, or egg.",
        "ingredients": ["flour", "water", "salt", "spreadable cheese", "honey", "egg (optional)"]
    },
    "omani_shuwa": {
        "display_name": "Omani Shuwa",
        "description": "Festive centerpiece dish of lamb or goat marinated in spiced date vinegar, wrapped in banana leaves, and slow-cooked for up to 48 hours in an underground fire pit.",
        "ingredients": ["goat or lamb", "garlic", "date vinegar", "coriander", "red chili", "cloves", "cumin", "banana leaves"]
    }
}

_model = None
_eval_transform = None

def _get_transform():
    global _eval_transform
    if _eval_transform is None:
        _eval_transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD)
        ])
    return _eval_transform

def _load_model():
    global _model
    if _model is not None:
        return _model

    # Check candidates for best weights
    candidate_checkpoints = [
        ROOT / "ai-dataset" / "training" / "enhanced_results" / "efficientnet_b0" / "best_model.pth",
        ROOT / "ai-dataset" / "training" / "training_results" / "best_model.pth",
        ROOT / "ai-dataset" / "training" / "training_results_v2" / "best_model_v2.pth"
    ]

    selected_ckpt = None
    for p in candidate_checkpoints:
        if p.exists():
            selected_ckpt = p
            break

    if not selected_ckpt:
        raise FileNotFoundError("No trained model weights (.pth) found in ai-dataset/training/")

    weights = models.EfficientNet_B0_Weights.DEFAULT
    model = models.efficientnet_b0(weights=weights)
    in_features = model.classifier[1].in_features
    model.classifier = nn.Sequential(
        nn.Dropout(0.35),
        nn.Linear(in_features, len(CLASS_NAMES))
    )

    state = torch.load(selected_ckpt, map_location="cpu")
    if isinstance(state, dict) and "model_state_dict" in state:
        model.load_state_dict(state["model_state_dict"])
    elif isinstance(state, dict):
        model.load_state_dict(state)

    model.eval()
    _model = model
    return _model

def classify_food_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Takes raw image bytes, runs PyTorch inference, and returns structured predictions.
    """
    model = _load_model()
    tf = _get_transform()

    pil_img = Image.open(BytesIO(image_bytes)).convert("RGB")
    tensor = tf(pil_img).unsqueeze(0)

    with torch.no_grad():
        logits = model(tensor)
        probs = torch.softmax(logits, dim=1).squeeze(0)

    top_probs, top_indices = torch.topk(probs, k=min(3, len(CLASS_NAMES)))

    best_idx = top_indices[0].item()
    best_prob = float(top_probs[0].item())
    best_key = CLASS_NAMES[best_idx]
    meta = CLASS_META.get(best_key, {
        "display_name": best_key.replace("omani_", "").replace("_", " ").title(),
        "description": "Authentic Omani dish recognized by AI.",
        "ingredients": []
    })

    if best_prob >= 0.70:
        conf_label = "high"
    elif best_prob >= 0.45:
        conf_label = "medium"
    else:
        conf_label = "low"

    top3 = []
    for prob_tensor, idx_tensor in zip(top_probs, top_indices):
        c_key = CLASS_NAMES[idx_tensor.item()]
        c_meta = CLASS_META.get(c_key, {})
        top3.append({
            "key": c_key,
            "dish_name": c_meta.get("display_name", c_key),
            "probability": round(float(prob_tensor.item()) * 100, 1)
        })

    return {
        "dish_name": meta["display_name"],
        "class_key": best_key,
        "confidence": conf_label,
        "confidence_score": round(best_prob, 4),
        "confidence_percentage": round(best_prob * 100, 1),
        "description": meta["description"],
        "likely_ingredients": meta["ingredients"],
        "top3_predictions": top3,
        "notes": f"Recognized using fine-tuned EfficientNet-B0 with {round(best_prob * 100, 1)}% model certainty."
    }
