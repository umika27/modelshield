import json
from pathlib import Path
import pytest

from core.schemas.failure import FailureRecord, ModelRef
from core.schemas.regression import PolicyEnum, RegressionRecord
from core.schemas.decision import DecisionEnum, CheckStatusEnum, ReleaseDecision
from core.regression import (
    RegressionEngine,
    FailureToRegressionCompiler,
    PolicyEvaluator,
    CallableEvaluator,
    InMemoryFailureStore,
    InMemoryRegressionStore,
    JsonFileFailureStore,
    JsonFileRegressionStore,
)


@pytest.fixture
def sample_failure_dict():
    """Load reference FailureRecord from contract documentation."""
    contract_path = Path(__file__).parent.parent / "docs" / "contracts" / "failure_record.json"
    with open(contract_path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def sample_failure_record(sample_failure_dict):
    return FailureRecord.model_validate(sample_failure_dict)


def test_failure_record_validation(sample_failure_dict, sample_failure_record):
    assert sample_failure_record.failure_id == "failure-147"
    assert sample_failure_record.condition.type == "low_light_blur"
    assert sample_failure_record.metric.baseline_score == 0.82
    assert sample_failure_record.metric.candidate_score == 0.49
    assert sample_failure_record.severity == "critical"
    assert sample_failure_record.verification.status == "verified"


def test_failure_to_regression_compiler(sample_failure_record):
    compiler = FailureToRegressionCompiler()
    reg = compiler.compile(sample_failure_record, custom_threshold=0.65, custom_policy=PolicyEnum.BLOCK)

    assert reg.regression_id == "regression-147"
    assert reg.failure_id == "failure-147"
    assert reg.condition.type == "low_light_blur"
    assert reg.metric.minimum_threshold == 0.65
    assert reg.policy == PolicyEnum.BLOCK
    assert reg.enabled is True


def test_regression_engine_block_decision(sample_failure_record):
    engine = RegressionEngine()
    engine.remember_failure(sample_failure_record, custom_threshold=0.65, custom_policy=PolicyEnum.BLOCK)

    candidate = ModelRef(name="candidate-v3", version="v3")
    # Candidate score 0.49 is below minimum threshold 0.65
    decision = engine.evaluate_model(
        candidate_model=candidate,
        score_overrides={"regression-147": 0.49},
        decision_id="decision-001",
    )

    assert decision.decision == DecisionEnum.BLOCK
    assert decision.summary.total_regressions == 1
    assert decision.summary.failed == 1
    assert decision.summary.passed == 0
    assert len(decision.failures) == 1
    assert decision.failures[0].status == CheckStatusEnum.FAILED

    # Check contract dict format compatibility
    contract_dict = decision.to_contract_dict()
    assert contract_dict["decision"] == "block"
    assert contract_dict["summary"]["failed"] == 1


def test_regression_engine_pass_decision(sample_failure_record):
    engine = RegressionEngine()
    engine.remember_failure(sample_failure_record, custom_threshold=0.65, custom_policy=PolicyEnum.BLOCK)

    candidate = ModelRef(name="candidate-v4", version="v4")
    # Candidate score 0.85 passes the 0.65 threshold
    decision = engine.evaluate_model(
        candidate_model=candidate,
        score_overrides={"regression-147": 0.85},
    )

    assert decision.decision == DecisionEnum.PASS
    assert decision.summary.total_regressions == 1
    assert decision.summary.passed == 1
    assert decision.summary.failed == 0
    assert len(decision.failures) == 0


def test_regression_engine_review_decision(sample_failure_record):
    engine = RegressionEngine()
    # Threshold 0.65 with default review_margin 0.05 -> [0.60, 0.65) triggers REVIEW
    engine.remember_failure(sample_failure_record, custom_threshold=0.65)

    candidate = ModelRef(name="candidate-v5", version="v5")
    decision = engine.evaluate_model(
        candidate_model=candidate,
        score_overrides={"regression-147": 0.62},
    )

    assert decision.decision == DecisionEnum.REVIEW
    assert decision.summary.review_required == 1
    assert decision.summary.passed == 0
    assert decision.summary.failed == 0


def test_pluggable_evaluator_interface(sample_failure_record):
    # Evaluator returns 0.90 for high brightness, 0.40 for low brightness
    def mock_eval_fn(model, cond_type, params, metric_name):
        if params.get("brightness", 1.0) < 0.5:
            return 0.40
        return 0.90

    evaluator = CallableEvaluator(mock_eval_fn)
    engine = RegressionEngine(evaluator=evaluator)
    engine.remember_failure(sample_failure_record, custom_threshold=0.65)

    candidate = ModelRef(name="candidate-v2", version="v2")
    decision = engine.evaluate_model(candidate_model=candidate)

    # Condition has brightness: 0.3 -> evaluator returns 0.40 < 0.65 -> BLOCK
    assert decision.decision == DecisionEnum.BLOCK
    assert decision.detailed_checks[0].observed_score == 0.40


def test_json_file_stores(tmp_path, sample_failure_record):
    fail_dir = tmp_path / "failures"
    reg_dir = tmp_path / "regressions"

    fail_store = JsonFileFailureStore(fail_dir)
    reg_store = JsonFileRegressionStore(reg_dir)

    # Save failure to file store
    fail_store.save_failure(sample_failure_record)
    loaded_fail = fail_store.get_failure("failure-147")
    assert loaded_fail is not None
    assert loaded_fail.failure_id == "failure-147"

    # Regression engine with file stores
    engine = RegressionEngine(failure_store=fail_store, regression_store=reg_store)
    created = engine.remember_stored_failures()
    assert len(created) == 1
    assert created[0].regression_id == "regression-147"

    # Verify persisted in regression file store
    loaded_reg = reg_store.get_regression("regression-147")
    assert loaded_reg is not None
    assert loaded_reg.name == "Low Light Blur regression"


def test_disabled_regression_is_skipped(sample_failure_record):
    engine = RegressionEngine()
    reg = engine.remember_failure(sample_failure_record, custom_threshold=0.65)
    # Disable the regression
    engine.regression_store.set_enabled(reg.regression_id, False)

    candidate = ModelRef(name="candidate-v2", version="v2")
    decision = engine.evaluate_model(
        candidate_model=candidate,
        score_overrides={"regression-147": 0.10},  # Even with bad score, it shouldn't run
    )

    assert decision.decision == DecisionEnum.PASS
    assert decision.summary.total_regressions == 0
