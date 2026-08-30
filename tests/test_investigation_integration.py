"""Bounded, offline integration coverage for Stage 5A discovery."""

from __future__ import annotations

from collections.abc import Sequence
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
import pytest
import torch
from torch import Tensor, nn

from core.schemas import ChallengeSpec, EvaluationResult, ModelMetadata
from dataset_adapters import ImageFolderAdapter
from integration.failure_memory_adapter import FailureMemoryAdapter
from integration.investigation_service import InvestigationService
from integration.service import AnalysisRequest, DatasetConfig, ModelConfig, ModelShieldService
from investigation import AIInvestigationAgent, InvestigationAction, InvestigationEvidence
from model_adapters import AdapterMetadata, ModelAdapter, PreprocessingSpec


def spec(name: str, kind: str, parameters: dict[str, float] | None = None) -> ChallengeSpec:
    return ChallengeSpec(name, kind, parameters or {}, seed=42)


def action(name: str, kind: str, parameters: dict[str, float] | None = None) -> InvestigationAction:
    return InvestigationAction(spec(name, kind, parameters), f"test {kind}")


def request() -> AnalysisRequest:
    return AnalysisRequest(
        baseline=ModelConfig("baseline", "v1", "tiny"),
        candidate=ModelConfig("candidate", "v2", "tiny"),
        dataset=DatasetConfig("tiny", "/unused"),
        verification_runs=1,
    )


