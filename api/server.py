"""FastAPI interface backed exclusively by ModelShieldService."""

from __future__ import annotations

from pathlib import Path
import os
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from dataset_adapters.exceptions import DatasetAdapterError
from experiments.exceptions import ExperimentError
from integration.service import AnalysisRequest, DatasetConfig, ModelConfig, ModelShieldService
from integration.investigation_service import InvestigationService
from investigation import (
    AIInvestigationAgent,
    DeterministicInvestigationAgent,
    InvestigationAction,
    InvestigationProviderError,
    OpenAICompatibleHTTPClient,
)
from core.schemas import ChallengeSpec
from model_adapters.exceptions import ModelAdapterError


class ModelRequest(BaseModel):
    name: str
    version: str
    architecture: str
    checkpoint_path: str | None = None


class DatasetRequest(BaseModel):
    dataset_type: str
    root: str
    split: str = "test"


class AnalyzeRequest(BaseModel):
    baseline: ModelRequest
    candidate: ModelRequest
    dataset: DatasetRequest
    challenge_type: str = "clean"
    challenge_parameters: dict[str, object] = Field(default_factory=dict)
    seed: int = 42
    batch_size: int = 32
    max_samples: int | None = None
    failure_threshold: float = -0.15
    verification_runs: int = 3
    experiment_id: str | None = None

    def to_service_request(self) -> AnalysisRequest:
        return AnalysisRequest(
            baseline=ModelConfig(**self.baseline.model_dump()),
            candidate=ModelConfig(**self.candidate.model_dump()),
            dataset=DatasetConfig(**self.dataset.model_dump()),
            challenge_type=self.challenge_type,
            challenge_parameters=self.challenge_parameters,
            seed=self.seed,
            batch_size=self.batch_size,
            max_samples=self.max_samples,
            failure_threshold=self.failure_threshold,
            verification_runs=self.verification_runs,
            experiment_id=self.experiment_id,
        )


class _TrackingFallback:
    """Observe optional fallback use without changing selection behavior."""

    def __init__(self) -> None:
        self._delegate = DeterministicInvestigationAgent()
        self.used = False

    def choose_next(self, evidence_history, available_challenges, remaining_budget):
        self.used = True
        return self._delegate.choose_next(evidence_history, available_challenges, remaining_budget)


class _UnavailableProvider:
    """Keep the existing agent's deterministic fallback available without a provider."""

    def __init__(self, reason: str) -> None:
        self.reason = reason

    def propose(self, prompt: str) -> dict[str, object]:
        del prompt
        raise InvestigationProviderError(self.reason)


def _review_request() -> AnalysisRequest:
    """Return the fixed, real-data reviewer configuration; no scores are supplied."""
    root = Path(__file__).resolve().parent.parent
    return AnalysisRequest(
        baseline=ModelConfig(
            "cifar10-resnet18-baseline", "reference-v1", "resnet18",
            str(root / "artifacts/models/cifar10_resnet18_baseline.pth"),
        ),
        candidate=ModelConfig(
            "cifar10-resnet18-candidate", "candidate-v1", "resnet18",
            str(root / "artifacts/models/cifar10_resnet18_candidate.pth"),
        ),
        dataset=DatasetConfig("cifar10", str(root / "data"), "test"),
        seed=42,
        batch_size=32,
        max_samples=50,
        verification_runs=1,
    )


def _review_available_challenges() -> list[ChallengeSpec]:
    """Provide only canonical challenges and semantically valid example parameters."""
    parameters = {
        "clean": {}, "blur": {"severity": 0.5}, "noise": {"level": 0.5},
        "brightness": {"factor": 0.7}, "rotation": {"degrees": 15.0},
        "low_light": {"brightness": 0.5},
        "low_light_blur": {"brightness": 0.5, "blur": 0.4},
    }
    return [
        ChallengeSpec(f"review-{kind}", kind, values, source="initial_suite", reason="review investigation", seed=42)
        for kind, values in parameters.items()
    ]


def _new_verified_failures(service: ModelShieldService, before: set[int]) -> list[dict[str, object]]:
    """Project only failures that this investigation actually verified and stored."""
    records = service.memory.list_active_regressions()
    return [
        {
            "failure_id": record["failure_id"], "fingerprint": record["fingerprint"],
            "challenge": record["condition"], "parameters": record["parameters"],
            "delta": record["delta"], "severity": record["severity"], "stored": True,
        }
        for record in records
        if record["failure_id"] not in before
    ]


