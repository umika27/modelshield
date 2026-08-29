"""Implementation of `modelshield failures` command group."""
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

app = typer.Typer(help="Inspect and query stored failure records from memory.")


@app.command("list")
def list_failures(
    path: str = typer.Option("examples/mock_failures.json", "--path", "-p", help="Path to failures file or directory."),
    severity: Optional[str] = typer.Option(None, "--severity", "-s", help="Filter by severity (critical, high, medium, low)."),
):
    """List all stored failure records in memory."""
    print_banner()
    print(f"Querying Failure Memory: {DIM}{path}{RESET}\n")

    runner = RegressionRunner()
    failures = runner.load_failures(path)
    if not failures and Path("examples/mock_failures.json").exists():
        failures = runner.load_failures("examples/mock_failures.json")

    if severity:
        failures = [f for f in failures if f.severity.lower() == severity.lower()]

    if not failures:
        print(f"{DIM}No failure records found matching criteria.{RESET}")
        return

    headers = ["FAILURE ID", "CONDITION", "SEVERITY", "BASELINE", "CANDIDATE", "DELTA", "VERIFIED", "CAPSULE"]
    rows = []

    for f in failures:
        sev_color = RED if f.severity.lower() in ("critical", "high") else YELLOW
        delta_color = RED if f.metric.delta < -0.15 else YELLOW
        verified_str = f"{GREEN}yes ({f.verification.verification_runs}x){RESET}" if f.verification.consistent else f"{RED}no{RESET}"
        capsule_id = f.reproducibility_capsule_id or "n/a"

        rows.append([
            f"{BOLD}{f.failure_id}{RESET}",
            f.condition.type,
            f"{sev_color}{f.severity}{RESET}",
            f"{f.metric.baseline_score:.2f}",
            f"{f.metric.candidate_score:.2f}",
            f"{delta_color}{f.metric.delta:+.2f}{RESET}",
            verified_str,
            f"{CYAN}{capsule_id}{RESET}",
        ])

    print(format_table(headers, rows))
    print(f"\n{DIM}Total stored failures: {len(failures)} | Use `modelshield replay <failure_id>` to re-test.{RESET}")


@app.command("inspect")
def inspect_failure(
    failure_id: str = typer.Argument(..., help="The failure ID to inspect."),
    path: str = typer.Option("examples/mock_failures.json", "--path", "-p", help="Path to failures file or directory."),
):
    """View full JSON details for a specific failure record."""
    print_banner()
    runner = RegressionRunner()
    failures = runner.load_failures(path)
    if not failures and Path("examples/mock_failures.json").exists():
        failures = runner.load_failures("examples/mock_failures.json")

    matching = [f for f in failures if f.failure_id == failure_id]
    if not matching:
        print(f"{RED}Error: Failure ID '{failure_id}' not found.{RESET}")
        raise typer.Exit(code=1)

    record = matching[0]
    print(f"Inspection for {BOLD}{record.failure_id}{RESET}:")
    print(f"{GRAY}───────────────────────────────────────────────────────────────────{RESET}")
    print(json.dumps(record.model_dump(), indent=2))
