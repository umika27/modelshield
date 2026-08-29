"""
Replay — turns a stored Capsule back into a runnable configuration, and
(optionally) re-executes the evaluation to confirm the failure still
reproduces (Section 13: "anyone should be able to reconstruct the exact
run").

This module does NOT contain any model-running code itself — ModelShield's
actual evaluator belongs to Umika's side of the system. Instead, replay()
takes an `evaluator` function as an argument (dependency injection), so this
module can be built and tested today, and wired up to the real evaluator
the moment it exists — same pattern as the mock EvaluationResult JSON.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from typing import Any, Callable, Optional

from reproducibility.capsule import get_capsule


@dataclass
class ReplayConfig:
    """Everything needed to re-run one evaluation exactly as it happened."""
    failure_id: int
    model_reference: str
    dataset_reference: str
    condition: str
    challenge_parameters: dict[str, Any]
    preprocessing: dict[str, Any]
    evaluation_config: dict[str, Any]
    seed: Optional[int]
    environment: dict[str, Any]
    original_metrics: dict[str, Any]
    run_id: str


class ReplayError(Exception):
    """Raised when a failure has no capsule to replay from."""


def build_replay_config(
    conn: sqlite3.Connection,
    failure_id: int,
) -> ReplayConfig:
    """Reconstruct a runnable config from the most recent capsule for a failure.

    Raises ReplayError if no capsule was ever saved for this failure — you
    can't replay what was never captured.
    """
    capsule = get_capsule(conn, failure_id)
    if capsule is None:
        raise ReplayError(
            f"No capsule found for failure_id={failure_id} — nothing to replay. "
            f"Capsules are created at verification time; check that "
            f"save_capsule() was called for this failure."
        )

    condition_row = conn.execute(
        "SELECT condition FROM failures WHERE failure_id = ?", (failure_id,)
    ).fetchone()
    condition = condition_row[0] if condition_row else capsule.get("challenge_parameters", {}).get("condition", "unknown")

    return ReplayConfig(
        failure_id=failure_id,
        model_reference=capsule["model_reference"],
        dataset_reference=capsule["dataset_reference"],
        condition=condition,
        challenge_parameters=capsule.get("challenge_parameters") or {},
        preprocessing=capsule.get("preprocessing") or {},
        evaluation_config=capsule.get("evaluation_config") or {},
        seed=capsule.get("seed"),
        environment=capsule.get("environment") or {},
        original_metrics=capsule.get("metrics") or {},
        run_id=capsule["run_id"],
    )


# Type alias: an evaluator takes a ReplayConfig and returns a fresh
# {"baseline_score": ..., "candidate_score": ...} dict. The real evaluator
# (Umika's side) will plug in here once it exists.
Evaluator = Callable[[ReplayConfig], dict[str, float]]


@dataclass
class ReplayResult:
    failure_id: int
    reproduced: bool
    original_metrics: dict[str, Any]
    replay_metrics: dict[str, float]
    tolerance: float


def replay_evaluation(
    conn: sqlite3.Connection,
    failure_id: int,
    evaluator: Evaluator,
    tolerance: float = 0.02,
) -> ReplayResult:
    """Rebuild the config for a failure and re-run it through `evaluator`.

    Compares the freshly produced candidate_score against the originally
    recorded one. If they match within `tolerance`, the failure is
    considered genuinely reproduced (not a fluke) — this is the check that
    should gate whether a failure gets marked verified.
    """
    config = build_replay_config(conn, failure_id)
    replay_metrics = evaluator(config)

    original_candidate = config.original_metrics.get("candidate_score")
    replay_candidate = replay_metrics.get("candidate_score")

    reproduced = (
        original_candidate is not None
        and replay_candidate is not None
        and abs(original_candidate - replay_candidate) <= tolerance
    )

    return ReplayResult(
        failure_id=failure_id,
        reproduced=reproduced,
        original_metrics=config.original_metrics,
        replay_metrics=replay_metrics,
        tolerance=tolerance,
    )