def _serialize_investigation(result, *, fallback_used: bool, provider_model: str | None, verified_failures: list[dict[str, object]]) -> dict[str, object]:
    """Return a UI projection derived exclusively from canonical investigation evidence."""
    experiments: list[dict[str, Any]] = []
    for index, entry in enumerate(result.trace, start=1):
        challenge = entry.action.challenge
        item: dict[str, Any] = {
            "number": index, "state": entry.state, "source": challenge.source,
            "challenge": challenge.type, "parameters": dict(challenge.parameters),
            "rationale": entry.action.rationale,
        }
        if entry.evaluation is not None:
            evaluation = entry.evaluation
            item.update({
                "baseline_score": evaluation.baseline_score,
                "candidate_score": evaluation.candidate_score,
                "delta": evaluation.delta, "status": evaluation.status,
                "verification": {"required": evaluation.status == "failure"},
            })
        else:
            item["reason"] = entry.reason
        experiments.append(item)
    ai_used = any(item["source"] == "ai_investigation" for item in experiments)
    return {
        "investigation_id": result.investigation_id,
        "baseline": result.baseline.__dict__ if result.baseline else None,
        "candidate": result.candidate.__dict__ if result.candidate else None,
        "dataset": {"type": "cifar10", "root": "data", "split": "test"},
        "experiments_executed": result.experiments_executed,
        "budget": result.experiment_budget,
        "termination_reason": result.termination_reason,
        "ai": {"provider_model": provider_model, "actually_used": ai_used and not fallback_used, "fallback_used": fallback_used},
        "experiments": experiments,
        "verified_failures": verified_failures,
        # InvestigationResult deliberately has no aggregate release contract.
        "release": {"available": False, "message": "Investigation completed; experiment statuses are shown individually."},
    }


def create_app(service: ModelShieldService | None = None) -> FastAPI:
    """Create an API whose analysis data is always produced by one service."""
    app = FastAPI(title="ModelShield", version="1.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    app.state.service = service or ModelShieldService()

    @app.post("/api/analyze")
    def analyze(request: AnalyzeRequest):
        try:
            return app.state.service.run_analysis(request.to_service_request()).to_dict()
        except (DatasetAdapterError, ModelAdapterError, ExperimentError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.get("/api/analysis/latest")
    def latest_analysis():
        result = app.state.service.latest_result
        if result is None:
            raise HTTPException(status_code=404, detail="No real analysis has been run yet.")
        return result.to_dict()

    @app.post("/api/investigate")
    def investigate_release():
        """Run the bounded, real CIFAR-10 autonomous review investigation."""
        fallback = _TrackingFallback()
        provider_model = os.environ.get("MODELSHIELD_LLM_MODEL") or None
        try:
            client = OpenAICompatibleHTTPClient.from_environment()
        except InvestigationProviderError as exc:
            client = _UnavailableProvider("AI provider unavailable")
        agent = AIInvestigationAgent(client, fallback=fallback)
        before = {record["failure_id"] for record in app.state.service.memory.list_active_regressions()}
        try:
            result = InvestigationService(app.state.service).investigate(
                _review_request(),
                initial_action=InvestigationAction(_review_available_challenges()[0], "Start with the clean baseline comparison."),
                agent=agent,
                available_challenges=_review_available_challenges(),
                experiment_budget=2,
            )
            return _serialize_investigation(
                result,
                fallback_used=fallback.used,
                provider_model=provider_model,
                verified_failures=_new_verified_failures(app.state.service, before),
            )
        except (DatasetAdapterError, ModelAdapterError, ExperimentError, ValueError) as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    repository_root = Path(__file__).resolve().parent.parent
    agent_assets_dir = repository_root / "agents_gif"
    if agent_assets_dir.is_dir():
        # This must precede the dashboard's root catch-all mount.
        app.mount("/agents_gif", StaticFiles(directory=str(agent_assets_dir)), name="agents_gif")

    static_dir = repository_root / "dashboard"
    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="dashboard")
    return app


app = create_app()
