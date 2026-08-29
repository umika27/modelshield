from datetime import datetime, timezone

import pytest
import torch
from torch import nn

from challenges import (
    BlurChallenge,
    BrightnessChallenge,
    ImageChallenge,
    LowLightBlurChallenge,
    LowLightChallenge,
    NoiseChallenge,
    RotationChallenge,
)
from core.evaluator import EvaluationEngine
from core.schemas import ChallengeSpec, ExperimentMetadata, ModelMetadata


@pytest.fixture
def images() -> torch.Tensor:
    return torch.linspace(0, 1, steps=2 * 1 * 5 * 5, dtype=torch.float32).reshape(2, 1, 5, 5)


@pytest.mark.parametrize(
    ("challenge", "parameters"),
    [
        (BlurChallenge(), {"severity": 0.6}),
        (NoiseChallenge(), {"level": 0.1}),
        (BrightnessChallenge(), {"factor": 0.5}),
        (RotationChallenge(), {"degrees": 30}),
        (LowLightChallenge(), {"brightness": 0.3}),
        (LowLightBlurChallenge(), {"brightness": 0.3, "blur": 0.7}),
    ],
)
def test_challenges_implement_interface_preserve_shape_and_do_not_mutate(images, challenge, parameters) -> None:
    original = images.clone()

    output = challenge.apply(images, parameters, seed=42)

    assert isinstance(challenge, ImageChallenge)
    assert output.shape == images.shape
    assert output.dtype == images.dtype
    assert output.device == images.device
    assert torch.equal(images, original)
    assert output.data_ptr() != images.data_ptr()
    assert torch.all((output >= 0) & (output <= 1))


@pytest.mark.parametrize(
    ("challenge", "parameters"),
    [
        (BlurChallenge(), {}),
        (BlurChallenge(), {"severity": 1.1}),
        (NoiseChallenge(), {"level": -0.1}),
        (BrightnessChallenge(), {"factor": "bright"}),
        (RotationChallenge(), {"degrees": 181}),
        (LowLightChallenge(), {"brightness": 1.1}),
        (LowLightBlurChallenge(), {"brightness": 0.4}),
    ],
)
def test_challenges_reject_invalid_parameters(images, challenge, parameters) -> None:
    with pytest.raises((TypeError, ValueError)):
        challenge.apply(images, parameters)


def test_challenges_reject_incompatible_image_representation() -> None:
    with pytest.raises(ValueError, match="N, C, H, W"):
        BlurChallenge().apply(torch.zeros((1, 5, 5)), {"severity": 0.2})
    with pytest.raises(TypeError, match="floating-point"):
        NoiseChallenge().apply(torch.zeros((1, 1, 5, 5), dtype=torch.long), {"level": 0.1})


def test_blur_brightness_rotation_and_low_light_change_expected_images(images) -> None:
    assert not torch.equal(BlurChallenge().apply(images, {"severity": 0.8}), images)
    assert torch.equal(BrightnessChallenge().apply(images, {"factor": 0.5}), images * 0.5)
    assert not torch.equal(RotationChallenge().apply(images, {"degrees": 30}), images)
    assert torch.equal(LowLightChallenge().apply(images, {"brightness": 0.3}), images * 0.3)
    assert not torch.equal(
        LowLightBlurChallenge().apply(images, {"brightness": 0.3, "blur": 0.7}),
        images * 0.3,
    )


def test_noise_is_seeded_and_clamped(images) -> None:
    challenge = NoiseChallenge()
    first = challenge.apply(images, {"level": 0.2}, seed=7)
    second = challenge.apply(images, {"level": 0.2}, seed=7)
    different_seed = challenge.apply(images, {"level": 0.2}, seed=8)

    assert torch.equal(first, second)
    assert not torch.equal(first, different_seed)
    assert torch.all((first >= 0) & (first <= 1))


def test_challenge_spec_preserves_contract_metadata() -> None:
    spec = ChallengeSpec(
        "challenge-002",
        "noise",
        {"level": 0.1},
        parent_challenge_id="challenge-001",
        source="adaptive_follow_up",
        reason="blur_degradation",
        reproducible=True,
        seed=7,
    )

    assert spec.to_dict() == {
        "schema_version": "1.0",
        "challenge_id": "challenge-002",
        "type": "noise",
        "parameters": {"level": 0.1},
        "parent_challenge_id": "challenge-001",
        "source": "adaptive_follow_up",
        "reason": "blur_degradation",
        "reproducible": True,
        "seed": 7,
    }


class RecordingModel(nn.Module):
    def __init__(self, predicted_class: int) -> None:
        super().__init__()
        self.predicted_class = predicted_class
        self.received: list[torch.Tensor] = []

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        self.received.append(inputs.detach().clone())
        logits = torch.zeros((inputs.shape[0], 2), device=inputs.device)
        logits[:, self.predicted_class] = 1.0
        return logits


def test_actual_challenge_integrates_with_evaluation_engine(images) -> None:
    baseline_info = ModelMetadata("baseline-id", "baseline", "v1", "baseline")
    candidate_info = ModelMetadata("candidate-id", "candidate", "v2", "candidate")
    experiment = ExperimentMetadata(
        experiment_id="exp-challenge",
        baseline_model_id="baseline-id",
        candidate_model_id="candidate-id",
        dataset_name="synthetic-images",
        dataset_version="v1",
        threshold=-0.2,
    )
    spec = ChallengeSpec("challenge-llb", "low_light_blur", {"brightness": 0.3, "blur": 0.7}, seed=42)
    baseline = RecordingModel(0)
    candidate = RecordingModel(1)
    original = images.clone()

    result = EvaluationEngine().evaluate(
        baseline_model=baseline,
        candidate_model=candidate,
        inputs=images,
        labels=torch.zeros(images.shape[0], dtype=torch.long),
        baseline_metadata=baseline_info,
        candidate_metadata=candidate_info,
        experiment=experiment,
        challenge=spec,
        evaluation_id="eval-challenge",
        challenge_transform=lambda batch, challenge_spec: LowLightBlurChallenge().apply(
            batch, challenge_spec.parameters, challenge_spec.seed
        ),
        timestamp=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
    )

    assert torch.equal(images, original)
    assert torch.equal(baseline.received[0], candidate.received[0])
    assert not torch.equal(baseline.received[0], images)
    assert result.status == "failure"
    assert result.to_dict()["condition"] == {
        "type": "low_light_blur",
        "parameters": {"brightness": 0.3, "blur": 0.7},
    }
