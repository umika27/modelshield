"""SQLite persistence adapter for canonical verified ModelShield failures.

The table layout and query behavior are derived from Shyalona's Failure
Memory implementation.  This adapter intentionally accepts only the
canonical :class:`VerifiedFailureArtifact`, so Core ML contracts remain
unchanged and duplicate legacy evaluation types are not introduced.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .contracts import VerifiedFailureArtifact


_SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS models (
    model_id TEXT PRIMARY KEY,
    role TEXT NOT NULL CHECK (role IN ('baseline', 'candidate')),
    reference TEXT,
    created_at TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS evaluations (
    evaluation_id INTEGER PRIMARY KEY AUTOINCREMENT,
    canonical_evaluation_id TEXT NOT NULL,
    experiment_id TEXT NOT NULL,
    model_id TEXT NOT NULL REFERENCES models(model_id),
    condition TEXT NOT NULL,
    parameters TEXT NOT NULL,
    baseline_score REAL NOT NULL,
    candidate_score REAL NOT NULL,
    delta REAL NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pass', 'failure')),
    seed INTEGER,
    created_at TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS failures (
    failure_id INTEGER PRIMARY KEY AUTOINCREMENT,
    evaluation_id INTEGER REFERENCES evaluations(evaluation_id),
    fingerprint TEXT NOT NULL UNIQUE,
    condition TEXT NOT NULL,
    parameters TEXT NOT NULL,
    baseline_score REAL NOT NULL,
    candidate_score REAL NOT NULL,
    delta REAL NOT NULL,
    severity TEXT NOT NULL CHECK (severity IN ('minor', 'major', 'critical')),
    verified INTEGER NOT NULL DEFAULT 0 CHECK (verified IN (0, 1)),
    model_id TEXT REFERENCES models(model_id),
    dataset_ref TEXT,
    created_at TEXT DEFAULT (datetime('now','localtime'))
);

CREATE TABLE IF NOT EXISTS capsules (
    capsule_id INTEGER PRIMARY KEY AUTOINCREMENT,
    failure_id INTEGER NOT NULL REFERENCES failures(failure_id),
    model_reference TEXT,
    dataset_reference TEXT,
    preprocessing TEXT,
    seed INTEGER,
    evaluation_config TEXT,
    challenge_parameters TEXT,
    environment TEXT,
    metrics TEXT,
    run_id TEXT,
    created_at TEXT DEFAULT (datetime('now','localtime'))
);

CREATE INDEX IF NOT EXISTS idx_evaluations_experiment ON evaluations(experiment_id);
CREATE INDEX IF NOT EXISTS idx_failures_verified ON failures(verified);
CREATE INDEX IF NOT EXISTS idx_failures_condition ON failures(condition);
"""


def classify_failure_memory_severity(delta: float) -> str:
    """Use Shyalona's existing internal minor/major/critical bands."""
    magnitude = abs(delta)
    if magnitude >= 0.30:
        return "critical"
    if magnitude >= 0.15:
        return "major"
    return "minor"


