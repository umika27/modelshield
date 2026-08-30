"""Single application service shared by ModelShield's API and CLI."""

from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Callable
from uuid import uuid4

from core.schemas import ChallengeSpec, EvaluationResult, ModelMetadata
from dataset_adapters import create_dataset_adapter
from experiments import ComparisonExperimentRunner, ExperimentConfig
from integration.contracts import ModelIdentity, PublicSeverity, ReleaseDecision, VerifiedFailureArtifact
from integration.failure_memory_adapter import FailureMemoryAdapter
from integration.release_adapter import ReleaseDecisionAdapter, ReleaseEvidence
from model_adapters import create_model_adapter
from verification import VerificationEngine


@dataclass(frozen=True)
class ModelConfig:
    name: str
    version: str
    architecture: str
    checkpoint_path: str | None = None


@dataclass(frozen=True)
class DatasetConfig:
    dataset_type: str
    root: str
    split: str = "test"


@dataclass(frozen=True)
class AnalysisRequest:
    baseline: ModelConfig
    candidate: ModelConfig
    dataset: DatasetConfig
    challenge_type: str = "clean"
    challenge_parameters: dict[str, object] | None = None
    seed: int = 42
    batch_size: int = 32
    max_samples: int | None = None
    failure_threshold: float = -0.15
    verification_runs: int = 3
    experiment_id: str | None = None


@dataclass(frozen=True)
class AnalysisResult:
    """UI/API-friendly projection of canonical evaluation evidence."""

    analysis_id: str
    evaluation: EvaluationResult
    dataset: DatasetConfig
    verification_required: bool
    verification_verified: bool | None
    verification_runs: int
    successful_reproductions: int
    failure_fingerprint: str | None
    severity: str | None
    release: ReleaseDecision

    def to_dict(self) -> dict[str, object]:
        result = self.evaluation
        return {
            "analysis_id": self.analysis_id,
            "experiment_id": result.experiment_id,
            "baseline": {"id": result.baseline.model_id, "name": result.baseline.name, "version": result.baseline.version, "score": result.baseline_score},
            "candidate": {"id": result.candidate.model_id, "name": result.candidate.name, "version": result.candidate.version, "score": result.candidate_score},
            "dataset": {"type": self.dataset.dataset_type, "root": self.dataset.root, "split": self.dataset.split},
            "condition": {"type": result.challenge.type, "parameters": result.challenge.parameters},
            "metric": {"name": result.metric_name, "baseline_score": result.baseline_score, "candidate_score": result.candidate_score, "delta": result.delta},
            "status": result.status,
            "threshold": result.threshold,
            "verification": {"required": self.verification_required, "verified": self.verification_verified, "runs": self.verification_runs, "successful_reproductions": self.successful_reproductions},
            "failure": {"fingerprint": self.failure_fingerprint, "severity": self.severity},
            "release": self.release.to_dict(),
            "reproducibility": {"seed": result.seed},
        }


Evaluator = Callable[[AnalysisRequest, str], EvaluationResult]


