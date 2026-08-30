"""Offline tests for the external-model-backed investigation policy."""

from __future__ import annotations

import json

import pytest

from core.schemas import ChallengeSpec, EvaluationResult, ModelMetadata
from investigation import (
    AIInvestigationAgent,
    InvestigationAction,
    InvestigationEvidence,
    InvestigationProviderError,
    OpenAICompatibleHTTPClient,
)


def _evidence() -> InvestigationEvidence:
    baseline = ModelMetadata("base:v1", "baseline", "v1", "baseline")
    candidate = ModelMetadata("candidate:v2", "candidate", "v2", "candidate")
    result = EvaluationResult(
        evaluation_id="eval-real", experiment_id="exp-real", model=candidate,
        baseline=baseline, candidate=candidate,
        challenge=ChallengeSpec("low-light", "low_light", {"brightness": 0.5}, seed=42),
        baseline_score=0.734, candidate_score=0.678, threshold=-0.05,
        status="failure", seed=42,
    )
    return InvestigationEvidence.from_evaluation(result)


class FakeClient:
    def __init__(self, responses) -> None:
        self.responses = list(responses)
        self.prompts: list[str] = []

    def propose(self, prompt: str) -> dict[str, object]:
        self.prompts.append(prompt)
        response = self.responses.pop(0)
        if isinstance(response, BaseException):
            raise response
        return response


class Fallback:
    def __init__(self) -> None:
        self.calls = 0

    def choose_next(self, evidence_history, available_challenges, remaining_budget):
        del evidence_history, available_challenges, remaining_budget
        self.calls += 1
        return InvestigationAction(ChallengeSpec("fallback", "blur", {"severity": 0.2}, seed=42), "fallback")


def _available() -> list[ChallengeSpec]:
    return [
        ChallengeSpec("blur", "blur", {"severity": 0.2}, seed=42),
        ChallengeSpec("combined", "low_light_blur", {"brightness": 0.4, "blur": 0.3}, seed=42),
    ]


def test_valid_ai_action_becomes_a_canonical_ai_spec() -> None:
    client = FakeClient([{"stop": False, "challenge_type": "low_light_blur", "parameters": {"brightness": 0.4, "blur": 0.3}, "rationale": "Illumination may compound with blur."}])
    action = AIInvestigationAgent(client).choose_next([_evidence()], _available(), 2)
    assert action is not None
    assert action.challenge.type == "low_light_blur"
    assert action.challenge.parameters == {"brightness": 0.4, "blur": 0.3}
    assert action.challenge.source == "ai_investigation"
    assert action.challenge.parent_challenge_id == "low-light"
    assert action.challenge.seed == 42
    assert action.rationale == "Illumination may compound with blur."
    assert not hasattr(action.challenge, "delta")
    assert not hasattr(action.challenge, "status")


def test_stop_response_ends_investigation_without_fallback() -> None:
    fallback = Fallback()
    action = AIInvestigationAgent(FakeClient([{"stop": True, "rationale": "No useful unexplored action remains."}]), fallback=fallback).choose_next([_evidence()], _available(), 2)
    assert action is None
    assert fallback.calls == 0


@pytest.mark.parametrize(
    "response",
    [
        {"stop": False, "challenge_type": "blur", "parameters": {"severity": 0.2}},
        {"stop": False, "challenge_type": "blur", "parameters": [], "rationale": "bad"},
        {"stop": False, "parameters": {"severity": 0.2}, "rationale": "bad"},
        {"stop": "false", "challenge_type": "blur", "parameters": {}, "rationale": "bad"},
    ],
)
def test_malformed_provider_response_uses_fallback(response) -> None:
    fallback = Fallback()
    action = AIInvestigationAgent(FakeClient([response]), fallback=fallback).choose_next([_evidence()], _available(), 2)
    assert action is not None
    assert action.challenge.challenge_id == "fallback"
    assert fallback.calls == 1


def test_provider_exception_uses_fallback() -> None:
    fallback = Fallback()
    action = AIInvestigationAgent(FakeClient([TimeoutError("offline")]), fallback=fallback).choose_next([_evidence()], _available(), 2)
    assert action is not None
    assert action.challenge.type == "blur"
    assert fallback.calls == 1


@pytest.mark.parametrize(
    "challenge_type, parameters",
    [("fog", {}), ("blur", {"severity": 5})],
)
def test_structurally_valid_but_canonically_invalid_actions_are_not_repaired(challenge_type, parameters) -> None:
    action = AIInvestigationAgent(FakeClient([{"stop": False, "challenge_type": challenge_type, "parameters": parameters, "rationale": "Investigate this."}])).choose_next([_evidence()], _available(), 2)
    assert action is not None
    assert action.challenge.type == challenge_type
    assert action.challenge.parameters == parameters


def test_prompt_contains_only_grounded_evidence_and_constraints() -> None:
    client = FakeClient([{"stop": True, "rationale": "Done."}])
    AIInvestigationAgent(client).choose_next([_evidence()], _available(), 2)
    prompt = client.prompts[0]
    assert "baseline_score: 0.734" in prompt
    assert "candidate_score: 0.678" in prompt
    assert "delta: -0.05599999999999994" in prompt
    assert "low_light_blur: brightness: 0.0 to 1.0; blur: 0.0 to 1.0" in prompt
    assert "blur: severity: 0.0 to 1.0" in prompt
    assert "predict scores" in prompt
    assert "release status" in prompt
    assert "0.999" not in prompt


def test_http_client_missing_environment_fails_without_network(monkeypatch) -> None:
    for key in ("MODELSHIELD_LLM_BASE_URL", "MODELSHIELD_LLM_API_KEY", "MODELSHIELD_LLM_MODEL"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(InvestigationProviderError, match="BASE_URL"):
        OpenAICompatibleHTTPClient.from_environment()


def test_http_client_parses_json_only_content_without_network(monkeypatch) -> None:
    class Response:
        def read(self):
            return json.dumps({"choices": [{"message": {"content": '{"stop": true, "rationale": "Done."}'}}]}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    seen = {}

    def fake_urlopen(request, timeout):
        seen["url"], seen["timeout"] = request.full_url, timeout
        seen["body"] = json.loads(request.data.decode())
        return Response()

    monkeypatch.setattr("investigation.provider.urlopen", fake_urlopen)
    client = OpenAICompatibleHTTPClient(base_url="https://example.invalid/v1", api_key="test-key", model="test-model", timeout=3)
    assert client.propose("grounded prompt") == {"stop": True, "rationale": "Done."}
    assert seen["url"] == "https://example.invalid/v1/chat/completions"
    assert seen["timeout"] == 3
    assert seen["body"]["temperature"] == 0
    assert seen["body"]["response_format"] == {"type": "json_object"}
