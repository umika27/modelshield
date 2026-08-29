from dataclasses import replace
from datetime import datetime, timezone

import pytest

from core.schemas import ChallengeSpec, EvaluationResult, ModelMetadata
from verification import VerificationEngine


def make_result(
    *,
    status: str = "failure",
    evaluation_id: str = "eval-001",
    challenge: ChallengeSpec | None = None,
    candidate_name: str = "candidate-v2",
    candidate_version: str = "v2",
    seed: int = 42,
    threshold: float = -0.15,
) -> EvaluationResult:
    challenge = challenge or ChallengeSpec("challenge-001", "blur", {"severity": 0.6}, seed=seed)
    baseline = ModelMetadata("baseline-id", "production-v1", "v1", "baseline")
    candidate = ModelMetadata("candidate-id", candidate_name, candidate_version, "candidate")
    return EvaluationResult(
        evaluation_id=evaluation_id,
        experiment_id="exp-001",
        model=candidate,
        baseline=baseline,
        candidate=candidate,
        challenge=challenge,
        baseline_score=0.9,
        candidate_score=0.4 if status == "failure" else 0.9,
        threshold=threshold,
        status=status,
        seed=seed,
        timestamp=datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
    )


class CallbackSequence:
    def __init__(self, results: list[object]) -> None:
        self.results = results
        self.calls = 0

    def __call__(self) -> object:
        result = self.results[self.calls % len(self.results)]
        self.calls += 1
        return result


def test_pass_is_not_verified_and_does_not_execute_callback() -> None:
    callback = CallbackSequence([make_result()])

    result = VerificationEngine().verify(make_result(status="pass"), callback, runs=3)

    assert result.verified is False
    assert result.runs == 0
    assert result.successful_reproductions == 0
    assert callback.calls == 0
    assert result.failure_fingerprint is None


def test_failure_reproduced_in_all_runs_is_verified() -> None:
    original = make_result()
    callback = CallbackSequence([make_result(evaluation_id="eval-repeat")])

    result = VerificationEngine().verify(original, callback, runs=3)

    assert result.verified is True
    assert result.runs == 3
    assert result.successful_reproductions == 3
    assert callback.calls == 3
    assert result.failure_fingerprint is not None


def test_failure_followed_by_pass_is_not_verified() -> None:
    result = VerificationEngine().verify(make_result(), CallbackSequence([make_result(status="pass")]), runs=2)

    assert result.verified is False
    assert result.successful_reproductions == 0


def test_mixed_results_are_not_verified() -> None:
    result = VerificationEngine().verify(
        make_result(),
        CallbackSequence([make_result(evaluation_id="eval-repeat"), make_result(status="pass")]),
        runs=3,
    )

    assert result.verified is False
    assert result.successful_reproductions == 2


@pytest.mark.parametrize(
    "changed_result",
    [
        lambda: make_result(challenge=ChallengeSpec("challenge-002", "low_light", {"brightness": 0.3}, seed=42)),
        lambda: make_result(challenge=ChallengeSpec("challenge-001", "blur", {"severity": 0.7}, seed=42)),
        lambda: make_result(candidate_name="candidate-v3", candidate_version="v3"),
        lambda: make_result(challenge=ChallengeSpec("challenge-001", "blur", {"severity": 0.6}, seed=7), seed=7),
        lambda: make_result(threshold=-0.1),
    ],
)
def test_mismatched_failure_configuration_is_not_a_reproduction(changed_result) -> None:
    result = VerificationEngine().verify(make_result(), CallbackSequence([changed_result()]), runs=1)

    assert result.verified is False
    assert result.successful_reproductions == 0


@pytest.mark.parametrize("runs", [0, -1, True, "3"])
def test_invalid_run_count_is_rejected(runs) -> None:
    with pytest.raises(ValueError, match="positive integer"):
        VerificationEngine().verify(make_result(), CallbackSequence([make_result()]), runs=runs)


def test_invalid_callback_result_is_rejected() -> None:
    with pytest.raises(TypeError, match="EvaluationResult"):
        VerificationEngine().verify(make_result(), CallbackSequence(["not an evaluation"]), runs=1)


def test_original_result_is_not_mutated_and_results_are_deterministic() -> None:
    original = make_result()
    original_json = original.to_json()
    engine = VerificationEngine()

    first = engine.verify(original, CallbackSequence([make_result(evaluation_id="repeat-a")]), runs=2)
    second = engine.verify(original, CallbackSequence([make_result(evaluation_id="repeat-a")]), runs=2)

    assert original.to_json() == original_json
    assert first.to_dict() == second.to_dict()
