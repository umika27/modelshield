import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from failures.fingerprint import EvaluationResult, build_fingerprint
from failures.memory import FailureMemory
from reproducibility.capsule import Capsule, save_capsule
from reproducibility.replay import (
    build_replay_config,
    replay_evaluation,
    ReplayError,
)


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


@pytest.fixture
def mem_with_capsule():
    m = FailureMemory(db_path=":memory:")
    m.ensure_model("candidate-v2", role="candidate")
    fp = build_fingerprint(SAMPLE_FAILURE)
    failure_id = m.save_failure(fp)
    m.mark_verified(failure_id)

    capsule = Capsule(
        failure_id=failure_id,
        model_reference="candidate-v2@local",
        dataset_reference="cv-demo@v1",
        seed=42,
        challenge_parameters={"blur": 0.7, "brightness": 0.3},
        metrics={"baseline_score": 0.82, "candidate_score": 0.49},
    )
    save_capsule(m.conn, capsule)

    yield m, failure_id
    m.close()


def test_build_replay_config_reconstructs_context(mem_with_capsule):
    mem, failure_id = mem_with_capsule
    config = build_replay_config(mem.conn, failure_id)

    assert config.model_reference == "candidate-v2@local"
    assert config.dataset_reference == "cv-demo@v1"
    assert config.seed == 42
    assert config.condition == "low_light_blur"
    assert config.challenge_parameters == {"blur": 0.7, "brightness": 0.3}
    assert config.original_metrics["candidate_score"] == 0.49


def test_build_replay_config_raises_without_capsule():
    mem = FailureMemory(db_path=":memory:")
    mem.ensure_model("candidate-v2", role="candidate")
    fp = build_fingerprint(SAMPLE_FAILURE)
    failure_id = mem.save_failure(fp)  # no capsule saved

    with pytest.raises(ReplayError):
        build_replay_config(mem.conn, failure_id)
    mem.close()


def test_replay_evaluation_confirms_reproduction(mem_with_capsule):
    mem, failure_id = mem_with_capsule

    def fake_evaluator(config):
        # Simulates re-running the model and getting almost the same score
        return {"baseline_score": 0.82, "candidate_score": 0.485}

    result = replay_evaluation(mem.conn, failure_id, fake_evaluator, tolerance=0.02)
    assert result.reproduced is True


def test_replay_evaluation_flags_non_reproduction(mem_with_capsule):
    mem, failure_id = mem_with_capsule

    def flaky_evaluator(config):
        # Simulates a re-run that came back very different — likely a fluke
        return {"baseline_score": 0.82, "candidate_score": 0.80}

    result = replay_evaluation(mem.conn, failure_id, flaky_evaluator, tolerance=0.02)
    assert result.reproduced is False
