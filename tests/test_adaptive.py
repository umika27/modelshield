from datetime import datetime, timezone

import pytest
import torch
from torch import nn

from adaptive import DeterministicInvestigator, Investigator
from challenges import LowLightChallenge
from core.evaluator import EvaluationEngine
from core.schemas import ChallengeSpec, EvaluationResult, ExperimentMetadata, ModelMetadata


def make_spec(challenge_id: str, challenge_type: str, parameters: dict[str, float]) -> ChallengeSpec:
    return ChallengeSpec(challenge_id, challenge_type, parameters, seed=42)


def make_result(challenge: ChallengeSpec, status: str) -> EvaluationResult:
    baseline = ModelMetadata("baseline-id", "baseline", "v1", "baseline")
    candidate = ModelMetadata("candidate-id", "candidate", "v2", "candidate")
    candidate_score = 0.4 if status == "failure" else 0.9
    return EvaluationResult(
        evaluation_id=f"eval-{challenge.challenge_id}-{status}",
        experiment_id="exp-001",
        model=candidate,
        baseline=baseline,
        candidate=candidate,
        challenge=challenge,
        baseline_score=0.9,
        candidate_score=candidate_score,
        threshold=-0.2,
        status=status,
        seed=challenge.seed,
        timestamp=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def available_challenges() -> list[ChallengeSpec]:
    return [
        make_spec("blur-initial", "blur", {"severity": 0.6}),
        make_spec("low-light-initial", "low_light", {"brightness": 0.3}),
        make_spec("combined-initial", "low_light_blur", {"brightness": 0.3, "blur": 0.7}),
    ]


def test_investigator_is_interface_compatible() -> None:
    assert isinstance(DeterministicInvestigator(), Investigator)


def test_no_failure_returns_default_challenge_set(available_challenges) -> None:
    investigator = DeterministicInvestigator()
    history = [make_result(available_challenges[0], "pass")]

    followups = investigator.suggest(history, available_challenges)

    assert followups == available_challenges


def test_low_light_failure_changes_followups_and_targets_brightness(available_challenges) -> None:
    investigator = DeterministicInvestigator()
    without_failure = investigator.suggest([make_result(available_challenges[1], "pass")], available_challenges)
    with_failure = investigator.suggest([make_result(available_challenges[1], "failure")], available_challenges)

    assert without_failure != with_failure
    assert [spec.parameters["brightness"] for spec in with_failure] == [0.2, 0.4]
    assert all(spec.type == "low_light" for spec in with_failure)
    assert all(spec.parent_challenge_id == "low-light-initial" for spec in with_failure)
    assert all(spec.source == "adaptive_investigation" for spec in with_failure)
    assert all(spec.reason == "low_light_failure_refinement" for spec in with_failure)


def test_blur_failure_targets_nearby_severities(available_challenges) -> None:
    followups = DeterministicInvestigator().suggest(
        [make_result(available_challenges[0], "failure")], available_challenges
    )

    assert [spec.parameters["severity"] for spec in followups] == [0.5, 0.7]
    assert all(spec.type == "blur" for spec in followups)
    assert all(spec.parent_challenge_id == "blur-initial" for spec in followups)


def test_combined_failure_refines_combined_condition(available_challenges) -> None:
    followups = DeterministicInvestigator().suggest(
        [make_result(available_challenges[2], "failure")], available_challenges
    )

    assert all(spec.type == "low_light_blur" for spec in followups)
    assert all(spec.parent_challenge_id == "combined-initial" for spec in followups)
    assert all(spec.reason == "low_light_blur_failure_refinement" for spec in followups)
    assert {tuple(sorted(spec.parameters.items())) for spec in followups} == {
        (("blur", 0.7), ("brightness", 0.2)),
        (("blur", 0.8), ("brightness", 0.3)),
    }


def test_separate_low_light_and_blur_failures_add_combined_challenge(available_challenges) -> None:
    followups = DeterministicInvestigator().suggest(
        [make_result(available_challenges[1], "failure"), make_result(available_challenges[0], "failure")],
        available_challenges,
    )

    combined = [spec for spec in followups if spec.reason == "low_light_and_blur_failures"]
    assert len(combined) == 1
    assert combined[0].parameters == {"brightness": 0.3, "blur": 0.6}
    assert combined[0].parent_challenge_id == "low-light-initial"


def test_same_inputs_are_deterministic_and_history_is_not_mutated(available_challenges) -> None:
    history = [make_result(available_challenges[0], "failure")]
    history_before = list(history)
    investigator = DeterministicInvestigator()

    assert investigator.suggest(history, available_challenges) == investigator.suggest(history, available_challenges)
    assert history == history_before


def test_duplicate_followups_are_removed(available_challenges) -> None:
    repeated_failure = make_result(available_challenges[0], "failure")
    followups = DeterministicInvestigator().suggest([repeated_failure, repeated_failure], available_challenges)

    assert len(followups) == 2
    assert len({(spec.type, tuple(sorted(spec.parameters.items()))) for spec in followups}) == 2


class FixedClassModel(nn.Module):
    def __init__(self, class_index: int) -> None:
        super().__init__()
        self.class_index = class_index
        self.received: list[torch.Tensor] = []

    def forward(self, inputs: torch.Tensor) -> torch.Tensor:
        self.received.append(inputs.detach().clone())
        logits = torch.zeros((inputs.shape[0], 2), device=inputs.device)
        logits[:, self.class_index] = 1.0
        return logits


def test_evaluator_consumes_generated_challenge_spec(available_challenges) -> None:
    generated = DeterministicInvestigator().suggest(
        [make_result(available_challenges[1], "failure")], available_challenges
    )[0]
    baseline_info = ModelMetadata("baseline-id", "baseline", "v1", "baseline")
    candidate_info = ModelMetadata("candidate-id", "candidate", "v2", "candidate")
    experiment = ExperimentMetadata(
        experiment_id="exp-generated",
        baseline_model_id="baseline-id",
        candidate_model_id="candidate-id",
        dataset_name="synthetic",
        dataset_version="v1",
        threshold=-0.2,
    )
    baseline = FixedClassModel(0)
    candidate = FixedClassModel(1)

    result = EvaluationEngine().evaluate(
        baseline_model=baseline,
        candidate_model=candidate,
        inputs=torch.full((2, 1, 4, 4), 0.8),
        labels=torch.zeros(2, dtype=torch.long),
        baseline_metadata=baseline_info,
        candidate_metadata=candidate_info,
        experiment=experiment,
        challenge=generated,
        evaluation_id="eval-generated",
        challenge_transform=lambda images, spec: LowLightChallenge().apply(images, spec.parameters, spec.seed),
        timestamp=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
    )

    assert result.challenge == generated
    assert torch.equal(baseline.received[0], candidate.received[0])
    assert result.status == "failure"
