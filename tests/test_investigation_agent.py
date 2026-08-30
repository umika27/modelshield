"""Unit coverage for safe investigation contracts and fallback selection."""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone

import pytest

from core.schemas import ChallengeSpec, EvaluationResult, ModelMetadata
from investigation import DeterministicInvestigationAgent, InvestigationAction, InvestigationEvidence


def _result() -> EvaluationResult:
    baseline = ModelMetadata("base:v1", "base", "v1", "baseline")
    candidate = ModelMetadata("candidate:v2", "candidate", "v2", "candidate")
    return EvaluationResult(
        evaluation_id="eval-1", experiment_id="exp-1", model=candidate,
        baseline=baseline, candidate=candidate,
        challenge=ChallengeSpec("low", "low_light", {"brightness": 0.5}, seed=42),
        baseline_score=0.9, candidate_score=0.6, threshold=-0.15,
        status="failure", seed=42, timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def test_evidence_is_grounded_in_real_evaluation_values() -> None:
    result = _result()
    evidence = InvestigationEvidence.from_evaluation(result)
    assert evidence.delta == result.delta
    assert evidence.status == result.status
    assert evidence.challenge == result.challenge
    assert evidence.baseline_score == result.baseline_score
    assert evidence.candidate_score == result.candidate_score


def test_action_requires_a_canonical_spec_and_rationale() -> None:
    with pytest.raises(TypeError):
        InvestigationAction("not-a-spec", "reason")  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        InvestigationAction(ChallengeSpec("x", "blur", {"severity": 0.1}), " ")


def test_deterministic_fallback_adapts_existing_low_light_rule() -> None:
    source = _result()
    agent = DeterministicInvestigationAgent()
    action = agent.choose_next(
        [InvestigationEvidence.from_evaluation(source)],
        [source.challenge],
        remaining_budget=2,
    )
    assert action is not None
    assert action.challenge.type == "low_light"
    assert action.challenge.source == "adaptive_investigation"
    assert action.challenge.parent_challenge_id == "low"
    assert action.rationale.startswith("Deterministic fallback")


def test_deterministic_fallback_respects_no_remaining_budget() -> None:
    assert DeterministicInvestigationAgent().choose_next([], [], 0) is None


def test_deterministic_fallback_does_not_repeat_an_executed_default() -> None:
    source = _result()
    passing = replace(source, candidate_score=0.9, status="pass")
    evidence = InvestigationEvidence.from_evaluation(passing)
    assert DeterministicInvestigationAgent().choose_next([evidence], [source.challenge], 1) is None
