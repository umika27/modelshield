from datetime import datetime, timezone
import json

import pytest
import torch
from torch import nn

from core.evaluator import EvaluationEngine
from core.schemas import ChallengeSpec, ExperimentMetadata, ModelMetadata


class FixedClassModel(nn.Module):
    def __init__(self, predicted_class: int) -> None:
        super().__init__()
        self.predicted_class = predicted_class
        self.seen_inputs: list[torch.Tensor] = []

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        self.seen_inputs.append(inputs.detach().clone())
        logits = torch.zeros((inputs.shape[0], 2), device=inputs.device)
        logits[:, self.predicted_class] = 1.0
        return logits


class SequenceClassModel(nn.Module):
    def __init__(self, predicted_classes: list[int]) -> None:
        super().__init__()
        self.predicted_classes = predicted_classes

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        logits = torch.zeros((inputs.shape[0], 2), device=inputs.device)
        logits[torch.arange(inputs.shape[0], device=inputs.device), self.predicted_classes] = 1.0
        return logits


@pytest.fixture
def metadata() -> tuple[ModelMetadata, ModelMetadata, ExperimentMetadata, ChallengeSpec]:
    baseline = ModelMetadata("model-baseline", "production-v1", "v1", "baseline")
    candidate = ModelMetadata("model-candidate", "candidate-v2", "v2", "candidate")
    experiment = ExperimentMetadata(
        experiment_id="exp-001",
        baseline_model_id=baseline.model_id,
        candidate_model_id=candidate.model_id,
        dataset_name="unit-data",
        dataset_version="v1",
        threshold=-0.5,
        seed=42,
    )
    challenge = ChallengeSpec("challenge-001", "blur", {"severity": 0.6}, seed=42)
    return baseline, candidate, experiment, challenge


def test_evaluator_compares_models_with_identical_challenged_values(metadata) -> None:
    baseline_info, candidate_info, experiment, challenge = metadata
    baseline = FixedClassModel(0)
    candidate = FixedClassModel(1)
    inputs = torch.zeros((4, 2))
    original_inputs = inputs.clone()
    labels = torch.zeros(4, dtype=torch.long)
    transform_calls = 0

    def transform(batch: torch.Tensor, _challenge: ChallengeSpec) -> torch.Tensor:
        nonlocal transform_calls
        transform_calls += 1
        batch.add_(7)
        return batch

    result = EvaluationEngine().evaluate(
        baseline_model=baseline,
        candidate_model=candidate,
        inputs=inputs,
        labels=labels,
        baseline_metadata=baseline_info,
        candidate_metadata=candidate_info,
        experiment=experiment,
        challenge=challenge,
        evaluation_id="eval-001",
        challenge_transform=transform,
        timestamp=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
    )

    assert transform_calls == 1
    assert torch.equal(inputs, original_inputs)
    assert torch.equal(baseline.seen_inputs[0], candidate.seen_inputs[0])
    assert torch.equal(baseline.seen_inputs[0], torch.full_like(inputs, 7))
    assert result.baseline_score == 1.0
    assert result.candidate_score == 0.0
    assert result.delta == -1.0
    assert result.status == "failure"


def test_evaluator_uses_configured_threshold_boundary(metadata) -> None:
    baseline_info, candidate_info, experiment, challenge = metadata
    result = EvaluationEngine().evaluate(
        baseline_model=FixedClassModel(0),
        candidate_model=SequenceClassModel([0, 1]),
        inputs=torch.zeros((2, 2)),
        labels=torch.tensor([0, 0]),
        baseline_metadata=baseline_info,
        candidate_metadata=candidate_info,
        experiment=experiment,
        challenge=challenge,
        evaluation_id="eval-002",
        timestamp=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
    )

    assert result.baseline_score == 1.0
    assert result.candidate_score == 0.5
    assert result.delta == -0.5
    assert result.status == "failure"


def test_evaluator_replays_reproducible_torch_transform_with_challenge_seed(metadata) -> None:
    baseline_info, candidate_info, experiment, challenge = metadata
    baseline = FixedClassModel(0)
    candidate = FixedClassModel(1)

    def random_transform(batch: torch.Tensor, _challenge: ChallengeSpec) -> torch.Tensor:
        return batch + torch.rand_like(batch)

    engine = EvaluationEngine()
    for evaluation_id in ("eval-seeded-1", "eval-seeded-2"):
        engine.evaluate(
            baseline_model=baseline,
            candidate_model=candidate,
            inputs=torch.zeros((2, 2)),
            labels=torch.zeros(2, dtype=torch.long),
            baseline_metadata=baseline_info,
            candidate_metadata=candidate_info,
            experiment=experiment,
            challenge=challenge,
            evaluation_id=evaluation_id,
            challenge_transform=random_transform,
        )

    assert torch.equal(baseline.seen_inputs[0], baseline.seen_inputs[1])
    assert torch.equal(candidate.seen_inputs[0], candidate.seen_inputs[1])


def test_evaluation_result_serializes_to_shared_contract_shape(metadata) -> None:
    baseline_info, candidate_info, experiment, challenge = metadata
    result = EvaluationEngine().evaluate(
        baseline_model=FixedClassModel(0),
        candidate_model=FixedClassModel(1),
        inputs=torch.zeros((2, 2)),
        labels=torch.tensor([0, 0]),
        baseline_metadata=baseline_info,
        candidate_metadata=candidate_info,
        experiment=experiment,
        challenge=challenge,
        evaluation_id="eval-003",
        timestamp=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
    )

    serialized = json.loads(result.to_json())
    assert set(serialized) == {
        "schema_version", "evaluation_id", "experiment_id", "model", "baseline",
        "candidate", "condition", "metric", "status", "threshold", "reproducibility", "timestamp",
    }
    assert serialized["condition"] == {"type": "blur", "parameters": {"severity": 0.6}}
    assert serialized["metric"] == {
        "name": "accuracy", "baseline_score": 1.0, "candidate_score": 0.0, "delta": -1.0,
    }
    assert serialized["threshold"] == {"value": -0.5, "comparison": "less_than_or_equal"}
    assert serialized["timestamp"] == "2026-08-29T10:00:00Z"
    assert result.to_json() == result.to_json()
