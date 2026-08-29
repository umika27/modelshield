
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from failures.fingerprint import EvaluationResult, build_fingerprint
from failures.memory import FailureMemory
from failures.regression import promote_to_regression
from reproducibility.capsule import Capsule, save_capsule, get_capsule


def main():
    mock_path = Path(__file__).parent / "examples" / "mock_evaluation_result.json"
    results = [EvaluationResult.from_dict(d) for d in json.loads(mock_path.read_text())]
    mem = FailureMemory(db_path="modelshield.db")
    mem.ensure_model("candidate-v2", role="candidate")

    for result in results:
        eval_id = mem.save_evaluation(result.__dict__)  

        if result.status != "failure":
            print(f"[pass]    {result.condition:20s} delta={result.delta:+.2f}")
            continue

        fingerprint = build_fingerprint(result, evaluation_id=eval_id)
        failure_id = mem.save_failure(fingerprint)
        print(f"[failure] {result.condition:20s} delta={result.delta:+.2f} "
              f"severity={fingerprint.severity} -> failure_id={failure_id}")

        # Simulate verification (in the real system: repeat evaluation under
        # locked config, per Section 9's adaptive algorithm)
        mem.mark_verified(failure_id, verified=True)

        capsule = Capsule(
            failure_id=failure_id,
            model_reference="candidate-v2@local",
            dataset_reference="cv-demo-dataset@v1",
            seed=result.seed,
            challenge_parameters=result.parameters,
            metrics={"candidate_score": result.candidate_score,
                     "baseline_score": result.baseline_score},
        )
        save_capsule(mem.conn, capsule)

        reg = promote_to_regression(
            mem.conn, failure_id, threshold=result.baseline_score * 0.9, policy="block"
        )
        print(f"          -> regression_id={reg.regression_id} "
              f"threshold={reg.threshold:.2f} policy={reg.policy}")

    print("\nVerified failures in memory:")
    for f in mem.list_failures(verified=True):
        print(f"  #{f['failure_id']} {f['condition']} severity={f['severity']}")
        capsule = get_capsule(mem.conn, f["failure_id"])
        print(f"    capsule run_id={capsule['run_id']}")

    mem.close()


if __name__ == "__main__":
    main()
