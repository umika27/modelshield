"""FastAPI interface backed exclusively by ModelShieldService."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from integration.service import AnalysisRequest, DatasetConfig, ModelConfig, ModelShieldService


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


def create_app(service: ModelShieldService | None = None) -> FastAPI:
    """Create an API whose analysis data is always produced by one service."""
    app = FastAPI(title="ModelShield", version="1.0.0")
    app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
    app.state.service = service or ModelShieldService()

    @app.post("/api/analyze")
    def analyze(request: AnalyzeRequest):
        return app.state.service.run_analysis(request.to_service_request()).to_dict()

    @app.get("/api/analysis/latest")
    def latest_analysis():
        result = app.state.service.latest_result
        if result is None:
            raise HTTPException(status_code=404, detail="No real analysis has been run yet.")
        return result.to_dict()

    static_dir = Path(__file__).resolve().parent.parent / "dashboard"
    if static_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="dashboard")
    return app


app = create_app()
