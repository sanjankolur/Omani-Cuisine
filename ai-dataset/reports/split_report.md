# Oman Food AI — Dataset Stratified Splitting Report

## Split Distribution Overview

- **Total Cleaned Images:** 946
- **Training Set (Train):** 658 (69.6%)
- **Validation Set (Val):** 138 (14.6%)
- **Test Set (Test):** 150 (15.9%)
- **Random Seed:** `42` (fully deterministic and reproducible)

---

## Category-by-Category Split Breakdown

| Category | Total Usable | Train (70%) | Val (15%) | Test (15%) |
|:---|:---:|:---:|:---:|:---:|
| `omani_halwa` | 100 | **70** | 15 | 15 |
| `omani_harees` | 100 | **70** | 15 | 15 |
| `omani_luqaimat` | 98 | **68** | 14 | 16 |
| `omani_madrouba` | 91 | **63** | 13 | 15 |
| `omani_majboos` | 96 | **67** | 14 | 15 |
| `omani_marqooq` | 97 | **67** | 14 | 16 |
| `omani_mashuai` | 95 | **66** | 14 | 15 |
| `omani_mishkak` | 98 | **68** | 14 | 16 |
| `omani_ragag_bread` | 80 | **56** | 12 | 12 |
| `omani_shuwa` | 91 | **63** | 13 | 15 |
| **Total** | **946** | **658** | **138** | **150** |

---

## Split Directory Layout

```text
ai-dataset/split_data/
├── train/          (658 images)
│   ├── omani_halwa/
│   ├── omani_harees/
│   ├── ...
├── val/            (138 images)
│   ├── omani_halwa/
│   └── ...
└── test/           (150 images)
    ├── omani_halwa/
    └── ...
```

- Complete image-level manifest available at: [`ai-dataset/reports/dataset_manifest.csv`](file:///c:/Users/prana/Downloads/oman-food-ai-complete/oman-food-ai/ai-dataset/reports/dataset_manifest.csv)
