"""Focused tests for the canonical verification-to-Failure-Memory adapter."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from core.schemas import ChallengeSpec, EvaluationResult, ModelMetadata
from integration import FailureMemoryAdapter, VerifiedFailureArtifact
from verification import FailureFingerprinter, VerificationResult


def _evaluation(*, status: str = "failure") -> EvaluationResult:
    baseline = ModelMetadata("baseline-id", "baseline", "v1", "baseline")
    candidate = ModelMetadata("candidate-id", "candidate", "v2", "candidate")
    return EvaluationResult(
        evaluation_id="eval-integration-1",
        experiment_id="exp-integration-1",
        model=candidate,
        baseline=baseline,
        candidate=candidate,
        challenge=ChallengeSpec(
            challenge_id="challenge-low-light-blur",
            type="low_light_blur",
            parameters={"brightness": 0.3, "blur": 0.7},
            seed=42,
        ),
        baseline_score=0.82,
        candidate_score=0.49 if status == "failure" else 0.80,
        threshold=-0.15,
        status=status,
        seed=42,
        timestamp=datetime(2026, 8, 30, tzinfo=timezone.utc),
    )


def _artifact(evaluation: EvaluationResult | None = None) -> VerifiedFailureArtifact:
    evaluation = evaluation or _evaluation()
    fingerprint = FailureFingerprinter().generate(evaluation)
    verification = VerificationResult(
        original_evaluation_id=evaluation.evaluation_id,
        experiment_id=evaluation.experiment_id,
        verified=True,
        runs=1,
        successful_reproductions=1,
        results=(evaluation,),
        reason="Failure reproduced in all verification runs.",
        failure_fingerprint=fingerprint,
    )
    return VerifiedFailureArtifact.from_verification(evaluation, verification)


def test_canonical_evaluation_maps_to_failure_memory_and_round_trips(tmp_path):
    artifact = _artifact()
    memory = FailureMemoryAdapter(tmp_path / "memory.sqlite")
    try:
        failure_id = memory.store(
            artifact,
            dataset_reference="cifar10:test",
            preprocessing={"name": "cifar10-eval", "version": "1"},
        )
        stored = memory.get_failure(failure_id)
        capsule = memory.get_capsule(failure_id)
    finally:
        memory.close()

    assert stored is not None
    assert stored["parameters"] == {"blur": 0.7, "brightness": 0.3}
    assert stored["baseline_score"] == 0.82
    assert stored["candidate_score"] == 0.49
    assert stored["fingerprint"] == FailureFingerprinter().generate(artifact.evaluation)
    assert stored["verified"] is True
    assert capsule is not None
    assert capsule["seed"] == 42
    assert capsule["challenge_parameters"] == {
        "parameters": {"blur": 0.7, "brightness": 0.3},
        "type": "low_light_blur",
    }
    assert capsule["evaluation_config"] == {
        "experiment_id": "exp-integration-1",
        "metric": "accuracy",
        "threshold": -0.15,
        "threshold_comparison": "less_than_or_equal",
    }


def test_verified_failure_is_queryable_and_duplicate_fingerprint_is_rejected(tmp_path):
    memory = FailureMemoryAdapter(tmp_path / "memory.sqlite")
    try:
        artifact = _artifact()
        memory.store(artifact)
        assert len(memory.list_failures(verified=True)) == 1
        with pytest.raises(Exception, match="UNIQUE constraint failed"):
            memory.store(artifact)
    finally:
        memory.close()


def test_unverified_failure_cannot_form_an_artifact():
    evaluation = _evaluation()
    verification = VerificationResult(
        original_evaluation_id=evaluation.evaluation_id,
        experiment_id=evaluation.experiment_id,
        verified=False,
        runs=1,
        successful_reproductions=0,
        results=(replace(evaluation, candidate_score=0.80, status="pass"),),
        reason="Failure did not reproduce consistently.",
    )
    with pytest.raises(ValueError, match="verified"):
        VerifiedFailureArtifact.from_verification(evaluation, verification)


def test_passing_evaluation_cannot_form_an_artifact():
    evaluation = _evaluation(status="pass")
    verification = VerificationResult(
        original_evaluation_id=evaluation.evaluation_id,
        experiment_id=evaluation.experiment_id,
        verified=False,
        runs=0,
        successful_reproductions=0,
        results=(),
        reason="Original evaluation is not a failure.",
    )
    with pytest.raises(ValueError, match="failing"):
        VerifiedFailureArtifact.from_verification(evaluation, verification)
