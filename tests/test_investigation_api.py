"""Review-API coverage using real investigation orchestration and fake inference only."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path

from api.server import create_app
from core.schemas import ChallengeSpec, EvaluationResult, ModelMetadata
from integration.service import AnalysisRequest, ModelShieldService
from investigation import InvestigationProviderError


class _Provider:
    def __init__(self, responses: list[dict[str, object] | Exception]) -> None:
        self.responses = list(responses)

    def propose(self, prompt: str) -> dict[str, object]:
        del prompt
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _evaluation(request: AnalysisRequest, evaluation_id: str) -> EvaluationResult:
    baseline = ModelMetadata("baseline:review", "production", "v1", "baseline")
    candidate = ModelMetadata("candidate:review", "candidate", "v2", "candidate")
    candidate_score = 0.44 if request.challenge_type == "noise" else 0.73
    baseline_score = 0.81
    delta = candidate_score - baseline_score
    return EvaluationResult(
        evaluation_id=evaluation_id,
        experiment_id=request.experiment_id or "review-experiment",
        model=candidate,
        baseline=baseline,
        candidate=candidate,
        challenge=ChallengeSpec("evaluated", request.challenge_type, request.challenge_parameters or {}, seed=request.seed),
        baseline_score=baseline_score,
        candidate_score=candidate_score,
        threshold=-0.15,
        status="failure" if delta <= -0.15 else "pass",
        seed=request.seed,
        timestamp=datetime(2026, 8, 30, tzinfo=timezone.utc),
    )


def _endpoint(service: ModelShieldService):
    api = create_app(service)
    return next(route.endpoint for route in api.routes if getattr(route, "path", None) == "/api/investigate")


def _post_via_asgi(app, path: str) -> tuple[int, dict[str, object]]:
    """Exercise FastAPI's sync endpoint threadpool without an optional HTTP client."""
    async def request() -> tuple[int, dict[str, object]]:
        sent: list[dict[str, object]] = []
        received = False

        async def receive() -> dict[str, object]:
            nonlocal received
            if not received:
                received = True
                return {"type": "http.request", "body": b"", "more_body": False}
            return {"type": "http.disconnect"}

        async def send(message: dict[str, object]) -> None:
            sent.append(message)

        scope = {
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": "POST", "scheme": "http", "path": path, "raw_path": path.encode(),
            "query_string": b"", "headers": [], "client": ("127.0.0.1", 0), "server": ("testserver", 80),
        }
        await app(scope, receive, send)
        status = next(message["status"] for message in sent if message["type"] == "http.response.start")
        body = b"".join(message.get("body", b"") for message in sent if message["type"] == "http.response.body")
        return int(status), json.loads(body)

    return asyncio.run(request())


def test_investigate_endpoint_serializes_real_investigation_evidence(monkeypatch) -> None:
    provider = _Provider([{"stop": False, "challenge_type": "noise", "parameters": {"level": 0.5}, "rationale": "Measure stochastic robustness."}])
    monkeypatch.setattr("api.server.OpenAICompatibleHTTPClient.from_environment", lambda: provider)
    monkeypatch.setenv("MODELSHIELD_LLM_MODEL", "review-model")

    payload = _endpoint(ModelShieldService(evaluator=_evaluation))()

    assert payload["experiments_executed"] == 2
    assert payload["ai"] == {"provider_model": "review-model", "actually_used": True, "fallback_used": False}
    assert [item["source"] for item in payload["experiments"]] == ["initial_suite", "ai_investigation"]
    # These numbers originate in _evaluation, rather than a review-endpoint constant.
    assert payload["experiments"][1]["baseline_score"] == 0.81
    assert payload["experiments"][1]["candidate_score"] == 0.44
    assert payload["experiments"][1]["status"] == "failure"
    assert payload["experiments"][1]["rationale"] == "Measure stochastic robustness."
    assert payload["verified_failures"][0]["stored"] is True
    assert payload["release"]["available"] is False


def test_investigate_endpoint_uses_failure_memory_safely_from_fastapi_worker(monkeypatch) -> None:
    provider = _Provider([{"stop": False, "challenge_type": "noise", "parameters": {"level": 0.5}, "rationale": "Measure stochastic robustness."}])
    monkeypatch.setattr("api.server.OpenAICompatibleHTTPClient.from_environment", lambda: provider)

    status, payload = _post_via_asgi(create_app(ModelShieldService(evaluator=_evaluation)), "/api/investigate")

    assert status == 200
    assert payload["experiments_executed"] == 2
    assert payload["verified_failures"]


