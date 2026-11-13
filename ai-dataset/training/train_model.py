from pathlib import Path
import argparse, json, random, copy, time
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models
from torchvision.models import EfficientNet_B0_Weights
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from tqdm import tqdm

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DATA = ROOT / "ai-dataset" / "split_data"
OUT = ROOT / "ai-dataset" / "training" / "training_results"

def seed_all(seed=42):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)

def device_auto():
    if torch.cuda.is_available(): return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available(): return torch.device("mps")
    return torch.device("cpu")

def make_data(data, batch, workers, device):
    train_tf = transforms.Compose([
        transforms.RandomResizedCrop(224, scale=(0.75, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(12),
        transforms.ColorJitter(brightness=.15, contrast=.15, saturation=.12, hue=.02),
        transforms.ToTensor(),
        transforms.Normalize([.485,.456,.406],[.229,.224,.225])
    ])
    eval_tf = transforms.Compose([
        transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor(),
        transforms.Normalize([.485,.456,.406],[.229,.224,.225])
    ])
    tr = datasets.ImageFolder(data/"train", transform=train_tf)
    va = datasets.ImageFolder(data/"val", transform=eval_tf)
    te = datasets.ImageFolder(data/"test", transform=eval_tf)
    if tr.classes != va.classes or tr.classes != te.classes:
        raise ValueError("Class folders/order must match across train, val and test.")
    common = dict(batch_size=batch, num_workers=workers, pin_memory=device.type=="cuda")
    return tr, DataLoader(tr, shuffle=True, **common), DataLoader(va, shuffle=False, **common), DataLoader(te, shuffle=False, **common)

def epoch(model, loader, loss_fn, device, optimizer=None, scaler=None):
    training = optimizer is not None
    model.train(training)
    losses, ys, ps = 0.0, [], []
    with torch.enable_grad() if training else torch.no_grad():
        for x,y in tqdm(loader, leave=False):
            x,y = x.to(device),y.to(device)
            if training: optimizer.zero_grad(set_to_none=True)
            if device.type=="cuda":
                with torch.autocast(device_type="cuda", dtype=torch.float16):
                    logits=model(x); loss=loss_fn(logits,y)
            else:
                logits=model(x); loss=loss_fn(logits,y)
            if training:
                if device.type=="cuda":
                    scaler.scale(loss).backward(); scaler.step(optimizer); scaler.update()
                else:
                    loss.backward(); optimizer.step()
            losses += loss.item()*x.size(0)
            ps.extend(logits.argmax(1).detach().cpu().tolist()); ys.extend(y.cpu().tolist())
    return losses/len(loader.dataset), accuracy_score(ys,ps), np.array(ys), np.array(ps)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--data",type=Path,default=DEFAULT_DATA)
    ap.add_argument("--epochs",type=int,default=30)
    ap.add_argument("--batch-size",type=int,default=8)
    ap.add_argument("--lr",type=float,default=1e-4)
    ap.add_argument("--patience",type=int,default=6)
    ap.add_argument("--workers",type=int,default=0)
    ap.add_argument("--no-pretrained",action="store_true")
    a=ap.parse_args()
    seed_all(42); device=device_auto(); OUT.mkdir(parents=True,exist_ok=True)
    print("Device:",device)
    if device.type=="cuda": print("GPU:",torch.cuda.get_device_name(0))
    print("Data:",a.data.resolve())
    ds,tr,va,te=make_data(a.data,a.batch_size,a.workers,device)
    names=ds.classes; mapping=ds.class_to_idx
    (OUT/"class_mapping.json").write_text(json.dumps({"classes":names,"class_to_idx":mapping},indent=2))
    weights=None if a.no_pretrained else EfficientNet_B0_Weights.DEFAULT
    model=models.efficientnet_b0(weights=weights)
    model.classifier[1]=nn.Linear(model.classifier[1].in_features,len(names))
    model.to(device)
    criterion=nn.CrossEntropyLoss()
    optimizer=torch.optim.AdamW(model.parameters(),lr=a.lr,weight_decay=1e-4)
    scheduler=torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer,mode="max",factor=.5,patience=2)
    scaler=torch.amp.GradScaler("cuda") if device.type=="cuda" else None
    best=-1; best_epoch=0; waiting=0
    hist={"train_loss":[],"train_accuracy":[],"val_loss":[],"val_accuracy":[],"val_macro_f1":[]}
    for ep in range(1,a.epochs+1):
        start=time.time()
        tl,ta,_,_=epoch(model,tr,criterion,device,optimizer,scaler)
        vl,va_acc,y,p=epoch(model,va,criterion,device)
        _,_,vf1,_=precision_recall_fscore_support(y,p,labels=list(range(len(names))),average="macro",zero_division=0)
        scheduler.step(vf1)
        for k,v in [("train_loss",tl),("train_accuracy",ta),("val_loss",vl),("val_accuracy",va_acc),("val_macro_f1",float(vf1))]: hist[k].append(v)
        print(f"Epoch {ep}/{a.epochs} train_loss={tl:.4f} train_acc={ta:.3f} val_loss={vl:.4f} val_acc={va_acc:.3f} val_macro_f1={vf1:.3f} ({time.time()-start:.1f}s)")
        if vf1>best:
            best=float(vf1); best_epoch=ep; waiting=0
            torch.save({"model_state_dict":model.state_dict(),"class_names":names,"class_to_idx":mapping,"architecture":"efficientnet_b0","input_size":224,"best_epoch":ep,"best_val_macro_f1":best},OUT/"best_model.pth")
        else:
            waiting+=1
            if waiting>=a.patience:
                print("Early stopping."); break
    (OUT/"training_history.json").write_text(json.dumps(hist,indent=2))
    ck=torch.load(OUT/"best_model.pth",map_location=device)
    model.load_state_dict(ck["model_state_dict"])
    # Test set is used only once, after checkpoint selection on validation data.
    tl,acc,y,p=epoch(model,te,criterion,device)
    pr,re,f1,sup=precision_recall_fscore_support(y,p,labels=list(range(len(names))),zero_division=0)
    metrics={"test_loss":tl,"test_accuracy":float(acc),"macro_precision":float(np.mean(pr)),"macro_recall":float(np.mean(re)),"macro_f1":float(np.mean(f1)),"per_class":{n:{"precision":float(pr[i]),"recall":float(re[i]),"f1":float(f1[i]),"support":int(sup[i])} for i,n in enumerate(names)}}
    (OUT/"test_metrics.json").write_text(json.dumps(metrics,indent=2))
    print("Best validation macro-F1:",best,"at epoch",best_epoch)
    print("TEST METRICS:\n",json.dumps(metrics,indent=2))
    print("Saved artifacts:",OUT)

if __name__=="__main__": main()
