# Oman Food AI — Image Preprocessing & Augmentation Report

## Preprocessing Specification

- **Target Image Size:** 224 × 224 pixels
- **Color Space:** RGB (3 Channels)
- **Tensor Format:** `torch.float32` (PyTorch Tensor `[3, 224, 224]`)
- **Normalization Formula:** `(pixel - mean) / std` using ImageNet coefficients:
  - Mean: `[0.485, 0.456, 0.406]`
  - Std:  `[0.229, 0.224, 0.225]`
- **Total Tensors Verified:** 946 / 946
- **Integrity Verification:** 100% Passed (No NaNs, No Infs, Exact [3, 224, 224] Shape)
- **Processing Time:** 71.27 seconds

---

## Augmentation & Transform Strategy

| Partition | Augmentation Applied | Operations | Purpose |
|---|---|---|---|
| **Train (658 imgs)** | **Yes (Active)** | `RandomResizedCrop(224, scale=(0.85, 1.0))`, `RandomHorizontalFlip(p=0.5)`, `RandomRotation(15°)`, `ColorJitter(0.1)` | Invariance to camera angle, lighting, zoom |
| **Val (138 imgs)** | **No (Clean)** | `Resize(256)`, `CenterCrop(224)`, ImageNet Normalization | Standardized benchmark evaluation |
| **Test (150 imgs)** | **No (Clean)** | `Resize(256)`, `CenterCrop(224)`, ImageNet Normalization | Final unseen generalization metric |

---

## Split Tensor Distribution

| Food Category | Train (Augmented) | Validation | Testing | Total Tensors |
|:---|:---:|:---:|:---:|:---:|
| `omani_halwa` | 70 | 15 | 15 | **100** |
| `omani_harees` | 70 | 15 | 15 | **100** |
| `omani_luqaimat` | 68 | 14 | 16 | **98** |
| `omani_madrouba` | 63 | 13 | 15 | **91** |
| `omani_majboos` | 67 | 14 | 15 | **96** |
| `omani_marqooq` | 67 | 14 | 16 | **97** |
| `omani_mashuai` | 66 | 14 | 15 | **95** |
| `omani_mishkak` | 68 | 14 | 16 | **98** |
| `omani_ragag_bread` | 56 | 12 | 12 | **80** |
| `omani_shuwa` | 63 | 13 | 15 | **91** |
| **Total** | **658** | **138** | **150** | **946** |

---

## Output Directory Structure

```text
ai-dataset/processed_data/
├── class_mapping.json     (index-to-label mapping for 10 Omani dishes)
├── train/                 (658 preprocessed PyTorch tensors)
├── val/                   (138 preprocessed PyTorch tensors)
└── test/                  (150 preprocessed PyTorch tensors)
```

- Report saved to: [`ai-dataset/reports/preprocessing_report.md`](file:///c:/Users/prana/Downloads/oman-food-ai-complete/oman-food-ai/ai-dataset/reports/preprocessing_report.md)