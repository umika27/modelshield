"""Implementation of `modelshield test` command."""
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
)
from regression.runner import RegressionRunner
from regression.schemas import ModelRef

app = typer.Typer(help="Run verification & challenge tests on a candidate model.")


@app.callback(invoke_without_command=True)
def test_command(
    candidate: str = typer.Option("candidate-v2", "--candidate", "-c", help="Candidate model name/id."),
    version: str = typer.Option("v2", "--version", "-v", help="Candidate model version."),
    baseline: str = typer.Option("production-v1", "--baseline", "-b", help="Baseline model for comparison."),
    failures_file: str = typer.Option("examples/mock_failures.json", "--failures", "-f", help="Path to stored failures or test suite."),
    threshold: float = typer.Option(-0.15, "--threshold", "-t", help="Allowable delta degradation threshold before flagging failure."),
    output_json: Optional[str] = typer.Option(None, "--output", "-o", help="Optional output JSON path for test results."),
):
    """Execute model verification and challenge suite against baseline."""
    print_banner()
    print(f"Comparing Candidate {BOLD}{candidate}:{version}{RESET} against Baseline {BOLD}{baseline}{RESET}")
    print(f"Max degradation threshold: {YELLOW}{threshold:+.2f}{RESET}\n")

    runner = RegressionRunner()
    failures = runner.load_failures(failures_file)

    if not failures:
        # Fallback to default examples/mock_failures.json or examples/failure_record.json
        for p in ["examples/mock_failures.json", "examples/failure_record.json", "docs/contracts/failure_record.json"]:
            if Path(p).exists():
                failures = runner.load_failures(p)
                break

    headers = ["CONDITION", "PARAMETERS", "BASELINE", "CANDIDATE", "DELTA", "VERDICT"]
    rows = []
    discovered_failures = 0

    results_data = []

    for f in failures:
        params_str = ", ".join(f"{k}={v}" for k, v in f.condition.parameters.items())
        b_score = f.metric.baseline_score
        c_score = f.metric.candidate_score
        delta = c_score - b_score

        is_fail = delta < threshold
        if is_fail:
            discovered_failures += 1
            verdict = f"{RED}✖ FAILED{RESET}"
            delta_str = f"{RED}{delta:+.2f}{RESET}"
        else:
            verdict = f"{GREEN}✓ PASSED{RESET}"
            delta_str = f"{GREEN}{delta:+.2f}{RESET}"

        rows.append([
            f"{BOLD}{f.condition.type}{RESET}",
            f"{DIM}{params_str}{RESET}",
            f"{b_score:.2f}",
            f"{c_score:.2f}",
            delta_str,
            verdict,
        ])

        results_data.append({
            "condition": f.condition.type,
            "parameters": f.condition.parameters,
            "baseline": b_score,
            "candidate": c_score,
            "delta": delta,
            "status": "failure" if is_fail else "passed",
        })

    print(format_table(headers, rows))
    print(f"\n{GRAY}───────────────────────────────────────────────────────────────────{RESET}")
    if discovered_failures > 0:
        print(f"{RED}● Discovered {discovered_failures} failure condition(s). Added to failure memory.{RESET}")
    else:
        print(f"{GREEN}✓ All conditions passed within degradation tolerance.{RESET}")

    if output_json:
        with open(output_json, "w", encoding="utf-8") as out_f:
            json.dump(results_data, out_f, indent=2)
        print(f"{DIM}Results saved to {output_json}{RESET}")
