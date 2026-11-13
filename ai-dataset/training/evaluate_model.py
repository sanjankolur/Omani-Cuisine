from pathlib import Path
import torch
import torch.nn as nn
from torchvision import datasets, transforms, models
from torch.utils.data import DataLoader
from sklearn.metrics import classification_report, confusion_matrix, ConfusionMatrixDisplay
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[2]
DATA=ROOT/"ai-dataset"/"split_data"
OUT=ROOT/"ai-dataset"/"training"/"training_results"

def main():
    device=torch.device("cuda" if torch.cuda.is_available() else ("mps" if hasattr(torch.backends,"mps") and torch.backends.mps.is_available() else "cpu"))
    ck=torch.load(OUT/"best_model.pth",map_location=device)
    names=ck["class_names"]
    tf=transforms.Compose([transforms.Resize(256),transforms.CenterCrop(224),transforms.ToTensor(),transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
    ds=datasets.ImageFolder(DATA/"test",transform=tf)
    if ds.classes!=names: raise ValueError("Test class order does not match checkpoint.")
    dl=DataLoader(ds,batch_size=16,shuffle=False,num_workers=0)
    model=models.efficientnet_b0(weights=None)
    model.classifier[1]=nn.Linear(model.classifier[1].in_features,len(names))
    model.load_state_dict(ck["model_state_dict"]); model.to(device).eval()
    y,p=[],[]
    with torch.no_grad():
        for x,t in dl:
            p.extend(model(x.to(device)).argmax(1).cpu().tolist()); y.extend(t.tolist())
    OUT.mkdir(parents=True,exist_ok=True)
    report=classification_report(y,p,target_names=names,zero_division=0)
    (OUT/"classification_report.txt").write_text(report,encoding="utf-8")
    cm=confusion_matrix(y,p,labels=list(range(len(names))))
    fig,ax=plt.subplots(figsize=(12,10))
    ConfusionMatrixDisplay(cm,display_labels=names).plot(ax=ax,xticks_rotation=45,colorbar=False)
    fig.tight_layout(); fig.savefig(OUT/"confusion_matrix.png",dpi=160); plt.close(fig)
    print(report); print("Saved classification report and confusion matrix.")

if __name__=="__main__": main()
