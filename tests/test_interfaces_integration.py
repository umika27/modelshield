"""Service, FastAPI, and CLI tests sharing one controlled evaluator."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from typer.testing import CliRunner

from api.server import AnalyzeRequest, create_app
from cli.main import app
from core.schemas import ChallengeSpec, EvaluationResult, ModelMetadata
from integration.service import AnalysisRequest, DatasetConfig, ModelConfig, ModelShieldService


def _request(candidate_name: str = "candidate") -> AnalysisRequest:
    return AnalysisRequest(
        baseline=ModelConfig("baseline", "v1", "resnet18"),
        candidate=ModelConfig(candidate_name, "v2", "resnet18"),
        dataset=DatasetConfig("cifar10", "/local/cifar10"),
        challenge_type="low_light_blur",
        challenge_parameters={"brightness": 0.3, "blur": 0.7},
        verification_runs=1,
    )


def _evaluator(request: AnalysisRequest, evaluation_id: str) -> EvaluationResult:
    baseline = ModelMetadata("baseline:v1", "baseline", "v1", "baseline")
    candidate = ModelMetadata(f"{request.candidate.name}:v2", request.candidate.name, "v2", "candidate")
    failing = request.candidate.name != "fixed"
    return EvaluationResult(
        evaluation_id=evaluation_id,
        experiment_id=request.experiment_id or "exp-interface",
        model=candidate, baseline=baseline, candidate=candidate,
        challenge=ChallengeSpec("interface-challenge", request.challenge_type, request.challenge_parameters or {}, seed=request.seed),
        baseline_score=0.82, candidate_score=0.49 if failing else 0.82,
        threshold=-0.15, status="failure" if failing else "pass", seed=request.seed,
        timestamp=datetime(2026, 8, 30, tzinfo=timezone.utc),
    )


def test_service_produces_serializable_real_pipeline_projection():
    result = ModelShieldService(evaluator=_evaluator).run_analysis(_request())
    payload = result.to_dict()
    assert payload["metric"]["delta"] == pytest.approx(-0.33)
    assert payload["verification"]["verified"] is True
    assert payload["failure"]["fingerprint"].startswith("sha256:")
    assert payload["release"]["verdict"] == "BLOCK"


def test_service_passing_analysis_is_pass():
    result = ModelShieldService(evaluator=_evaluator).run_analysis(_request("fixed"))
    assert result.release.verdict.value == "PASS"
    assert result.failure_fingerprint is None


def test_api_uses_the_injected_shared_service_and_exposes_dashboard_fields():
    service = ModelShieldService(evaluator=_evaluator)
    api = create_app(service)
    endpoints = {route.path: route.endpoint for route in api.routes if hasattr(route, "endpoint")}
    payload = endpoints["/api/analyze"](AnalyzeRequest.model_validate({
        "baseline": {"name": "baseline", "version": "v1", "architecture": "resnet18"},
        "candidate": {"name": "candidate", "version": "v2", "architecture": "resnet18"},
        "dataset": {"dataset_type": "cifar10", "root": "/local/cifar10"},
        "challenge_type": "low_light_blur", "challenge_parameters": {"brightness": 0.3, "blur": 0.7}, "verification_runs": 1,
    }))
    assert payload["release"]["verdict"] == "BLOCK"
    assert payload["failure"]["fingerprint"].startswith("sha256:")
    assert payload["verification"]["verified"] is True
    assert endpoints["/api/analysis/latest"]()["analysis_id"] == payload["analysis_id"]


def test_latest_analysis_has_every_field_consumed_by_live_dashboard():
    service = ModelShieldService(evaluator=_evaluator)
    payload = service.run_analysis(_request()).to_dict()
    assert payload["condition"]["type"] == "low_light_blur"
    assert isinstance(payload["condition"]["parameters"], dict)
    assert all(isinstance(payload["metric"][key], float) for key in ("baseline_score", "candidate_score", "delta"))
    assert payload["verification"]["verified"] is True
    assert payload["failure"]["fingerprint"].startswith("sha256:")
    assert payload["failure"]["severity"] in {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    assert payload["release"]["verdict"] in {"PASS", "REVIEW", "BLOCK"}
    assert payload["release"]["candidate"] == {"model_id": "candidate:v2", "name": "candidate", "version": "v2"}


def test_cli_uses_shared_service_without_release_policy_logic(monkeypatch):
    service = ModelShieldService(evaluator=_evaluator)
    monkeypatch.setattr("cli.main.ModelShieldService", lambda: service)
    result = CliRunner().invoke(app, ["analyze", "--baseline-checkpoint", "base.pt", "--candidate-checkpoint", "candidate.pt", "--dataset-root", "/local/cifar10", "--max-samples", "1"])
    assert result.exit_code == 0
    assert '"verdict": "BLOCK"' in result.stdout
