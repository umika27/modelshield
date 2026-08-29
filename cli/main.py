"""ModelShield Root CLI Application.
Clean developer CLI inspired by GitHub CLI, Docker CLI, and VS Code.
"""
from __future__ import annotations

import typer

from cli.commands.failures import app as failures_app
from cli.commands.regression import app as regression_app
from cli.commands.replay import replay_command
from cli.commands.test import test_command
from cli.formatters import BOLD, CYAN, DIM, GRAY, RESET, print_banner

app = typer.Typer(
    name="modelshield",
    help="ModelShield: Adaptive ML Verification & Regression Release Gating Layer.",
    no_args_is_help=True,
)

# Register top-level commands and groups
app.command("test", help="Run verification & challenge tests on a candidate model.")(test_command)
app.command("replay", help="Deterministically replay a verified failure test.")(replay_command)
app.add_typer(failures_app, name="failures")
app.add_typer(regression_app, name="regression")


@app.command("info")
def info_command():
    """Print ModelShield system and verification status."""
    print_banner()
    print(f"{BOLD}Core Verification Loop:{RESET}")
    print(f"  {CYAN}DISCOVER{RESET}  → Find subtle performance drops under challenge conditions")
    print(f"  {CYAN}INVESTIGATE{RESET} → Stress test failure boundaries and sensitivities")
    print(f"  {CYAN}VERIFY{RESET}     → Reproduce and freeze failure capsules")
    print(f"  {CYAN}REMEMBER{RESET}   → Compile verified failures into active regression tests")
    print(f"  {CYAN}PROTECT{RESET}    → Gate releases and block regressions in CI/CD\n")
    print(f"{BOLD}Quick Commands:{RESET}")
    print(f"  {DIM}$ modelshield test{RESET}              # Run candidate vs baseline comparison")
    print(f"  {DIM}$ modelshield failures list{RESET}     # View stored failure memories")
    print(f"  {DIM}$ modelshield regression run{RESET}    # Run regression suite & gate release")
    print(f"  {DIM}$ modelshield replay <id>{RESET}       # Deterministically replay a test\n")


def main():
    app()


if __name__ == "__main__":
    main()
