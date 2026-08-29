"""Implementation of `modelshield replay` command."""
from __future__ import annotations

from pathlib import Path
import typer

from cli.formatters import (
    BOLD,
    CYAN,
    DIM,
    GRAY,
    GREEN,
    RED,
    RESET,
    YELLOW,
    format_table,
    print_banner,
)
from regression.runner import RegressionRunner
from regression.schemas import ModelRef

app = typer.Typer(help="Deterministically replay a verified failure test.")


@app.callback(invoke_without_command=True)
def replay_command(
    failure_id: str = typer.Argument("failure-147", help="Failure ID to replay."),
    candidate: str = typer.Option("candidate-v3", "--candidate", "-c", help="Candidate model to test against."),
    version: str = typer.Option("v3", "--version", "-v", help="Candidate model version."),
    failures_file: str = typer.Option("examples/mock_failures.json", "--failures", "-f", help="Path to failures file."),
):
    """Replay a specific failure test condition deterministically."""
    print_banner()
    print(f"Replaying Failure Test: {BOLD}{failure_id}{RESET} on Candidate {BOLD}{candidate}:{version}{RESET}\n")

    runner = RegressionRunner(failures_path=failures_file)
    candidate_model = ModelRef(name=candidate, version=version)

    try:
        result = runner.replay_failure(
            failure_id=failure_id,
            candidate_model=candidate_model,
            failures_path=failures_file,
        )
    except Exception as e:
        print(f"{RED}Error: {e}{RESET}")
        raise typer.Exit(code=1)

    print(f"{BOLD}Challenge Condition:{RESET} {result.details.get('condition_type')}")
    print(f"{BOLD}Parameters:{RESET} {result.details.get('parameters')}")
    print(f"{BOLD}Metric Evaluated:{RESET} {result.metric_name}")
    print(f"{BOLD}Minimum Threshold:{RESET} {result.minimum_threshold:.2f}")
    print(f"{BOLD}Observed Score:{RESET} {result.observed_score:.2f}")
    print(f"{BOLD}Enforced Policy:{RESET} {result.policy.value.upper()}")
    print(f"{GRAY}───────────────────────────────────────────────────────────────────{RESET}")

    if result.status.value == "passed":
        print(f"{GREEN}✓ REPLAY PASSED: Candidate fixed the regression.{RESET}")
    elif result.status.value == "review_required":
        print(f"{YELLOW}▲ REPLAY IN REVIEW: Candidate performance is near boundary.{RESET}")
    else:
        print(f"{RED}✖ REPLAY FAILED: Candidate reproduced the regression failure.{RESET}")
