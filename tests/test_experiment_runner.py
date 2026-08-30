from pathlib import Path

from PIL import Image
import pytest
import torch
from torch import Tensor, nn

from adaptive import DeterministicInvestigator
from core.schemas import ChallengeSpec, ModelMetadata
from dataset_adapters import ImageFolderAdapter
from experiments import ClassSpace, ComparisonExperimentRunner, ExperimentCompatibilityError, ExperimentConfig, ExperimentExecutionError
from model_adapters import AdapterMetadata, ModelAdapter, PreprocessingSpec, TorchvisionModelAdapter
from verification import FailureFingerprinter, VerificationEngine


class MeanModel(nn.Module):
    def __init__(self, forced_class: int | None = None, output_classes: int = 2) -> None:
        super().__init__()
        self.forced_class, self.output_classes = forced_class, output_classes

    def forward(self, images: Tensor) -> Tensor:
        classes = torch.full((images.shape[0],), self.forced_class, device=images.device) if self.forced_class is not None else (images.mean((1, 2, 3)) >= 0.5).long()
        logits = torch.zeros((images.shape[0], self.output_classes), device=images.device)
        logits[torch.arange(images.shape[0]), classes] = 1.0
        return logits


class TinyAdapter(ModelAdapter):
    def __init__(self, model: nn.Module, num_classes: int = 2) -> None:
        self.model, self._metadata = model, AdapterMetadata("pytorch", "test", "tiny", num_classes, None)
        self.seen: list[Tensor] = []

    @property
    def metadata(self) -> AdapterMetadata:
        return self._metadata

    @property
    def preprocessing(self) -> PreprocessingSpec:
        return PreprocessingSpec((10, 10), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0))

    def preprocess(self, images: Tensor) -> Tensor:
        self.seen.append(images.detach().clone())
        return images.detach().clone()

    def load(self) -> nn.Module:
        return self.model.eval()


def make_folder(root: Path) -> Path:
    for name, value in (("cat", 25), ("dog", 220)):
        folder = root / name
        folder.mkdir(parents=True)
        for index in range(2):
            Image.new("RGB", (10, 10), color=(value + index,) * 3).save(folder / f"{index}.png")
    return root


def make_config(*, threshold: float = -0.15, max_samples: int | None = None, baseline_space=None) -> ExperimentConfig:
    return ExperimentConfig(
        "real-exp", ModelMetadata("base", "baseline", "v1", "baseline"), ModelMetadata("candidate", "candidate", "v2", "candidate"),
        batch_size=2, failure_threshold=threshold, max_samples=max_samples, baseline_class_space=baseline_space,
    )


def make_runner(tmp_path: Path, **config_kwargs):
    dataset = ImageFolderAdapter(root=make_folder(tmp_path / "images"))
    return ComparisonExperimentRunner(make_config(**config_kwargs)), dataset, TinyAdapter(MeanModel()), TinyAdapter(MeanModel(forced_class=0))


def test_clean_metrics_delta_boundary_and_max_samples(tmp_path: Path) -> None:
    runner, dataset, baseline, candidate = make_runner(tmp_path, threshold=-0.5, max_samples=4)
    result = runner.run(baseline_adapter=baseline, candidate_adapter=candidate, dataset_adapter=dataset, challenge_spec=ChallengeSpec("clean", "clean", {}, seed=42))
    assert (result.baseline_correct, result.candidate_correct, result.num_samples) == (4, 2, 4)
    assert result.evaluation_result.delta == -0.5
    assert result.evaluation_result.status == "failure"
    assert result.sample_indices == (0, 1, 2, 3)


def test_partial_sample_limit_and_pass_condition(tmp_path: Path) -> None:
    runner, dataset, baseline, _ = make_runner(tmp_path, max_samples=3)
    candidate = TinyAdapter(MeanModel())
    result = runner.run(baseline_adapter=baseline, candidate_adapter=candidate, dataset_adapter=dataset, challenge_spec=ChallengeSpec("clean", "clean", {}))
    assert result.num_samples == 3
    assert result.sample_indices == (0, 1, 2)
    assert result.evaluation_result.baseline_score == result.evaluation_result.candidate_score == 1.0
    assert result.evaluation_result.status == "pass"