def test_investigate_endpoint_truthfully_serializes_rejected_proposal(monkeypatch) -> None:
    provider = _Provider([
        {"stop": False, "challenge_type": "unsupported", "parameters": {}, "rationale": "Try an unsupported transform."},
        {"stop": True, "rationale": "Stop after rejected proposal."},
    ])
    monkeypatch.setattr("api.server.OpenAICompatibleHTTPClient.from_environment", lambda: provider)

    payload = _endpoint(ModelShieldService(evaluator=_evaluation))()

    rejected = payload["experiments"][1]
    assert rejected["state"] == "rejected"
    assert rejected["reason"]
    assert "baseline_score" not in rejected


def test_investigate_endpoint_truthfully_serializes_skipped_duplicate(monkeypatch) -> None:
    provider = _Provider([
        {"stop": False, "challenge_type": "clean", "parameters": {}, "rationale": "Repeat the clean check."},
        {"stop": True, "rationale": "Stop after duplicate proposal."},
    ])
    monkeypatch.setattr("api.server.OpenAICompatibleHTTPClient.from_environment", lambda: provider)

    payload = _endpoint(ModelShieldService(evaluator=_evaluation))()

    skipped = payload["experiments"][1]
    assert skipped["state"] == "skipped"
    assert skipped["reason"] == "Duplicate effective experiment."
    assert "baseline_score" not in skipped


def test_investigate_endpoint_reports_fallback_without_secrets(monkeypatch) -> None:
    monkeypatch.setattr(
        "api.server.OpenAICompatibleHTTPClient.from_environment",
        lambda: _Provider([InvestigationProviderError("request failed using secret-value")]),
    )
    monkeypatch.setenv("MODELSHIELD_LLM_API_KEY", "secret-value")

    payload = _endpoint(ModelShieldService(evaluator=_evaluation))()

    assert payload["ai"]["fallback_used"] is True
    assert payload["ai"]["actually_used"] is False
    assert "secret-value" not in str(payload)


def test_dashboard_investigation_renderer_does_not_calculate_release_status() -> None:
    source = (Path(__file__).resolve().parents[1] / "dashboard" / "app.js").read_text()
    renderer = source[source.index("function renderInvestigation"):]
    assert "investigation.release?.message" in renderer
    assert "release.verdict" not in renderer
    assert "BLOCK" not in renderer


def test_agent_gif_is_served_and_workspace_loader_stops_after_one_failure() -> None:
    app = create_app(ModelShieldService(evaluator=_evaluation))
    asset_mount = next(route for route in app.routes if getattr(route, "path", None) == "/agents_gif")
    assert Path(asset_mount.app.directory, "idle.gif").is_file()
    assert Path(asset_mount.app.directory, "registry.json").is_file()
    loader_source = (Path(__file__).resolve().parents[1] / "dashboard/components/workspace_loader.js").read_text()
    assert 'gifPath: "/agents_gif/idle.gif"' in loader_source
    assert "gifImg.onerror = null;" in loader_source
    assert 'gifImg.removeAttribute("src");' in loader_source


def test_dashboard_starts_neutral_and_uses_only_canonical_asset_routes() -> None:
    root = Path(__file__).resolve().parents[1]
    app_source = (root / "dashboard/app.js").read_text()
    index_source = (root / "dashboard/index.html").read_text()
    agent_source = (root / "dashboard/components/agent_gif.js").read_text()
    live_source = (root / "dashboard/live.js").read_text()
    assert "renderNoAnalysisState();" in app_source
    assert "hydrateDashboardFromApi" not in app_source
    assert "No release investigation has been run yet." in app_source
    assert "renderNeutralWorkspace(container, currentView);" in app_source
    assert 'currentView = "comparison";' in app_source
    assert "candidate-v3" not in index_source
    assert "production-v1" not in index_source
    assert "agents/gif/" not in agent_source
    assert 'fetch("/agents_gif/registry.json")' in agent_source
    assert "if (response.status === 404) return null;" in live_source
