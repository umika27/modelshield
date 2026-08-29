import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from failures.fingerprint import EvaluationResult, build_fingerprint, classify_severity
from failures.memory import FailureMemory
from failures.regression import promote_to_regression
from reproducibility.capsule import Capsule, save_capsule, get_capsule


SAMPLE_FAILURE = EvaluationResult(
    model="candidate-v2",
    experiment_id="exp-test",
    condition="low_light_blur",
    parameters={"blur": 0.7, "brightness": 0.3},
    baseline_score=0.82,
    candidate_score=0.49,
    delta=-0.33,
    status="failure",
    seed=42,
)

SAMPLE_PASS = EvaluationResult(
    model="candidate-v2",
    experiment_id="exp-test",
    condition="noise",
    parameters={"level": 0.3},
    baseline_score=0.89,
    candidate_score=0.91,
    delta=0.02,
    status="pass",
    seed=42,
)


@pytest.fixture
def mem():
    m = FailureMemory(db_path=":memory:")
    m.ensure_model("candidate-v2", role="candidate")
    yield m
    m.close()


def test_severity_classification():
    assert classify_severity(-0.33) == "critical"
    assert classify_severity(-0.17) == "major"
    assert classify_severity(-0.05) == "minor"


def test_build_fingerprint_rejects_passing_result():
    with pytest.raises(ValueError):
        build_fingerprint(SAMPLE_PASS)


def test_save_and_get_failure(mem):
    eval_id = mem.save_evaluation(SAMPLE_FAILURE.__dict__)
    fp = build_fingerprint(SAMPLE_FAILURE, evaluation_id=eval_id)
    failure_id = mem.save_failure(fp)

    fetched = mem.get_failure(failure_id)
    assert fetched["condition"] == "low_light_blur"
    assert fetched["severity"] == "critical"
    assert fetched["verified"] is False
    assert fetched["parameters"] == {"blur": 0.7, "brightness": 0.3}


def test_verify_and_filter(mem):
    fp = build_fingerprint(SAMPLE_FAILURE)
    failure_id = mem.save_failure(fp)

    assert mem.list_failures(verified=True) == []
    mem.mark_verified(failure_id)
    verified = mem.list_failures(verified=True)
    assert len(verified) == 1
    assert verified[0]["failure_id"] == failure_id


def test_capsule_roundtrip(mem):
    fp = build_fingerprint(SAMPLE_FAILURE)
    failure_id = mem.save_failure(fp)
    mem.mark_verified(failure_id)

    capsule = Capsule(
        failure_id=failure_id,
        model_reference="candidate-v2@local",
        dataset_reference="cv-demo@v1",
        seed=42,
        challenge_parameters={"blur": 0.7, "brightness": 0.3},
    )
    save_capsule(mem.conn, capsule)

    fetched = get_capsule(mem.conn, failure_id)
    assert fetched["model_reference"] == "candidate-v2@local"
    assert fetched["challenge_parameters"] == {"blur": 0.7, "brightness": 0.3}


def test_regression_requires_verified_failure(mem):
    fp = build_fingerprint(SAMPLE_FAILURE)
    failure_id = mem.save_failure(fp)  # not verified

    with pytest.raises(ValueError):
        promote_to_regression(mem.conn, failure_id, threshold=0.65)

    mem.mark_verified(failure_id)
    reg = promote_to_regression(mem.conn, failure_id, threshold=0.65, policy="block")
    assert reg.regression_id is not None
    assert reg.policy == "block"