def evaluation(request: AnalysisRequest, evaluation_id: str) -> EvaluationResult:
    baseline = ModelMetadata("base:v1", "baseline", "v1", "baseline")
    candidate = ModelMetadata("candidate:v2", "candidate", "v2", "candidate")
    failing = request.challenge_type == "low_light"
    return EvaluationResult(
        evaluation_id=evaluation_id, experiment_id=request.experiment_id or "exp-test", model=candidate,
        baseline=baseline, candidate=candidate,
        challenge=ChallengeSpec("executed", request.challenge_type, request.challenge_parameters or {}, seed=request.seed),
        baseline_score=0.9, candidate_score=0.6 if failing else 0.9,
        threshold=-0.15, status="failure" if failing else "pass", seed=request.seed,
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


class ScriptedAgent:
    def __init__(self, actions: Sequence[InvestigationAction | None]) -> None:
        self.actions = list(actions)
        self.observations: list[tuple[InvestigationEvidence, ...]] = []

    def choose_next(self, evidence_history, available_challenges, remaining_budget):
        del available_challenges, remaining_budget
        self.observations.append(tuple(evidence_history))
        return self.actions.pop(0) if self.actions else None


class ProviderClient:
    def __init__(self, responses) -> None:
        self.responses = list(responses)
        self.prompts: list[str] = []

    def propose(self, prompt: str) -> dict[str, object]:
        self.prompts.append(prompt)
        return self.responses.pop(0)


class RecordingService(ModelShieldService):
    def __init__(self) -> None:
        super().__init__(evaluator=evaluation)
        self.replay_flags: list[bool] = []

    def run_analysis(self, request, *, replay_regressions=True):
        self.replay_flags.append(replay_regressions)
        return super().run_analysis(request, replay_regressions=replay_regressions)


def test_bounded_loop_uses_real_evidence_and_replay_isolation() -> None:
    service = RecordingService()
    agent = ScriptedAgent([action("next", "brightness", {"factor": 0.7}), None])
    result = InvestigationService(service).investigate(
        request(), initial_action=action("initial", "low_light", {"brightness": 0.5}),
        agent=agent, available_challenges=[spec("available", "brightness", {"factor": 0.7})], experiment_budget=2,
    )
    assert result.experiments_executed == 2
    assert result.termination_reason == "experiment_budget_exhausted"
    assert [entry.state for entry in result.trace] == ["executed", "executed"]
    assert service.replay_flags == [False, False]
    assert agent.observations[0][0].delta == result.evaluations[0].delta
    assert agent.observations[0][0].candidate_score == result.evaluations[0].candidate_score


def test_invalid_and_duplicate_actions_do_not_execute_models() -> None:
    service = RecordingService()
    duplicate = action("again", "low_light", {"brightness": 0.5})
    invalid = action("bad", "unknown", {})
    agent = ScriptedAgent([invalid, duplicate, None])
    result = InvestigationService(service, max_decision_attempts=5).investigate(
        request(), initial_action=action("initial", "low_light", {"brightness": 0.5}),
        agent=agent, available_challenges=[], experiment_budget=3,
    )
    assert result.experiments_executed == 1
    assert service.replay_flags == [False]
    assert [entry.state for entry in result.trace] == ["executed", "rejected", "skipped"]
    assert result.trace[1].evaluation is None
    assert "unsupported canonical" in (result.trace[1].reason or "")


def test_invalid_parameters_are_rejected_before_execution() -> None:
    service = RecordingService()
    result = InvestigationService(service).investigate(
        request(), initial_action=action("bad", "low_light", {"brightness": 2.0}),
        agent=ScriptedAgent([None]), available_challenges=[], experiment_budget=1,
    )
    assert result.experiments_executed == 0
    assert service.replay_flags == []
    assert result.trace[0].state == "rejected"
    assert result.trace[0].evaluation is None
    assert result.termination_reason == "agent_terminated"


@pytest.mark.parametrize(
    "proposal",
    [
        {"stop": False, "challenge_type": "fog", "parameters": {}, "rationale": "Try fog."},
        {"stop": False, "challenge_type": "blur", "parameters": {"severity": 5}, "rationale": "Try stronger blur."},
    ],
)
def test_ai_invalid_proposals_are_rejected_by_existing_stage_5a_validation(proposal) -> None:
    service = RecordingService()
    agent = AIInvestigationAgent(ProviderClient([proposal, {"stop": True, "rationale": "Done."}]))
    result = InvestigationService(service).investigate(
        request(), initial_action=action("initial", "low_light", {"brightness": 0.5}),
        agent=agent, available_challenges=[spec("blur", "blur", {"severity": 0.2})], experiment_budget=2,
    )
    assert result.experiments_executed == 1
    assert [entry.state for entry in result.trace] == ["executed", "rejected"]
    assert result.trace[1].evaluation is None
    assert service.replay_flags == [False]


def test_agent_none_terminates_and_budget_caps_unique_actions() -> None:
    service = RecordingService()
    agent = ScriptedAgent([
        action("b", "brightness", {"factor": 0.7}),
        action("r", "rotation", {"degrees": 10.0}),
        action("n", "noise", {"level": 0.1}),
    ])
    result = InvestigationService(service).investigate(
        request(), initial_action=action("i", "blur", {"severity": 0.1}),
        agent=agent, available_challenges=[], experiment_budget=2,
    )
    assert result.experiments_executed == 2
    assert len(service.replay_flags) == 2
    assert result.termination_reason == "experiment_budget_exhausted"


def test_agent_none_stops_after_the_initial_real_experiment() -> None:
    service = RecordingService()
    result = InvestigationService(service).investigate(
        request(), initial_action=action("i", "blur", {"severity": 0.1}),
        agent=ScriptedAgent([None]), available_challenges=[], experiment_budget=5,
    )
    assert result.experiments_executed == 1
    assert result.termination_reason == "agent_terminated"
    assert service.replay_flags == [False]


class MeanModel(nn.Module):
    def __init__(self, forced_class: int | None = None) -> None:
        super().__init__()
        self.forced_class = forced_class

    def forward(self, images: Tensor) -> Tensor:
        classes = torch.full((images.shape[0],), self.forced_class, device=images.device) if self.forced_class is not None else (images.mean((1, 2, 3)) >= 0.5).long()
        logits = torch.zeros((images.shape[0], 2), device=images.device)
        logits[torch.arange(images.shape[0]), classes] = 1
        return logits


class TinyAdapter(ModelAdapter):
    def __init__(self, model: nn.Module) -> None:
        self.model = model
        self._metadata = AdapterMetadata("pytorch", "test", "tiny", 2, None)

    @property
    def metadata(self):
        return self._metadata

    @property
    def preprocessing(self):
        return PreprocessingSpec((10, 10), (0.0, 0.0, 0.0), (1.0, 1.0, 1.0))

    def preprocess(self, images: Tensor) -> Tensor:
        return images.detach().clone()

    def load(self) -> nn.Module:
        return self.model.eval()


def _images(root: Path) -> Path:
    for label, value in (("cat", 25), ("dog", 220)):
        folder = root / label
        folder.mkdir(parents=True)
        Image.new("RGB", (10, 10), color=(value,) * 3).save(folder / "sample.png")
    return root


def test_vertical_real_runner_failure_verifies_and_enters_memory(tmp_path, monkeypatch) -> None:
    root = _images(tmp_path / "images")
    models = iter([TinyAdapter(MeanModel()), TinyAdapter(MeanModel(forced_class=0))] * 2)
    monkeypatch.setattr("integration.service.create_dataset_adapter", lambda **_: ImageFolderAdapter(root=root))
    monkeypatch.setattr("integration.service.create_model_adapter", lambda **_: next(models))
    memory = FailureMemoryAdapter(tmp_path / "memory.db")
    service = ModelShieldService(memory=memory)
    result = InvestigationService(service).investigate(
        AnalysisRequest(
            baseline=ModelConfig("baseline", "v1", "tiny"), candidate=ModelConfig("candidate", "v2", "tiny"),
            dataset=DatasetConfig("tiny", str(root)), failure_threshold=-0.15, verification_runs=1, batch_size=2,
        ),
        initial_action=action("real", "low_light", {"brightness": 0.8}),
        agent=ScriptedAgent([None]), available_challenges=[], experiment_budget=1,
    )
    assert result.evaluations[0].status == "failure"
    assert memory.list_active_regressions()[0]["verified"] is True
    assert result.trace[0].state == "executed"


def test_ai_action_drives_real_runner_and_preserves_failure_memory_path(tmp_path, monkeypatch) -> None:
    root = _images(tmp_path / "images")
    models = iter([TinyAdapter(MeanModel()), TinyAdapter(MeanModel(forced_class=0))] * 4)
    monkeypatch.setattr("integration.service.create_dataset_adapter", lambda **_: ImageFolderAdapter(root=root))
    monkeypatch.setattr("integration.service.create_model_adapter", lambda **_: next(models))
    memory = FailureMemoryAdapter(tmp_path / "memory.db")
    client = ProviderClient([{"stop": False, "challenge_type": "blur", "parameters": {"severity": 0.2}, "rationale": "Test blur after observed degradation."}])
    result = InvestigationService(ModelShieldService(memory=memory)).investigate(
        AnalysisRequest(
            baseline=ModelConfig("baseline", "v1", "tiny"), candidate=ModelConfig("candidate", "v2", "tiny"),
            dataset=DatasetConfig("tiny", str(root)), failure_threshold=-0.15, verification_runs=1, batch_size=2,
        ),
        initial_action=action("real", "low_light", {"brightness": 0.8}),
        agent=AIInvestigationAgent(client),
        available_challenges=[spec("available-blur", "blur", {"severity": 0.2})], experiment_budget=2,
    )
    assert result.experiments_executed == 2
    assert result.trace[1].action.challenge.source == "ai_investigation"
    assert all(entry.evaluation is not None for entry in result.trace)
    assert all(item.status == "failure" for item in result.evaluations)
    assert len(memory.list_active_regressions()) == 2
    assert "baseline_score:" in client.prompts[0]
