"""Implementation of `modelshield scan` command."""
from __future__ import annotations

import json
from pathlib import Path
import sys
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
)
from core.scanner import ModelScanner

app = typer.Typer(help="Scan and verify ML model weights & packaging safety.")


def _safe_print(text: str = ""):
    try:
        print(text)
    except UnicodeEncodeError:
        # Fallback for restrictive non-utf8 Windows consoles (e.g. cp1252)
        clean = (
            text.replace("─", "-")
            .replace("✓", "v")
            .replace("✗", "x")
            .replace("●", "*")
            .replace("▲", "!")
        )
        print(clean)


def scan_command(
    model: str = typer.Argument("model.pkl", help="Path to model file to scan (e.g. model.pkl, resnet50-v3.pkl)."),
    candidate: Optional[str] = typer.Option(None, "--candidate", "-c", help="Candidate model name override."),
    version: Optional[str] = typer.Option(None, "--version", "-v", help="Candidate model version override."),
    failures_file: Optional[str] = typer.Option(None, "--failures", "-f", help="Custom failure records path."),
    regressions_file: Optional[str] = typer.Option(None, "--regressions", "-r", help="Custom regression records path."),
    output_json: Optional[str] = typer.Option(None, "--output", "-o", help="Output scan report to JSON file."),
):
    """Scan and verify model weights against ModelShield security engine."""
    # Ensure UTF-8 output if possible
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    model_path = Path(model)

    # If the user passes a model name that doesn't exist locally, check examples or models directory
    if not model_path.exists():
        if (Path("examples") / model).exists():
            model_path = Path("examples") / model
        elif (Path("models") / model).exists():
            model_path = Path("models") / model
        elif model == "model.pkl" and (Path("examples") / "resnet50-v3.pkl").exists():
            model_path = Path("examples") / "resnet50-v3.pkl"

    scanner = ModelScanner()
    result = scanner.scan(
        model_path=model_path,
        candidate_name=candidate,
        candidate_version=version,
        failures_file=failures_file,
        regressions_file=regressions_file,
    )

    # Format Output according to ModelShield CLI Specification
    _safe_print(f"\n{BOLD}ModelShield{RESET}")
    _safe_print(f"{GRAY}────────────────────────────────────────{RESET}\n")

    _safe_print(f"{'Model':<12}{BOLD}{result.model_name}{RESET}")
    _safe_print(f"{'Format':<12}{result.file_format}")
    _safe_print(f"{'SHA-256':<12}{DIM}{result.sha256_hash}{RESET}\n")

    _safe_print(f"{BOLD}Verification{RESET}")
    _safe_print(f"{GRAY}────────────────────────────────────────{RESET}\n")

    # Render check items
    chk_loading = f"{GREEN}[✓]{RESET}" if result.loading_ok else f"{RED}[✗]{RESET}"
    chk_integrity = f"{GREEN}[✓]{RESET}" if result.integrity_ok else f"{RED}[✗]{RESET}"
    chk_security = f"{GREEN}[✓]{RESET}" if result.security_ok else f"{RED}[✗]{RESET}"
    chk_policy = f"{GREEN}[✓]{RESET}" if result.policy_ok else f"{RED}[✗]{RESET}"

    _safe_print(f"{chk_loading} Model loading")
    _safe_print(f"{chk_integrity} Integrity verification")

    if result.security_ok:
        _safe_print(f"{chk_security} Security checks")
    else:
        _safe_print(f"{chk_security} Security checks {RED}({result.security_msg}){RESET}")

    if result.policy_ok:
        _safe_print(f"{chk_policy} Policy evaluation")
    else:
        _safe_print(f"{chk_policy} Policy evaluation {RED}({result.policy_msg}){RESET}")

    _safe_print(f"\n{GRAY}────────────────────────────────────────{RESET}\n")

    if result.exit_code == 0:
        _safe_print(f"{GREEN}{BOLD}>> {result.verdict}{RESET}\n")
    elif result.exit_code == 2:
        _safe_print(f"{YELLOW}{BOLD}>> {result.verdict}{RESET}\n")
    else:
        _safe_print(f"{RED}{BOLD}>> {result.verdict}{RESET}\n")

    if output_json:
        report = {
            "model": result.model_name,
            "format": result.file_format,
            "sha256": result.sha256_hash,
            "file_size": result.file_size_bytes,
            "loading": result.loading_ok,
            "integrity": result.integrity_ok,
            "security": result.security_ok,
            "policy": result.policy_ok,
            "verdict": result.verdict,
            "exit_code": result.exit_code,
        }
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        _safe_print(f"{DIM}Scan report saved to {output_json}{RESET}")

    if result.exit_code != 0:
        raise typer.Exit(code=result.exit_code)
