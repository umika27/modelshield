"""Explainable, deterministic follow-up selection for verified evaluation evidence."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from core.schemas import ChallengeSpec, EvaluationResult

from .selector import ChallengeSelector


@runtime_checkable
class Investigator(Protocol):
    """Select the next challenge specifications without executing any model."""

    def suggest(
        self,
        failure_history: Sequence[EvaluationResult],
        available_challenges: Sequence[ChallengeSpec],
    ) -> list[ChallengeSpec]:
        """Return deterministic next challenges based only on evaluation evidence."""


class DeterministicInvestigator:
    """Rule-based MVP investigator for failure-driven challenge refinement.

    Rules are intentionally narrow and inspectable: blur failures refine severity,
    low-light failures refine brightness, combined failures refine the combined
    condition, and co-occurring blur/low-light failures introduce their combined
    condition.
    """

    _STEP = 0.1

    def suggest(
        self,
        failure_history: Sequence[EvaluationResult],
        available_challenges: Sequence[ChallengeSpec],
    ) -> list[ChallengeSpec]:
        history = self._validate_history(failure_history)
        defaults = ChallengeSelector.defaults(available_challenges)
        failures = [result for result in history if result.status == "failure"]
        if not failures:
            return defaults

        follow_ups: list[ChallengeSpec] = []
        blur_failures: list[ChallengeSpec] = []
        low_light_failures: list[ChallengeSpec] = []
        for result in failures:
            trigger = result.challenge
            if trigger.type == "blur":
                blur_failures.append(trigger)
                follow_ups.extend(self._blur_refinements(trigger))
            elif trigger.type == "low_light":
                low_light_failures.append(trigger)
                follow_ups.extend(self._low_light_refinements(trigger))
            elif trigger.type == "low_light_blur":
                follow_ups.extend(self._combined_refinements(trigger))

        if blur_failures and low_light_failures:
            follow_ups.append(self._combined_from_separate_failures(low_light_failures[0], blur_failures[0]))
        return ChallengeSelector.unique(follow_ups)

    @staticmethod
    def _validate_history(failure_history: Sequence[EvaluationResult]) -> list[EvaluationResult]:
        history = list(failure_history)
        if any(not isinstance(result, EvaluationResult) for result in history):
            raise TypeError("failure_history must contain EvaluationResult objects")
        return history

    def _blur_refinements(self, trigger: ChallengeSpec) -> list[ChallengeSpec]:
        severity = self._required_value(trigger, "severity")
        return self._nearby_specs(
            trigger,
            challenge_type="blur",
            parameter="severity",
            value=severity,
            reason="blur_failure_refinement",
        )

    def _low_light_refinements(self, trigger: ChallengeSpec) -> list[ChallengeSpec]:
        brightness = self._required_value(trigger, "brightness")
        return self._nearby_specs(
            trigger,
            challenge_type="low_light",
            parameter="brightness",
            value=brightness,
            reason="low_light_failure_refinement",
        )

    def _combined_refinements(self, trigger: ChallengeSpec) -> list[ChallengeSpec]:
        brightness = self._required_value(trigger, "brightness")
        blur = self._required_value(trigger, "blur")
        candidates = (
            {"brightness": self._bounded(brightness - self._STEP), "blur": blur},
            {"brightness": brightness, "blur": self._bounded(blur + self._STEP)},
        )
        return [
            ChallengeSelector.adaptive_spec(
                parent=trigger,
                challenge_type="low_light_blur",
                parameters=parameters,
                reason="low_light_blur_failure_refinement",
            )
            for parameters in candidates
            if parameters != trigger.parameters
        ]

    def _combined_from_separate_failures(self, low_light: ChallengeSpec, blur: ChallengeSpec) -> ChallengeSpec:
        return ChallengeSelector.adaptive_spec(
            parent=low_light,
            challenge_type="low_light_blur",
            parameters={
                "brightness": self._required_value(low_light, "brightness"),
                "blur": self._required_value(blur, "severity"),
            },
            reason="low_light_and_blur_failures",
        )

    def _nearby_specs(
        self,
        trigger: ChallengeSpec,
        *,
        challenge_type: str,
        parameter: str,
        value: float,
        reason: str,
    ) -> list[ChallengeSpec]:
        values = (self._bounded(value - self._STEP), self._bounded(value + self._STEP))
        return [
            ChallengeSelector.adaptive_spec(
                parent=trigger,
                challenge_type=challenge_type,
                parameters={parameter: candidate},
                reason=reason,
            )
            for candidate in values
            if candidate != value
        ]

    @staticmethod
    def _required_value(challenge: ChallengeSpec, parameter: str) -> float:
        value = challenge.parameters.get(parameter)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{challenge.type} challenge requires numeric '{parameter}'")
        if not 0.0 <= float(value) <= 1.0:
            raise ValueError(f"{challenge.type} parameter '{parameter}' must be in [0, 1]")
        return float(value)

    @staticmethod
    def _bounded(value: float) -> float:
        return round(min(1.0, max(0.0, value)), 6)
