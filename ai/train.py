"""Train a real 4-class freshness classifier.
Dataset layout:
datasets/freshness/train/{fresh,ripe,overripe,spoiled}/*.jpg
datasets/freshness/val/{fresh,ripe,overripe,spoiled}/*.jpg
"""
from pathlib import Path
import json
import torch
from torch import nn
from torch.utils.data import DataLoader
from torchvision import datasets, models, transforms

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "datasets" / "freshness"
MODEL_DIR = ROOT / "models"; MODEL_DIR.mkdir(exist_ok=True)
BATCH=24; EPOCHS=12; DEVICE="cuda" if torch.cuda.is_available() else "cpu"

train_tf = transforms.Compose([transforms.Resize((224,224)),transforms.RandomHorizontalFlip(),transforms.RandomRotation(10),transforms.ColorJitter(.15,.15,.12,.05),transforms.ToTensor(),transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
val_tf = transforms.Compose([transforms.Resize((224,224)),transforms.ToTensor(),transforms.Normalize([.485,.456,.406],[.229,.224,.225])])
train_ds=datasets.ImageFolder(DATA/'train',transform=train_tf); val_ds=datasets.ImageFolder(DATA/'val',transform=val_tf)
train_dl=DataLoader(train_ds,batch_size=BATCH,shuffle=True,num_workers=0); val_dl=DataLoader(val_ds,batch_size=BATCH,num_workers=0)
model=models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.DEFAULT)
model.classifier[3]=nn.Linear(model.classifier[3].in_features,len(train_ds.classes)); model.to(DEVICE)
opt=torch.optim.AdamW(model.parameters(),lr=2e-4,weight_decay=1e-4); loss_fn=nn.CrossEntropyLoss(); best=0.0
for epoch in range(EPOCHS):
    model.train(); correct=total=0
    for x,y in train_dl:
        x,y=x.to(DEVICE),y.to(DEVICE); opt.zero_grad(); out=model(x); loss=loss_fn(out,y); loss.backward(); opt.step(); correct+=(out.argmax(1)==y).sum().item(); total+=y.numel()
    model.eval(); vc=vt=0
    with torch.no_grad():
        for x,y in val_dl:
            x,y=x.to(DEVICE),y.to(DEVICE); out=model(x); vc+=(out.argmax(1)==y).sum().item(); vt+=y.numel()
    acc=vc/max(vt,1); print(f"epoch {epoch+1}/{EPOCHS} train={correct/max(total,1):.3f} val={acc:.3f}")
    if acc>best:
        best=acc; scripted=torch.jit.script(model.cpu()); scripted.save(str(MODEL_DIR/'freshfusion_mobilenet_v1.pt')); model.to(DEVICE); (MODEL_DIR/'labels.json').write_text(json.dumps(train_ds.classes))
print(f"best validation accuracy: {best:.3f}")
