from dataclasses import replace
from datetime import datetime, timezone
import json
import re

import pytest

from core.schemas import ChallengeSpec, EvaluationResult, ModelMetadata
from verification import FailureFingerprinter, VerificationEngine


def make_result(
    *,
    status: str = "failure",
    evaluation_id: str = "eval-001",
    timestamp: datetime | None = None,
    candidate_name: str = "candidate-v2",
    challenge: ChallengeSpec | None = None,
    threshold: float = -0.15,
) -> EvaluationResult:
    challenge = challenge or ChallengeSpec("challenge-001", "blur", {"severity": 0.6}, seed=42)
    baseline = ModelMetadata("baseline-id", "production-v1", "v1", "baseline")
    candidate = ModelMetadata("candidate-id", candidate_name, "v2", "candidate")
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
        seed=challenge.seed,
        timestamp=timestamp or datetime(2026, 8, 29, 10, 0, tzinfo=timezone.utc),
    )


def test_same_evaluation_has_same_sha256_fingerprint_without_mutation() -> None:
    result = make_result()
    before = result.to_json()
    fingerprinter = FailureFingerprinter()

    first = fingerprinter.generate(result)

    assert first == fingerprinter.generate(result)
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", first)
    assert result.to_json() == before


@pytest.mark.parametrize(
    "changed_result",
    [
        lambda: make_result(candidate_name="candidate-v3"),
        lambda: make_result(challenge=ChallengeSpec("challenge-002", "low_light", {"brightness": 0.3}, seed=42)),
        lambda: make_result(challenge=ChallengeSpec("challenge-001", "blur", {"severity": 0.7}, seed=42)),
        lambda: make_result(threshold=-0.1),
    ],
)
def test_stable_failure_configuration_changes_change_fingerprint(changed_result) -> None:
    fingerprinter = FailureFingerprinter()
    assert fingerprinter.generate(make_result()) != fingerprinter.generate(changed_result())


def test_metric_name_participates_in_fingerprint_for_future_contract_metrics() -> None:
    current = make_result()
    future_metric = make_result(evaluation_id="eval-future-metric")
    # Phase 1 currently calculates accuracy only; this verifies canonicalization
    # still includes the contract's metric-name field when more metrics arrive.
    object.__setattr__(future_metric, "metric_name", "f1")

    assert FailureFingerprinter().generate(current) != FailureFingerprinter().generate(future_metric)


def test_timestamp_and_evaluation_id_do_not_change_fingerprint() -> None:
    fingerprinter = FailureFingerprinter()
    original = make_result()
    different_run = make_result(
        evaluation_id="eval-999",
        timestamp=datetime(2026, 8, 30, 10, 0, tzinfo=timezone.utc),
    )

    assert fingerprinter.generate(original) == fingerprinter.generate(different_run)


def test_parameter_order_does_not_change_fingerprint() -> None:
    first = make_result(challenge=ChallengeSpec("challenge-a", "low_light_blur", {"brightness": 0.3, "blur": 0.7}, seed=42))
    second = make_result(challenge=ChallengeSpec("challenge-b", "low_light_blur", {"blur": 0.7, "brightness": 0.3}, seed=42))

    assert FailureFingerprinter().generate(first) == FailureFingerprinter().generate(second)


def test_verified_artifact_is_json_serializable_end_to_end() -> None:
    initial = make_result()
    verification = VerificationEngine().verify(initial, lambda: make_result(evaluation_id="eval-repeat"), runs=2)

    artifact = FailureFingerprinter().build_verified_artifact(initial, verification)

    assert artifact["failure_fingerprint"] == verification.failure_fingerprint
    assert artifact["verification"]["verified"] is True
    assert json.loads(json.dumps(artifact)) == artifact


def test_unverified_failure_cannot_create_verified_artifact() -> None:
    initial = make_result()
    verification = VerificationEngine().verify(initial, lambda: make_result(status="pass"), runs=1)

    with pytest.raises(ValueError, match="verified failure artifact"):
        FailureFingerprinter().build_verified_artifact(initial, verification)
