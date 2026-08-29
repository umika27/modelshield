"""Unit and end-to-end integration tests for ChallengeEvaluationAdapter."""
from __future__ import annotations

import json
from pathlib import Path
import pytest

from regression.adapter import (
    ChallengeEvaluationAdapter,
    DemoTestEvaluator,
    EvaluationIntegrationError,
)
from regression.runner import RegressionRunner
from regression.schemas import (
    CheckStatusEnum,
    DecisionEnum,
    FailureRecord,
    ModelRef,
    PolicyEnum,
)


@pytest.fixture
def sample_failure_record():
    contract_path = Path(__file__).parent.parent / "docs" / "contracts" / "failure_record.json"
    with open(contract_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return FailureRecord.model_validate(data)


def test_adapter_unregistered_backend_raises_error():
    """Verify that an unregistered adapter raises EvaluationIntegrationError rather than returning fake scores."""
    adapter = ChallengeEvaluationAdapter()
    candidate = ModelRef(name="candidate-v2", version="v2")

    with pytest.raises(EvaluationIntegrationError, match="No model loader registered"):
        adapter.evaluate_condition(
            candidate_model=candidate,
            condition_type="low_light_blur",
            parameters={"brightness": 0.3, "blur": 0.7},
            metric_name="accuracy",
        )


def test_adapter_partial_registration_raises_error():
    adapter = ChallengeEvaluationAdapter(model_loader=lambda m: f"loaded_{m.name}")
    candidate = ModelRef(name="candidate-v2", version="v2")

    with pytest.raises(EvaluationIntegrationError, match="No challenge runner registered"):
        adapter.evaluate_condition(
            candidate_model=candidate,
            condition_type="low_light_blur",
            parameters={},
            metric_name="accuracy",
        )


def test_adapter_full_registration_execution():
    """Test that adapter properly passes condition, parameters, seed, and calculates score."""
    call_log = {}

    def mock_model_loader(model_ref: ModelRef):
        call_log["model"] = f"{model_ref.name}:{model_ref.version}"
        return {"weights": [0.1, 0.2, 0.3]}

    def mock_challenge_runner(model, condition_type, parameters, seed):
        call_log["condition"] = condition_type
        call_log["parameters"] = parameters
        call_log["seed"] = seed
        # Simulate predictions under condition
        return {"predictions": [1, 0, 1], "targets": [1, 1, 1]}

    def mock_metric_evaluator(outputs, metric_name):
        call_log["metric"] = metric_name
        # 2 correct out of 3 -> 0.6667 accuracy
        correct = sum(1 for p, t in zip(outputs["predictions"], outputs["targets"]) if p == t)
        return correct / len(outputs["targets"])

    adapter = ChallengeEvaluationAdapter(
        model_loader=mock_model_loader,
        challenge_runner=mock_challenge_runner,
        metric_evaluator=mock_metric_evaluator,
    )

    candidate = ModelRef(name="candidate-v3", version="v3")
    score = adapter.evaluate_condition(
        candidate_model=candidate,
        condition_type="low_light_blur",
        parameters={"brightness": 0.3, "blur": 0.7},
        metric_name="accuracy",
        seed=1337,
    )

    assert call_log["model"] == "candidate-v3:v3"
    assert call_log["condition"] == "low_light_blur"
    assert call_log["parameters"]["brightness"] == 0.3
    assert call_log["seed"] == 1337
    assert call_log["metric"] == "accuracy"
    assert round(score, 4) == 0.6667


def test_end_to_end_failure_to_release_decision_integration(sample_failure_record):
    """End-to-end integration test proving:
    FailureRecord
    → stored condition (low_light_blur, params: brightness=0.3, blur=0.7)
    → candidate evaluation via ChallengeEvaluationAdapter
    → observed_score (0.49 on vulnerable model, 0.85 on fixed model)
    → RegressionRunner
    → PASS/FAIL
    → ReleaseDecision (BLOCK / PASS)
    """
    # 1. Setup ML backend mock representing real model inference
    def model_loader(model_ref: ModelRef):
        return {"model_name": model_ref.name}

    def challenge_runner(model, condition_type, parameters, seed):
        # Candidate model v2 fails low-light, while candidate model v4 fixes it
        is_fixed_model = "v4" in model["model_name"]
        if condition_type == "low_light_blur" and parameters.get("brightness", 1.0) < 0.5:
            return 0.85 if is_fixed_model else 0.49
        return 0.90

    def metric_evaluator(score_or_outputs, metric_name):
        return float(score_or_outputs)

    adapter = ChallengeEvaluationAdapter(
        model_loader=model_loader,
        challenge_runner=challenge_runner,
        metric_evaluator=metric_evaluator,
    )

    # 2. Setup RegressionRunner with the live adapter
    runner = RegressionRunner(evaluator=adapter)

    # 3. Ingest FailureRecord and compile to RegressionRecord (minimum threshold 0.65, policy BLOCK)
    regression = runner.compile_failure_to_regression(
        sample_failure_record,
        minimum_threshold=0.65,
        policy=PolicyEnum.BLOCK,
    )
    assert regression.condition.type == "low_light_blur"
    assert regression.condition.parameters["brightness"] == 0.3
    assert regression.metric.minimum_threshold == 0.65

    # 4. Test Vulnerable Model (candidate-v2) -> score 0.49 < 0.65 -> FAILED -> BLOCK
    vulnerable_candidate = ModelRef(name="candidate-v2", version="v2")
    block_decision = runner.run_regression_suite(
        candidate_model=vulnerable_candidate,
        regressions=[regression],
    )

    assert block_decision.decision == DecisionEnum.BLOCK
    assert block_decision.summary.failed == 1
    assert block_decision.summary.passed == 0
    assert block_decision.failures[0].status == CheckStatusEnum.FAILED
    assert block_decision.detailed_checks[0].observed_score == 0.49

    # 5. Test Fixed Model (candidate-v4) -> score 0.85 >= 0.65 -> PASSED -> PASS
    fixed_candidate = ModelRef(name="candidate-v4", version="v4")
    pass_decision = runner.run_regression_suite(
        candidate_model=fixed_candidate,
        regressions=[regression],
    )

    assert pass_decision.decision == DecisionEnum.PASS
    assert pass_decision.summary.passed == 1
    assert pass_decision.summary.failed == 0
    assert len(pass_decision.failures) == 0
    assert pass_decision.detailed_checks[0].observed_score == 0.85
