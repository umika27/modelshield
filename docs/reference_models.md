# Reference CIFAR-10 models

`baseline` and `candidate` are legitimately trained ResNet18 models on CIFAR-10. Both use SGD with momentum, random crop, and horizontal flip augmentation. The sole recipe difference is weight decay: baseline uses `0.0001`; candidate uses `0.0005`. Quick runs use 1,000 samples and one epoch for pipeline verification; full runs use all data and 30 epochs.

Train locally (downloads only with explicit consent):

```bash
python scripts/train_reference_models.py --profile quick --data-root ./data --download
```

Artifacts are written to `artifacts/models/`: two `.pth` checkpoints plus `manifest.json`. Checkpoints store ordered CIFAR-10 class names, architecture, configuration, metrics, and seed. Use the existing CIFAR-10 adapter, `TorchvisionModelAdapter`, and `ComparisonExperimentRunner` to evaluate them.
