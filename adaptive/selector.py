"""Small helpers for selecting stable, duplicate-free challenge specifications."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Sequence

from core.schemas import ChallengeSpec


def challenge_key(challenge: ChallengeSpec) -> tuple[str, str]:
    """Identify an experiment by its condition, independent of generated IDs."""
    return challenge.type, json.dumps(challenge.parameters, sort_keys=True, separators=(",", ":"))


class ChallengeSelector:
    """Return ordered, duplicate-free challenge specifications without mutation."""

    @staticmethod
    def unique(challenges: Iterable[ChallengeSpec]) -> list[ChallengeSpec]:
        selected: list[ChallengeSpec] = []
        seen: set[tuple[str, str]] = set()
        for challenge in challenges:
            if not isinstance(challenge, ChallengeSpec):
                raise TypeError("available_challenges must contain ChallengeSpec objects")
            key = challenge_key(challenge)
            if key not in seen:
                selected.append(challenge)
                seen.add(key)
        return selected

    @staticmethod
    def adaptive_spec(
        *,
        parent: ChallengeSpec,
        challenge_type: str,
        parameters: dict[str, float],
        reason: str,
    ) -> ChallengeSpec:
        """Build a stable follow-up spec that retains its evidence lineage."""
        normalized_parameters = json.dumps(parameters, sort_keys=True, separators=(",", ":"))
        digest_source = f"{parent.challenge_id}|{challenge_type}|{normalized_parameters}"
        challenge_id = f"adaptive-{parent.challenge_id}-{hashlib.sha256(digest_source.encode()).hexdigest()[:10]}"
        return ChallengeSpec(
            challenge_id=challenge_id,
            type=challenge_type,
            parameters=parameters,
            parent_challenge_id=parent.challenge_id,
            source="adaptive_investigation",
            reason=reason,
            reproducible=parent.reproducible,
            seed=parent.seed,
        )

    @staticmethod
    def defaults(available_challenges: Sequence[ChallengeSpec]) -> list[ChallengeSpec]:
        """Return the initial/default suite in stable caller-provided order."""
        return ChallengeSelector.unique(available_challenges)