class FailureMemoryAdapter:
    """Persist canonical verified failures using the Failure Memory SQLite model."""

    def __init__(self, db_path: str | Path = "modelshield.db") -> None:
        self.db_path = str(db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(_SCHEMA)
        self.conn.commit()

    def store(
        self,
        artifact: VerifiedFailureArtifact,
        *,
        dataset_reference: str | None = None,
        preprocessing: dict[str, Any] | None = None,
        environment: dict[str, Any] | None = None,
    ) -> int:
        """Store one verified failure and its reproducibility capsule.

        The operation rejects passes and unverified evidence at the artifact
        boundary. Re-storing the same canonical fingerprint is rejected by the
        database rather than creating duplicate failure records.
        """
        if not isinstance(artifact, VerifiedFailureArtifact):
            raise TypeError("artifact must be a VerifiedFailureArtifact")

        evaluation = artifact.evaluation
        candidate = evaluation.candidate
        # Keep the original Failure Memory's write sequence atomic. A rejected
        # duplicate fingerprint must not leave an orphan evaluation behind.
        with self.conn:
            self.ensure_model(
                candidate.model_id,
                role="candidate",
                reference=candidate.artifact_reference,
            )
            evaluation_id = self._save_evaluation(artifact)
            failure_id = self._save_failure(artifact, evaluation_id, dataset_reference)
            self._save_capsule(
                failure_id,
                artifact,
                dataset_reference=dataset_reference,
                preprocessing=preprocessing or {},
                environment=environment or {},
            )
        return failure_id

    def ensure_model(self, model_id: str, *, role: str, reference: str = "") -> None:
        """Preserve Failure Memory's idempotent model registration behavior."""
        self.conn.execute(
            "INSERT OR IGNORE INTO models (model_id, role, reference) VALUES (?, ?, ?)",
            (model_id, role, reference),
        )

    def get_failure(self, failure_id: int) -> dict[str, Any] | None:
        """Return a persisted failure record with decoded JSON parameters."""
        row = self.conn.execute(
            "SELECT * FROM failures WHERE failure_id = ?", (failure_id,)
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def get_capsule(self, failure_id: int) -> dict[str, Any] | None:
        """Return the latest reproducibility capsule for a stored failure."""
        row = self.conn.execute(
            "SELECT * FROM capsules WHERE failure_id = ? ORDER BY created_at DESC LIMIT 1",
            (failure_id,),
        ).fetchone()
        if row is None:
            return None
        data = dict(row)
        for key in (
            "preprocessing",
            "evaluation_config",
            "challenge_parameters",
            "environment",
            "metrics",
        ):
            if data.get(key):
                data[key] = json.loads(data[key])
        return data

    def list_failures(self, *, verified: bool | None = None) -> list[dict[str, Any]]:
        """Query stored failures, retaining Shyalona's verified filter behavior."""
        query = "SELECT * FROM failures"
        params: tuple[object, ...] = ()
        if verified is not None:
            query += " WHERE verified = ?"
            params = (int(verified),)
        query += " ORDER BY created_at DESC, failure_id DESC"
        return [self._row_to_dict(row) for row in self.conn.execute(query, params).fetchall()]

    def list_active_regressions(self) -> list[dict[str, Any]]:
        """Return verified historical failures eligible for deterministic replay."""
        return self.list_failures(verified=True)

    def close(self) -> None:
        """Close the owned SQLite connection."""
        self.conn.close()

    def _save_evaluation(self, artifact: VerifiedFailureArtifact) -> int:
        result = artifact.evaluation
        cursor = self.conn.execute(
            """
            INSERT INTO evaluations (
                canonical_evaluation_id, experiment_id, model_id, condition,
                parameters, baseline_score, candidate_score, delta, status, seed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result.evaluation_id,
                result.experiment_id,
                result.candidate.model_id,
                result.challenge.type,
                json.dumps(result.challenge.parameters, sort_keys=True),
                result.baseline_score,
                result.candidate_score,
                result.delta,
                result.status,
                result.seed,
            ),
        )
        return int(cursor.lastrowid)

    def _save_failure(
        self,
        artifact: VerifiedFailureArtifact,
        evaluation_id: int,
        dataset_reference: str | None,
    ) -> int:
        result = artifact.evaluation
        cursor = self.conn.execute(
            """
            INSERT INTO failures (
                evaluation_id, fingerprint, condition, parameters, baseline_score,
                candidate_score, delta, severity, verified, model_id, dataset_ref
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                evaluation_id,
                artifact.failure_fingerprint,
                result.challenge.type,
                json.dumps(result.challenge.parameters, sort_keys=True),
                result.baseline_score,
                result.candidate_score,
                result.delta,
                classify_failure_memory_severity(result.delta),
                1,
                result.candidate.model_id,
                dataset_reference,
            ),
        )
        return int(cursor.lastrowid)

    def _save_capsule(
        self,
        failure_id: int,
        artifact: VerifiedFailureArtifact,
        *,
        dataset_reference: str | None,
        preprocessing: dict[str, Any],
        environment: dict[str, Any],
    ) -> None:
        result = artifact.evaluation
        self.conn.execute(
            """
            INSERT INTO capsules (
                failure_id, model_reference, dataset_reference, preprocessing, seed,
                evaluation_config, challenge_parameters, environment, metrics, run_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                failure_id,
                f"{result.candidate.name}:{result.candidate.version}",
                dataset_reference,
                json.dumps(preprocessing, sort_keys=True),
                result.seed,
                json.dumps(
                    {
                        "experiment_id": result.experiment_id,
                        "metric": result.metric_name,
                        "threshold": result.threshold,
                        "threshold_comparison": result.threshold_comparison,
                    },
                    sort_keys=True,
                ),
                json.dumps(
                    {"type": result.challenge.type, "parameters": result.challenge.parameters},
                    sort_keys=True,
                ),
                json.dumps(environment, sort_keys=True),
                json.dumps(
                    {
                        "baseline_score": result.baseline_score,
                        "candidate_score": result.candidate_score,
                        "delta": result.delta,
                        "failure_fingerprint": artifact.failure_fingerprint,
                    },
                    sort_keys=True,
                ),
                f"verification-{result.evaluation_id}",
            ),
        )

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        data = dict(row)
        if data.get("parameters"):
            data["parameters"] = json.loads(data["parameters"])
        data["verified"] = bool(data["verified"])
        return data