class ModelShieldService:
    """Orchestrate real evaluation, verification, memory, and release policy."""

    def __init__(
        self,
        *,
        memory: FailureMemoryAdapter | None = None,
        evaluator: Evaluator | None = None,
        release_adapter: ReleaseDecisionAdapter | None = None,
    ) -> None:
        self.memory = memory or FailureMemoryAdapter(":memory:")
        self._evaluator = evaluator or self._run_real_evaluation
        self.release_adapter = release_adapter or ReleaseDecisionAdapter()
        self.latest_result: AnalysisResult | None = None

    def run_analysis(self, request: AnalysisRequest) -> AnalysisResult:
        """Run the canonical deterministic pipeline for one requested condition."""
        # Verification requires repeated runs to retain the same experiment
        # identity. Generate it once when the caller did not provide one.
        request = replace(request, experiment_id=request.experiment_id or f"exp-{uuid4().hex}")
        evaluation_id = f"eval-{uuid4().hex}"
        evaluation = self._evaluator(request, evaluation_id)
        if not isinstance(evaluation, EvaluationResult):
            raise TypeError("evaluator must return an EvaluationResult")
        candidate, baseline = _identities(evaluation)
        if evaluation.status != "failure":
            release = self.release_adapter.decide([], candidate=candidate, baseline=baseline)
            result = AnalysisResult(str(uuid4()), evaluation, request.dataset, False, None, 0, 0, None, None, release)
            self.latest_result = result
            return result

        verification = VerificationEngine().verify(
            evaluation,
            lambda: self._evaluator(request, f"eval-{uuid4().hex}"),
            runs=request.verification_runs,
        )
        if not verification.verified:
            evidence = ReleaseEvidence(
                failure_fingerprint="sha256:" + "0" * 64,
                baseline_score=evaluation.baseline_score,
                candidate_score=evaluation.candidate_score,
                severity=PublicSeverity.LOW,
                verified=False,
                candidate=candidate,
                baseline=baseline,
            )
            release = self.release_adapter.decide([evidence])
            result = AnalysisResult(str(uuid4()), evaluation, request.dataset, True, False, verification.runs, verification.successful_reproductions, None, None, release)
            self.latest_result = result
            return result

        artifact = VerifiedFailureArtifact.from_verification(evaluation, verification)
        failure_id = self.memory.store(artifact, dataset_reference=request.dataset.root)
        stored = self.memory.get_failure(failure_id)
        assert stored is not None
        evidence = ReleaseEvidence.from_failure_memory(stored, candidate=candidate, baseline=baseline)
        release = self.release_adapter.decide([evidence])
        result = AnalysisResult(str(uuid4()), evaluation, request.dataset, True, True, verification.runs, verification.successful_reproductions, artifact.failure_fingerprint, evidence.severity.value, release)
        self.latest_result = result
        return result

    def _run_real_evaluation(self, request: AnalysisRequest, evaluation_id: str) -> EvaluationResult:
        """Execute the existing real adapters/experiment runner; no synthetic scores."""
        dataset = create_dataset_adapter(dataset_type=request.dataset.dataset_type, root=Path(request.dataset.root), split=request.dataset.split, download=False)
        dataset.load()
        classes = dataset.metadata.num_classes
        baseline_metadata = _metadata(request.baseline, "baseline")
        candidate_metadata = _metadata(request.candidate, "candidate")
        config = ExperimentConfig(
            experiment_id=request.experiment_id or evaluation_id,
            baseline_model=baseline_metadata,
            candidate_model=candidate_metadata,
            batch_size=request.batch_size,
            failure_threshold=request.failure_threshold,
            seed=request.seed,
            max_samples=request.max_samples,
        )
        runner = ComparisonExperimentRunner(config)
        outcome = runner.run(
            baseline_adapter=create_model_adapter(backend="torchvision", architecture=request.baseline.architecture, num_classes=classes, checkpoint_path=request.baseline.checkpoint_path),
            candidate_adapter=create_model_adapter(backend="torchvision", architecture=request.candidate.architecture, num_classes=classes, checkpoint_path=request.candidate.checkpoint_path),
            dataset_adapter=dataset,
            challenge_spec=ChallengeSpec(f"challenge-{evaluation_id}", request.challenge_type, request.challenge_parameters or {}, seed=request.seed),
        )
        return outcome.evaluation_result


def _metadata(config: ModelConfig, role: str) -> ModelMetadata:
    return ModelMetadata(f"{config.name}:{config.version}", config.name, config.version, role, artifact_reference=config.checkpoint_path or "")


def _identities(result: EvaluationResult) -> tuple[ModelIdentity, ModelIdentity]:
    return (
        ModelIdentity(result.candidate.model_id, result.candidate.name, result.candidate.version),
        ModelIdentity(result.baseline.model_id, result.baseline.name, result.baseline.version),
    )
