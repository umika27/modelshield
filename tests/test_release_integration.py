"""Focused tests for deterministic evidence-to-release integration."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from core.schemas import ChallengeSpec, EvaluationResult, ModelMetadata
from integration import (
    FailureMemoryAdapter,
    ModelIdentity,
    PublicSeverity,
    ReleaseDecisionAdapter,
    ReleaseEvidence,
    ReleaseVerdict,
    VerifiedFailureArtifact,
    map_internal_policy,
    normalize_severity,
)
from verification import FailureFingerprinter, VerificationResult


BASELINE = ModelIdentity("baseline-id", "baseline", "v1")
CANDIDATE = ModelIdentity("candidate-id", "candidate", "v2")
FINGERPRINT = "sha256:" + "a" * 64


def _evidence(
    *,
    baseline_score: float = 0.82,
    candidate_score: float = 0.49,
    severity: PublicSeverity = PublicSeverity.CRITICAL,
    verified: bool = True,
) -> ReleaseEvidence:
    return ReleaseEvidence(
        failure_fingerprint=FINGERPRINT,
        baseline_score=baseline_score,
        candidate_score=candidate_score,
        severity=severity,
        verified=verified,
        candidate=CANDIDATE,
        baseline=BASELINE,
    )


def _artifact() -> VerifiedFailureArtifact:
    baseline = ModelMetadata("baseline-id", "baseline", "v1", "baseline")
    candidate = ModelMetadata("candidate-id", "candidate", "v2", "candidate")
    evaluation = EvaluationResult(
        evaluation_id="eval-release-1",
        experiment_id="exp-release-1",
        model=candidate,
        baseline=baseline,
        candidate=candidate,
        challenge=ChallengeSpec("challenge-1", "low_light_blur", {"brightness": 0.3, "blur": 0.7}),
        baseline_score=0.82,
        candidate_score=0.49,
        threshold=-0.15,
        status="failure",
        seed=42,
        timestamp=datetime(2026, 8, 30, tzinfo=timezone.utc),
    )
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


def test_no_verified_failures_is_pass():
    decision = ReleaseDecisionAdapter().decide([])
    assert decision.verdict is ReleaseVerdict.PASS
    assert decision.evaluated_findings == 0


def test_moderate_verified_failure_in_review_margin_requires_review():
    # Kartikay policy: threshold = 0.82 * 0.80 = 0.656, review floor = 0.606.
    decision = ReleaseDecisionAdapter().decide(
        [_evidence(candidate_score=0.64, severity=PublicSeverity.HIGH)]
    )
    assert decision.verdict is ReleaseVerdict.REVIEW
    assert decision.findings[0].internal_policy == "warn"


def test_severe_verified_failure_blocks_and_keeps_identity_and_fingerprint():
    decision = ReleaseDecisionAdapter().decide([_evidence()])
    assert decision.verdict is ReleaseVerdict.BLOCK
    assert decision.candidate == CANDIDATE
    assert decision.baseline == BASELINE
    assert decision.triggering_failure_fingerprints == (FINGERPRINT,)


def test_internal_policy_maps_to_product_vocabulary():
    assert map_internal_policy("allow") is ReleaseVerdict.PASS
    assert map_internal_policy("warn") is ReleaseVerdict.REVIEW
    assert map_internal_policy("block") is ReleaseVerdict.BLOCK


def test_severity_mapping_is_deterministic_and_conservative():
    assert normalize_severity("minor") is PublicSeverity.LOW
    assert normalize_severity("major") is PublicSeverity.HIGH
    assert normalize_severity("critical") is PublicSeverity.CRITICAL
    assert normalize_severity("medium") is PublicSeverity.MEDIUM
    with pytest.raises(ValueError, match="unsupported severity"):
        normalize_severity("unknown")


def test_unverified_evidence_cannot_trigger_a_block():
    decision = ReleaseDecisionAdapter().decide([_evidence(verified=False)])
    assert decision.verdict is ReleaseVerdict.PASS
    assert decision.evaluated_findings == 0


def test_failure_memory_record_converts_for_release_evaluation(tmp_path):
    artifact = _artifact()
    memory = FailureMemoryAdapter(tmp_path / "memory.sqlite")
    try:
        failure_id = memory.store(artifact)
        stored = memory.get_failure(failure_id)
        assert stored is not None
        evidence = ReleaseEvidence.from_failure_memory(
            stored,
            candidate=CANDIDATE,
            baseline=BASELINE,
        )
    finally:
        memory.close()

    decision = ReleaseDecisionAdapter().decide([evidence])
    assert decision.verdict is ReleaseVerdict.BLOCK
    assert decision.triggering_failure_fingerprints == (artifact.failure_fingerprint,)


def test_release_decision_serializes_deterministically():
    decision = ReleaseDecisionAdapter().decide([_evidence()])
    assert decision.to_dict()["verdict"] == "BLOCK"
    assert decision.to_dict()["candidate"] == CANDIDATE.__dict__
