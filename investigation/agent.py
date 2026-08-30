"""Safe contracts for selecting, but never executing, investigations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import json
from typing import Protocol, runtime_checkable

from adaptive import DeterministicInvestigator
from core.schemas import ChallengeSpec, EvaluationResult, ModelMetadata
from integration.contracts import ModelIdentity


@dataclass(frozen=True)
class InvestigationAction:
    """An agent-selected canonical challenge with non-authoritative rationale."""

    challenge: ChallengeSpec
    rationale: str

    def __post_init__(self) -> None:
        if not isinstance(self.challenge, ChallengeSpec):
            raise TypeError("challenge must be a ChallengeSpec")
        if not isinstance(self.rationale, str) or not self.rationale.strip():
            raise ValueError("rationale must be a non-empty string")


@dataclass(frozen=True)
class InvestigationEvidence:
    """Compact, serializable projection of one real ``EvaluationResult``."""

    experiment_id: str
    challenge: ChallengeSpec
    baseline: ModelIdentity
    candidate: ModelIdentity
    baseline_score: float
    candidate_score: float
    delta: float
    status: str
    metric_name: str
    threshold: float
    threshold_comparison: str
    seed: int

    @classmethod
    def from_evaluation(cls, result: EvaluationResult) -> "InvestigationEvidence":
        if not isinstance(result, EvaluationResult):
            raise TypeError("result must be an EvaluationResult")
        return cls(
            experiment_id=result.experiment_id,
            challenge=result.challenge,
            baseline=ModelIdentity(result.baseline.model_id, result.baseline.name, result.baseline.version),
            candidate=ModelIdentity(result.candidate.model_id, result.candidate.name, result.candidate.version),
            baseline_score=result.baseline_score,
            candidate_score=result.candidate_score,
            delta=result.delta,
            status=result.status,
            metric_name=result.metric_name,
            threshold=result.threshold,
            threshold_comparison=result.threshold_comparison,
            seed=result.seed,
        )

    def as_evaluation_result(self) -> EvaluationResult:
        """Reconstruct minimal canonical evidence for deterministic fallback rules.

        This is intentionally used only to adapt the pre-existing selector,
        which reads challenge and failure state; it is never persisted or used
        as authoritative execution evidence.
        """
        baseline = ModelMetadata(self.baseline.model_id, self.baseline.name, self.baseline.version, "baseline")
        candidate = ModelMetadata(self.candidate.model_id, self.candidate.name, self.candidate.version, "candidate")
        return EvaluationResult(
            evaluation_id=f"evidence-{self.experiment_id}-{self.challenge.challenge_id}",
            experiment_id=self.experiment_id,
            model=candidate,
            baseline=baseline,
            candidate=candidate,
            challenge=self.challenge,
            baseline_score=self.baseline_score,
            candidate_score=self.candidate_score,
            threshold=self.threshold,
            status=self.status,
            seed=self.seed,
            threshold_comparison=self.threshold_comparison,
            metric_name=self.metric_name,
        )


@dataclass(frozen=True)
class InvestigationTraceEntry:
    """One proposed action and its deterministic execution disposition."""

    action: InvestigationAction
    state: str
    evaluation: EvaluationResult | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.state not in {"executed", "rejected", "skipped"}:
            raise ValueError("state must be executed, rejected, or skipped")
        if self.state == "executed" and not isinstance(self.evaluation, EvaluationResult):
            raise ValueError("executed trace entries require a real EvaluationResult")
        if self.state != "executed" and self.evaluation is not None:
            raise ValueError("non-executed trace entries cannot contain an EvaluationResult")


@dataclass(frozen=True)
class InvestigationResult:
    """One bounded discovery session, without a competing release verdict."""

    investigation_id: str
    initial_action: InvestigationAction
    trace: tuple[InvestigationTraceEntry, ...]
    evaluations: tuple[EvaluationResult, ...]
    experiment_budget: int
    experiments_executed: int
    termination_reason: str
    baseline: ModelIdentity | None = None
    candidate: ModelIdentity | None = None


@runtime_checkable
class InvestigationAgent(Protocol):
    """Choose a next canonical action using compact prior evidence only."""

    def choose_next(
        self,
        evidence_history: Sequence[InvestigationEvidence],
        available_challenges: Sequence[ChallengeSpec],
        remaining_budget: int,
    ) -> InvestigationAction | None:
        """Return the next action, or ``None`` to end investigation."""


class DeterministicInvestigationAgent:
    """Offline fallback adapter for the existing deterministic investigator."""

    def __init__(self, investigator: DeterministicInvestigator | None = None) -> None:
        self._investigator = investigator or DeterministicInvestigator()

    def choose_next(
        self,
        evidence_history: Sequence[InvestigationEvidence],
        available_challenges: Sequence[ChallengeSpec],
        remaining_budget: int,
    ) -> InvestigationAction | None:
        if remaining_budget <= 0:
            return None
        history = list(evidence_history)
        if any(not isinstance(item, InvestigationEvidence) for item in history):
            raise TypeError("evidence_history must contain InvestigationEvidence objects")
        candidates = self._investigator.suggest(
            [item.as_evaluation_result() for item in history], available_challenges
        )
        executed = {
            (item.challenge.type, json.dumps(item.challenge.parameters, sort_keys=True, separators=(",", ":")), item.seed)
            for item in history
        }
        candidates = [
            candidate
            for candidate in candidates
            if (candidate.type, json.dumps(candidate.parameters, sort_keys=True, separators=(",", ":")), candidate.seed)
            not in executed
        ]
        if not candidates:
            return None
        return InvestigationAction(candidates[0], "Deterministic fallback selected this canonical follow-up.")
