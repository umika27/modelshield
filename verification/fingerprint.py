"""Canonical SHA-256 identities for reproducible model failures."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from core.schemas import EvaluationResult

from .verifier import VerificationResult


class FailureFingerprinter:
    """Generate stable identities from non-volatile failure configuration."""

    def generate(self, evaluation_result: EvaluationResult) -> str:
        """Return a canonical ``sha256:<hex>`` fingerprint for a failure setup."""
        if not isinstance(evaluation_result, EvaluationResult):
            raise TypeError("evaluation_result must be an EvaluationResult")
        canonical = self._canonical_payload(evaluation_result)
        payload = json.dumps(canonical, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return f"sha256:{hashlib.sha256(payload.encode('utf-8')).hexdigest()}"

    def build_verified_artifact(
        self,
        evaluation_result: EvaluationResult,
        verification_result: VerificationResult,
    ) -> dict[str, Any]:
        """Build the serializable handoff artifact for a verified failure."""
        if not isinstance(evaluation_result, EvaluationResult):
            raise TypeError("evaluation_result must be an EvaluationResult")
        if not isinstance(verification_result, VerificationResult):
            raise TypeError("verification_result must be a VerificationResult")
        if not verification_result.verified:
            raise ValueError("a verified failure artifact requires verified reproduction evidence")
        if verification_result.original_evaluation_id != evaluation_result.evaluation_id:
            raise ValueError("verification result does not belong to the evaluation result")
        fingerprint = self.generate(evaluation_result)
        if verification_result.failure_fingerprint not in {None, fingerprint}:
            raise ValueError("verification fingerprint does not match the evaluation result")
        return {
            "failure_fingerprint": fingerprint,
            "evaluation": evaluation_result.to_dict(),
            "verification": verification_result.to_dict(include_results=False),
        }

    @staticmethod
    def _canonical_payload(result: EvaluationResult) -> dict[str, Any]:
        """Exclude run-specific IDs, timestamps, and scores from identity."""
        return {
            "schema_version": "1.0",
            "model": {"name": result.model.name, "version": result.model.version},
            "baseline": {"name": result.baseline.name, "version": result.baseline.version},
            "candidate": {"name": result.candidate.name, "version": result.candidate.version},
            "condition": {
                "type": result.challenge.type,
                "parameters": result.challenge.parameters,
            },
            "metric": {"name": result.metric_name},
            "threshold": {
                "value": result.threshold,
                "comparison": result.threshold_comparison,
            },
            "reproducibility": {"seed": result.seed},
        }