@pytest.mark.parametrize("challenge_type, parameters", [("blur", {"severity": 0.6}), ("noise", {"level": 0.1})])
def test_existing_challenges_execute_and_share_input(tmp_path: Path, monkeypatch, challenge_type, parameters) -> None:
    runner, dataset, baseline, candidate = make_runner(tmp_path)
    calls = 0
    if challenge_type == "blur":
        from challenges import BlurChallenge
        original = BlurChallenge.apply
        def counted(self, *args, **kwargs):
            nonlocal calls
            calls += 1
            return original(self, *args, **kwargs)
        monkeypatch.setattr(BlurChallenge, "apply", counted)
    result = runner.run(baseline_adapter=baseline, candidate_adapter=candidate, dataset_adapter=dataset, challenge_spec=ChallengeSpec("stress", challenge_type, parameters, seed=42))
    assert result.num_samples == 4
    assert torch.equal(baseline.seen[0], candidate.seen[0])
    if challenge_type == "blur":
        assert calls == 2  # Two canonical batches; once per batch, not once per model.


def test_class_space_and_output_mismatches_fail(tmp_path: Path) -> None:
    runner, dataset, baseline, candidate = make_runner(tmp_path, baseline_space=ClassSpace(("dog", "cat")))
    with pytest.raises(ExperimentCompatibilityError, match="class ordering"):
        runner.run(baseline_adapter=baseline, candidate_adapter=candidate, dataset_adapter=dataset, challenge_spec=ChallengeSpec("clean", "clean", {}))
    runner, dataset, baseline, _ = make_runner(tmp_path / "two")
    candidate = TinyAdapter(MeanModel(forced_class=2, output_classes=3), num_classes=2)
    with pytest.raises(ExperimentExecutionError, match="class indices"):
        runner.run(baseline_adapter=baseline, candidate_adapter=candidate, dataset_adapter=dataset, challenge_spec=ChallengeSpec("clean", "clean", {}))


def test_dataset_class_count_mismatch_fails(tmp_path: Path) -> None:
    runner, dataset, baseline, candidate = make_runner(tmp_path)
    candidate = TinyAdapter(MeanModel(), num_classes=3)
    with pytest.raises(ExperimentCompatibilityError, match="expects 3 classes"):
        runner.run(baseline_adapter=baseline, candidate_adapter=candidate, dataset_adapter=dataset, challenge_spec=ChallengeSpec("clean", "clean", {}))


def test_noise_seed_reproduces_challenged_evidence(tmp_path: Path) -> None:
    runner, dataset, baseline, candidate = make_runner(tmp_path)
    spec = ChallengeSpec("noise", "noise", {"level": 0.2}, seed=7)
    runner.run(baseline_adapter=baseline, candidate_adapter=candidate, dataset_adapter=dataset, challenge_spec=spec)
    first = baseline.seen[0].clone()
    runner.run(baseline_adapter=baseline, candidate_adapter=candidate, dataset_adapter=dataset, challenge_spec=spec)
    assert torch.equal(first, baseline.seen[2])


def test_result_is_compatible_with_adaptive_verification_and_fingerprint(tmp_path: Path) -> None:
    runner, dataset, baseline, candidate = make_runner(tmp_path)
    spec = ChallengeSpec("blur", "blur", {"severity": 0.6}, seed=42)
    result = runner.run(baseline_adapter=baseline, candidate_adapter=candidate, dataset_adapter=dataset, challenge_spec=spec).evaluation_result
    assert DeterministicInvestigator().suggest([result], [spec])
    verification = VerificationEngine().verify(result, lambda: result, runs=2)
    assert verification.verified
    assert FailureFingerprinter().generate(result) == verification.failure_fingerprint


def test_real_imagefolder_torchvision_end_to_end(tmp_path: Path) -> None:
    dataset = ImageFolderAdapter(root=make_folder(tmp_path / "images"))
    runner = ComparisonExperimentRunner(make_config(threshold=-1.0))
    result = runner.run(
        baseline_adapter=TorchvisionModelAdapter(architecture="resnet18", num_classes=2),
        candidate_adapter=TorchvisionModelAdapter(architecture="resnet18", num_classes=2),
        dataset_adapter=dataset,
        challenge_spec=ChallengeSpec("clean", "clean", {}),
    )
    assert result.evaluation_result.candidate_score in {0.0, 0.5, 1.0}
