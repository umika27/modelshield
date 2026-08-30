"""Train legitimate CIFAR-10 ResNet18 baseline/candidate checkpoints."""
from __future__ import annotations
import argparse
from pathlib import Path
import torch
from torch import nn
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, models, transforms
from training import TrainingConfig, resolve_device, save_checkpoint, seed_everything, train_one_epoch, write_manifest

def recipe(name: str, profile: str, output: Path, seed: int, device: str) -> TrainingConfig:
    quick = profile == "quick"; return TrainingConfig(run_name=name, epochs=1 if quick else 30, batch_size=64, learning_rate=0.01, weight_decay=0.0001 if name == "baseline" else 0.0005, augmentation=True, output_dir=output, seed=seed, device=device, max_train_samples=1000 if quick else None)
def main() -> None:
    p=argparse.ArgumentParser(); p.add_argument("--profile",choices=("quick","full"),default="quick"); p.add_argument("--model",choices=("baseline","candidate","both"),default="both"); p.add_argument("--data-root",default="./data"); p.add_argument("--download",action="store_true"); p.add_argument("--device",default="auto"); p.add_argument("--output-dir",default="artifacts/models"); p.add_argument("--seed",type=int,default=42); a=p.parse_args()
    outputs={}; device=resolve_device(a.device)
    for name in (("baseline","candidate") if a.model == "both" else (a.model,)):
        c=recipe(name,a.profile,Path(a.output_dir),a.seed, a.device); seed_everything(c.seed)
        steps=[transforms.RandomCrop(32,padding=4),transforms.RandomHorizontalFlip()] if c.augmentation else []; steps += [transforms.ToTensor(),transforms.Normalize((.4914,.4822,.4465),(.247,.243,.261))]
        ds=datasets.CIFAR10(a.data_root,train=True,download=a.download,transform=transforms.Compose(steps)); ds=Subset(ds,range(min(len(ds),c.max_train_samples))) if c.max_train_samples else ds
        model=models.resnet18(weights=None,num_classes=10).to(device); metrics={}
        loader=DataLoader(ds,batch_size=c.batch_size,shuffle=True,generator=torch.Generator().manual_seed(c.seed)); opt=torch.optim.SGD(model.parameters(),lr=c.learning_rate,momentum=.9,weight_decay=c.weight_decay)
        for epoch in range(1,c.epochs+1): metrics=train_one_epoch(model,loader,opt,device); print(name,epoch,metrics)
        path=Path(a.output_dir)/f"cifar10_resnet18_{name}.pth"; save_checkpoint(path,model,c,c.epochs,metrics); outputs[name]={"checkpoint":str(path),"recipe":c.to_dict(),"metrics":metrics}
    write_manifest(Path(a.output_dir)/"manifest.json",{"architecture":"resnet18","dataset":"cifar10","class_names":["airplane","automobile","bird","cat","deer","dog","frog","horse","ship","truck"],"seed":a.seed,"models":outputs})
if __name__ == "__main__": main()
