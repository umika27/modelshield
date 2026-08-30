"""
Failure Memory — persistent SQLite store for FailureRecords.

This is the module Kartikay's regression engine reads from, and the module
Umika's evaluator writes into (via EvaluationResult -> build_fingerprint ->
save_failure). Build and test this against the mock JSON in examples/ —
don't wait on the real evaluator.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Optional

from failures.fingerprint import FailureRecord

SCHEMA_PATH = Path(__file__).resolve().parent.parent / "database" / "schema.sql"


class FailureMemory:
    def __init__(self, db_path: str = "modelshield.db"):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with open(SCHEMA_PATH, "r") as f:
            self.conn.executescript(f.read())
        self.conn.commit()

    # -- write ---------------------------------------------------------------

    def ensure_model(self, model_id: str, role: str, reference: str = "") -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO models (model_id, role, reference) VALUES (?, ?, ?)",
            (model_id, role, reference),
        )
        self.conn.commit()

    def save_evaluation(self, result_dict: dict[str, Any], owner_uid: Optional[str] = None) -> int:
        """Persist a raw EvaluationResult row, return its evaluation_id.

        owner_uid: the Firebase Auth UID of the user who ran this evaluation.
        Optional so existing calls (tests, demos without login) still work.
        """
        cur = self.conn.execute(
            """
            INSERT INTO evaluations
                (experiment_id, model_id, condition, parameters,
                 baseline_score, candidate_score, delta, status, seed, owner_uid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                result_dict["experiment_id"],
                result_dict["model"],
                result_dict["condition"],
                json.dumps(result_dict.get("parameters", {})),
                result_dict["baseline_score"],
                result_dict["candidate_score"],
                result_dict["delta"],
                result_dict["status"],
                result_dict.get("seed"),
                owner_uid,
            ),
        )
        self.conn.commit()
        return cur.lastrowid

    def save_failure(self, record: FailureRecord, owner_uid: Optional[str] = None) -> int:
        """Persist a FailureRecord (unverified by default), return failure_id.

        owner_uid: the Firebase Auth UID of the user this failure belongs to.
        """
        cur = self.conn.execute(
            """
            INSERT INTO failures
                (evaluation_id, condition, parameters, baseline_score,
                 candidate_score, delta, severity, verified, model_id,
                 dataset_ref, owner_uid)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.evaluation_id,
                record.condition,
                json.dumps(record.parameters),
                record.baseline_score,
                record.candidate_score,
                record.delta,
                record.severity,
                int(record.verified),
                record.model_id,
                record.dataset_ref,
                owner_uid,
            ),
        )
        self.conn.commit()
        record.failure_id = cur.lastrowid
        return cur.lastrowid

    def mark_verified(self, failure_id: int, verified: bool = True) -> None:
        """Flip a failure's verification state. Only verified failures should
        be promoted into regression tests — see failures/regression.py."""
        self.conn.execute(
            "UPDATE failures SET verified = ? WHERE failure_id = ?",
            (int(verified), failure_id),
        )
        self.conn.commit()

    # -- read ------------------------------------------------------------

    def get_failure(self, failure_id: int) -> Optional[dict[str, Any]]:
        row = self.conn.execute(
            "SELECT * FROM failures WHERE failure_id = ?", (failure_id,)
        ).fetchone()
        return self._row_to_dict(row) if row else None

    def list_failures(
        self,
        *,
        verified: Optional[bool] = None,
        condition: Optional[str] = None,
        severity: Optional[str] = None,
        model_id: Optional[str] = None,
        owner_uid: Optional[str] = None,
    ) -> list[dict[str, Any]]:
        """Filtered list — pass any combination of filters.

        Pass owner_uid to get only one user's failures — this is what your
        server should always pass once a user is logged in, so users never
        see each other's data.
        """
        clauses, params = [], []
        if verified is not None:
            clauses.append("verified = ?")
            params.append(int(verified))
        if condition is not None:
            clauses.append("condition = ?")
            params.append(condition)
        if severity is not None:
            clauses.append("severity = ?")
            params.append(severity)
        if model_id is not None:
            clauses.append("model_id = ?")
            params.append(model_id)
        if owner_uid is not None:
            clauses.append("owner_uid = ?")
            params.append(owner_uid)

        query = "SELECT * FROM failures"
        if clauses:
            query += " WHERE " + " AND ".join(clauses)
        query += " ORDER BY created_at DESC"

        rows = self.conn.execute(query, params).fetchall()
        return [self._row_to_dict(r) for r in rows]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        d = dict(row)
        if "parameters" in d and d["parameters"]:
            d["parameters"] = json.loads(d["parameters"])
        d["verified"] = bool(d["verified"])
        return d

    def close(self) -> None:
        self.conn.close()