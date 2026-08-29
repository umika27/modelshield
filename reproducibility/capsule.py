"""
Reproducibility Capsule — the locked context needed to replay an evaluation
exactly (Section 13 of the playbook).

A capsule is created once a failure is verified, and is what makes a saved
failure trustworthy: anyone should be able to reconstruct the exact run.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class Capsule:
    failure_id: int
    model_reference: str
    dataset_reference: str
    preprocessing: dict[str, Any] = field(default_factory=dict)
    seed: Optional[int] = None
    evaluation_config: dict[str, Any] = field(default_factory=dict)
    challenge_parameters: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    metrics: dict[str, Any] = field(default_factory=dict)
    run_id: str = ""
    capsule_id: Optional[int] = None

    def __post_init__(self):
        if not self.run_id:
            self.run_id = f"run-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def save_capsule(conn: sqlite3.Connection, capsule: Capsule) -> int:
    cur = conn.execute(
        """
        INSERT INTO capsules
            (failure_id, model_reference, dataset_reference, preprocessing,
             seed, evaluation_config, challenge_parameters, environment,
             metrics, run_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            capsule.failure_id,
            capsule.model_reference,
            capsule.dataset_reference,
            json.dumps(capsule.preprocessing),
            capsule.seed,
            json.dumps(capsule.evaluation_config),
            json.dumps(capsule.challenge_parameters),
            json.dumps(capsule.environment),
            json.dumps(capsule.metrics),
            capsule.run_id,
        ),
    )
    conn.commit()
    capsule.capsule_id = cur.lastrowid
    return cur.lastrowid


def get_capsule(conn: sqlite3.Connection, failure_id: int) -> Optional[dict[str, Any]]:
    row = conn.execute(
        "SELECT * FROM capsules WHERE failure_id = ? ORDER BY created_at DESC LIMIT 1",
        (failure_id,),
    ).fetchone()
    if row is None:
        return None
    d = dict(row)
    for key in ("preprocessing", "evaluation_config", "challenge_parameters",
                "environment", "metrics"):
        if d.get(key):
            d[key] = json.loads(d[key])
    return d
