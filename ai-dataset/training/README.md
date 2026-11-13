# OMAN FOOD AI — Step 7

Run all commands from the project root (`oman-food-ai/`).

## 1. Check hardware
Windows PowerShell:
```powershell
nvidia-smi
python --version
```
PyTorch will automatically select CUDA, Apple MPS, or CPU.

## 2. Create a virtual environment
Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```
If activation is blocked, use Command Prompt:
```cmd
.venv\Scripts\activate.bat
```

## 3. Install PyTorch
Use https://pytorch.org/get-started/locally/ to select the install command for your OS and CUDA version. If you do not have a supported NVIDIA GPU, choose CPU (or the appropriate Apple option).

Then install the remaining packages:
```bash
pip install -r ai-dataset/training/requirements.txt
```
Check:
```bash
python -c "import torch; print(torch.__version__); print('CUDA:',torch.cuda.is_available()); print('MPS:',hasattr(torch.backends,'mps') and torch.backends.mps.is_available())"
```

## 4. Verify data folders
Ensure the same class folder names exist in:
- ai-dataset/split_data/train/
- ai-dataset/split_data/val/
- ai-dataset/split_data/test/

The script uses folder names as class labels. It reads original images from split_data and does not overwrite processed_data.

## 5. First training run
For an unknown or CPU computer, begin with:
```bash
python ai-dataset/training/train_model.py --epochs 15 --batch-size 8
```
For a CUDA GPU with enough memory:
```bash
python ai-dataset/training/train_model.py --epochs 30 --batch-size 16
```
Windows default workers=0 is intentional. The first run may download ImageNet pretrained weights; internet access is needed. If that download is unavailable, do not silently train from random weights. `--no-pretrained` is provided only for a separate offline experiment and is not recommended for this small dataset.

## 6. Outputs
Created in ai-dataset/training/training_results/:
- best_model.pth
- class_mapping.json
- training_history.json
- test_metrics.json

Generate detailed report and confusion matrix:
```bash
python ai-dataset/training/evaluate_model.py
```

## Method notes
- Training augmentation is applied dynamically only to training images.
- Validation and test use deterministic resize/crop and ImageNet normalization.
- Best checkpoint is selected using validation macro-F1; the test set is held back until model selection is complete.
- With this small dataset, overfitting and limited generalization are possible. Treat test results as an initial estimate.
- Exact duplicates are not the only leakage risk: keep photos from the same original photo session together in one split.
