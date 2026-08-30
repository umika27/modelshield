"""Bounded discovery orchestration composed from the canonical service."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import replace
from typing import Any
from uuid import uuid4

import torch

from challenges import BlurChallenge, BrightnessChallenge, LowLightBlurChallenge, LowLightChallenge, NoiseChallenge, RotationChallenge
from core.schemas import ChallengeSpec, EvaluationResult
from investigation import InvestigationAction, InvestigationAgent, InvestigationEvidence, InvestigationResult, InvestigationTraceEntry

from .contracts import ModelIdentity
from .service import AnalysisRequest, ModelShieldService


_CHALLENGES = {
    "blur": BlurChallenge,
    "noise": NoiseChallenge,
    "brightness": BrightnessChallenge,
    "rotation": RotationChallenge,
    "low_light": LowLightChallenge,
    "low_light_blur": LowLightBlurChallenge,
}


def _action_key(challenge: ChallengeSpec) -> tuple[str, str, int]:
    """Stable execution identity, independent of agent rationale and IDs."""
    return challenge.type, json.dumps(challenge.parameters, sort_keys=True, separators=(",", ":")), challenge.seed


def validate_action(action: InvestigationAction) -> None:
    """Preflight an action with the actual canonical challenge implementation."""
    if not isinstance(action, InvestigationAction):
        raise TypeError("agent must return an InvestigationAction")
    if action.challenge.type == "clean":
        if action.challenge.parameters:
            raise ValueError("clean challenge does not accept parameters")
        return
    try:
        challenge = _CHALLENGES[action.challenge.type]()
    except KeyError as exc:
        raise ValueError(f"unsupported canonical challenge type '{action.challenge.type}'") from exc
    # This is parameter-only validation using a tiny canonical batch. It never
    # runs a model and does not create evaluation evidence.
    challenge.apply(torch.zeros((1, 3, 2, 2), dtype=torch.float32), action.challenge.parameters, action.challenge.seed)


class InvestigationService:
    """Execute a bounded, agent-directed sequence through ``ModelShieldService``."""

    def __init__(self, service: ModelShieldService, *, max_decision_attempts: int = 20) -> None:
        if not isinstance(service, ModelShieldService):
            raise TypeError("service must be a ModelShieldService")
        if (
            isinstance(max_decision_attempts, bool)
            or not isinstance(max_decision_attempts, int)
            or max_decision_attempts <= 0
        ):
            raise ValueError("max_decision_attempts must be positive")
        self.service = service
        self.max_decision_attempts = max_decision_attempts

    def investigate(
        self,
        request: AnalysisRequest,
        *,
        initial_action: InvestigationAction,
        agent: InvestigationAgent,
        available_challenges: Sequence[ChallengeSpec],
        experiment_budget: int = 5,
    ) -> InvestigationResult:
        """Run canonical experiments until the bounded agent loop terminates."""
        if not isinstance(request, AnalysisRequest):
            raise TypeError("request must be an AnalysisRequest")
        if not isinstance(agent, InvestigationAgent):
            raise TypeError("agent must implement InvestigationAgent")
        if isinstance(experiment_budget, bool) or not isinstance(experiment_budget, int) or experiment_budget <= 0:
            raise ValueError("experiment_budget must be a positive integer")
        challenges = list(available_challenges)
        if any(not isinstance(item, ChallengeSpec) for item in challenges):
            raise TypeError("available_challenges must contain ChallengeSpec objects")

        trace: list[InvestigationTraceEntry] = []
        evaluations: list[EvaluationResult] = []
        evidence: list[InvestigationEvidence] = []
        executed: set[tuple[str, str, int]] = set()
        action: InvestigationAction | None = initial_action
        attempts = 0
        reason = "experiment_budget_exhausted"

        while action is not None and len(evaluations) < experiment_budget:
            attempts += 1
            if attempts > self.max_decision_attempts:
                reason = "decision_attempt_limit_reached"
                break
            try:
                validate_action(action)
            except (TypeError, ValueError) as exc:
                trace.append(InvestigationTraceEntry(action, "rejected", reason=str(exc)))
            else:
                key = _action_key(action.challenge)
                if key in executed:
                    trace.append(InvestigationTraceEntry(action, "skipped", reason="Duplicate effective experiment."))
                else:
                    executed.add(key)
                    evaluation = self._execute(request, action)
                    trace.append(InvestigationTraceEntry(action, "executed", evaluation=evaluation))
                    evaluations.append(evaluation)
                    evidence.append(InvestigationEvidence.from_evaluation(evaluation))

            remaining = experiment_budget - len(evaluations)
            if remaining == 0:
                reason = "experiment_budget_exhausted"
                break
            action = agent.choose_next(tuple(evidence), tuple(challenges), remaining)
            if action is None:
                reason = "agent_terminated"
            elif not isinstance(action, InvestigationAction):
                raise TypeError("agent must return an InvestigationAction or None")

        baseline = candidate = None
        if evaluations:
            first = evaluations[0]
            baseline = ModelIdentity(first.baseline.model_id, first.baseline.name, first.baseline.version)
            candidate = ModelIdentity(first.candidate.model_id, first.candidate.name, first.candidate.version)
        return InvestigationResult(
            investigation_id=f"investigation-{uuid4().hex}",
            initial_action=initial_action,
            trace=tuple(trace),
            evaluations=tuple(evaluations),
            experiment_budget=experiment_budget,
            experiments_executed=len(evaluations),
            termination_reason=reason,
            baseline=baseline,
            candidate=candidate,
        )

    def _execute(self, request: AnalysisRequest, action: InvestigationAction) -> EvaluationResult:
        action_request = replace(
            request,
            challenge_type=action.challenge.type,
            challenge_parameters=dict(action.challenge.parameters),
            seed=action.challenge.seed,
            experiment_id=None,
        )
        result = self.service.run_analysis(action_request, replay_regressions=False)
        return result.evaluation
