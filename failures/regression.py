"""
Turns a *verified* FailureRecord into a RegressionRecord — the handoff
contract to Kartikay's regression runner/CLI (Section 12/14 of the playbook).

Only verified failures may be promoted. This module does not run the
regression check itself (that's Kartikay's job) — it just produces the
frozen, storable record his engine will read.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass
class RegressionRecord:
    failure_id: int
    threshold: float
    policy: str  # "pass" | "review" | "block"
    enabled: bool = True
    regression_id: int | None = None


def promote_to_regression(
    conn: sqlite3.Connection,
    failure_id: int,
    threshold: float,
    policy: str = "block",
) -> RegressionRecord:
    """Create a regression test from a verified failure.

    Raises if the failure isn't marked verified — unverified failures must
    never become regression gates (Section 13: "confirmed -> Failure Memory
    -> Regression Test").
    """
    row = conn.execute(
        "SELECT verified FROM failures WHERE failure_id = ?", (failure_id,)
    ).fetchone()
    if row is None:
        raise ValueError(f"No failure with id {failure_id}")
    if not row[0]:
        raise ValueError(
            f"Failure {failure_id} is not verified — cannot create a "
            f"regression test from an unverified failure."
        )

    cur = conn.execute(
        """
        INSERT INTO regression_tests (failure_id, threshold, policy, enabled)
        VALUES (?, ?, ?, ?)
        """,
        (failure_id, threshold, policy, int(True)),
    )
    conn.commit()
    return RegressionRecord(
        failure_id=failure_id,
        threshold=threshold,
        policy=policy,
        enabled=True,
        regression_id=cur.lastrowid,
    )
