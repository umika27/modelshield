"""Implementation of `modelshield regression` command group."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Optional
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
    badge,
    format_table,
    print_banner,
    print_verdict_card,
)
from regression.adapter import DemoTestEvaluator
from regression.runner import RegressionRunner
from regression.schemas import DecisionEnum, ModelRef

app = typer.Typer(help="Manage and run the ModelShield Regression Engine.")


@app.command("run")
def run_regressions(
    candidate: str = typer.Option("candidate-v3", "--candidate", "-c", help="Candidate model name."),
    version: str = typer.Option("v3", "--version", "-v", help="Candidate model version."),
    regressions_file: str = typer.Option("examples/mock_regressions.json", "--regressions", "-r", help="Path to regression records file."),
    failures_file: str = typer.Option("examples/mock_failures.json", "--failures", "-f", help="Fallback path to failures if no regressions file."),
    output_json: Optional[str] = typer.Option(None, "--output", "-o", help="Save ReleaseDecision JSON to file."),
    fail_on_review: bool = typer.Option(False, "--fail-on-review", help="Treat REVIEW decisions as BLOCK (exit code 1)."),
):
    """Execute regression suite against candidate model and gate release (BLOCK / REVIEW / PASS)."""
    print_banner()
    print(f"Executing Regression Bank for Candidate: {BOLD}{candidate}:{version}{RESET}\n")

    # Use explicit deterministic evaluator for CLI execution
    evaluator = DemoTestEvaluator()

    runner = RegressionRunner(
        failures_path=failures_file,
        regressions_path=regressions_file,
        evaluator=evaluator,
    )

    regressions = runner.load_regressions(regressions_file)
    if not regressions and Path("examples/mock_regressions.json").exists():
        regressions = runner.load_regressions("examples/mock_regressions.json")

    if not regressions:
        # Load from failures and compile
        failures = runner.load_failures(failures_file)
        if not failures and Path("examples/mock_failures.json").exists():
            failures = runner.load_failures("examples/mock_failures.json")
        regressions = [runner.compile_failure_to_regression(f) for f in failures if f.verification.status.lower() == "verified"]

    if not regressions:
        print(f"{RED}Error: No active regression records found.{RESET}")
        raise typer.Exit(code=1)

    candidate_model = ModelRef(name=candidate, version=version)

    decision = runner.run_regression_suite(
        candidate_model=candidate_model,
        regressions=regressions,
        decision_id="decision-001",
    )

    # Render results table
    headers = ["REGRESSION ID", "NAME", "METRIC", "OBSERVED", "THRESHOLD", "POLICY", "STATUS"]
    rows = []

    for chk in decision.detailed_checks:
        pol_color = RED if chk.policy.value == "block" else YELLOW
        if chk.status.value == "passed":
            st_badge = f"{GREEN}✓ PASS{RESET}"
            obs_str = f"{GREEN}{chk.observed_score:.2f}{RESET}"
        elif chk.status.value == "review_required":
            st_badge = f"{YELLOW}▲ REVIEW{RESET}"
            obs_str = f"{YELLOW}{chk.observed_score:.2f}{RESET}"
        else:
            st_badge = f"{RED}✖ FAIL{RESET}"
            obs_str = f"{RED}{chk.observed_score:.2f}{RESET}"

        rows.append([
            f"{BOLD}{chk.regression_id}{RESET}",
            chk.name,
            chk.metric_name,
            obs_str,
            f"{chk.minimum_threshold:.2f}",
            f"{pol_color}{chk.policy.value.upper()}{RESET}",
            st_badge,
        ])

    print(format_table(headers, rows))

    # Print high-visibility verdict card
    summary_dict = decision.summary.model_dump()
    print_verdict_card(
        decision=decision.decision.value,
        summary=summary_dict,
        reason=decision.reason,
        candidate_name=f"{candidate}:{version}",
    )

    if output_json:
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(decision.to_contract_dict(), f, indent=2)
        print(f"{DIM}Saved ReleaseDecision JSON to {output_json}{RESET}")

    # Set appropriate CI/CD exit code
    if decision.decision == DecisionEnum.BLOCK:
        raise typer.Exit(code=1)
    elif decision.decision == DecisionEnum.REVIEW and fail_on_review:
        raise typer.Exit(code=1)
    elif decision.decision == DecisionEnum.REVIEW:
        raise typer.Exit(code=2)
    else:
        raise typer.Exit(code=0)


@app.command("list")
def list_regressions(
    path: str = typer.Option("examples/mock_regressions.json", "--path", "-p", help="Path to regressions file or directory."),
):
    """List active and remembered regression tests in the suite."""
    print_banner()
    print(f"Listing Regression Bank: {DIM}{path}{RESET}\n")

    runner = RegressionRunner(regressions_path=path)
    regressions = runner.load_regressions(path)
    if not regressions and Path("examples/mock_regressions.json").exists():
        regressions = runner.load_regressions("examples/mock_regressions.json")

    if not regressions:
        print(f"{DIM}No regression records found.{RESET}")
        return

    headers = ["REGRESSION ID", "NAME", "CONDITION", "METRIC", "MIN THRESHOLD", "POLICY", "STATUS"]
    rows = []

    for r in regressions:
        status_str = f"{GREEN}enabled{RESET}" if r.enabled else f"{GRAY}disabled{RESET}"
        pol_color = RED if r.policy.value == "block" else YELLOW
        rows.append([
            f"{BOLD}{r.regression_id}{RESET}",
            r.name,
            r.condition.type,
            r.metric.name,
            f"{r.metric.minimum_threshold:.2f}",
            f"{pol_color}{r.policy.value.upper()}{RESET}",
            status_str,
        ])

    print(format_table(headers, rows))
    print(f"\n{DIM}Total active regressions: {len([r for r in regressions if r.enabled])} / {len(regressions)}{RESET}")
