"""Terminal formatting utilities for ModelShield CLI.
Inspired by GitHub CLI (gh), Docker CLI, and VS Code terminal output.
Clean, developer-focused, monospace-friendly.
"""
from __future__ import annotations

import sys
from typing import Any, Dict, List, Optional

# Ensure UTF-8 output on modern terminals if possible
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# ANSI Color & Style Constants
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
UNDERLINE = "\033[4m"

# Standard Developer CLI Colors
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
GRAY = "\033[90m"
WHITE = "\033[97m"

# Backgrounds
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"


def safe_print(text: str = ""):
    """Print with fallback encoding for restrictive Windows consoles."""
    try:
        print(text)
    except UnicodeEncodeError:
        clean = (
            text.replace("─", "-")
            .replace("┌", "+")
            .replace("┐", "+")
            .replace("└", "+")
            .replace("┘", "+")
            .replace("│", "|")
            .replace("✓", "v")
            .replace("✖", "x")
            .replace("✗", "x")
            .replace("●", "*")
            .replace("▲", "!")
            .replace("—", "-")
            .replace("→", "->")
        )
        print(clean)


def colorize(text: str, color_code: str) -> str:
    """Format string with ANSI escape codes."""
    return f"{color_code}{text}{RESET}"


def badge(status: str) -> str:
    """Return a developer-style status badge."""
    st = status.upper()
    if st in ("PASS", "PASSED", "VERIFIED", "ENABLED"):
        return f"{GREEN}● PASS{RESET}"
    elif st in ("BLOCK", "BLOCKED", "FAILED", "FAIL", "CRITICAL"):
        return f"{RED}✖ BLOCK{RESET}"
    elif st in ("REVIEW", "REVIEW_REQUIRED", "WARN", "HIGH", "MEDIUM"):
        return f"{YELLOW}▲ REVIEW{RESET}"
    elif st in ("DISABLED", "ALLOW", "LOW"):
        return f"{GRAY}○ {st}{RESET}"
    return f"{CYAN}{st}{RESET}"


def print_banner():
    """Print clean ModelShield developer header."""
    safe_print(f"\n{BOLD}{CYAN}MODELSHIELD{RESET} {DIM}v1.0.0 — Adaptive ML Verification & Release Gating{RESET}")
    safe_print(f"{GRAY}───────────────────────────────────────────────────────────────────{RESET}")


def format_table(headers: List[str], rows: List[List[str]], alignments: Optional[List[str]] = None) -> str:
    """Render a clean GitHub CLI / Docker CLI style table."""
    if not rows:
        return f"{DIM}No records found.{RESET}"

    # Calculate column widths
    col_widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            # Strip ANSI for length calculation
            clean_cell = cell
            for c in [RESET, BOLD, DIM, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, GRAY, WHITE]:
                clean_cell = clean_cell.replace(c, "")
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(clean_cell))

    alignments = alignments or ["<"] * len(headers)

    # Build header line
    header_parts = []
    for i, h in enumerate(headers):
        header_parts.append(f"{BOLD}{GRAY}{h:<{col_widths[i]}}{RESET}")
    header_line = "  ".join(header_parts)

    divider = "  ".join([f"{GRAY}{'─' * w}{RESET}" for w in col_widths])

    # Build rows
    row_lines = []
    for row in rows:
        row_parts = []
        for i, cell in enumerate(row):
            clean_cell = cell
            for c in [RESET, BOLD, DIM, RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, GRAY, WHITE]:
                clean_cell = clean_cell.replace(c, "")
            pad = col_widths[i] - len(clean_cell)
            if alignments[i] == ">":
                row_parts.append(f"{' ' * pad}{cell}")
            else:
                row_parts.append(f"{cell}{' ' * pad}")
        row_lines.append("  ".join(row_parts))

    return f"{header_line}\n{divider}\n" + "\n".join(row_lines)


def print_verdict_card(decision: str, summary: Dict[str, Any], reason: str, candidate_name: str):
    """Render high-visibility CI/CD verdict card."""
    dec = decision.upper()
    safe_print(f"\n{GRAY}┌─────────────────────────────────────────────────────────────────┐{RESET}")
    if dec == "BLOCK":
        safe_print(f"{GRAY}│{RESET}  {BG_RED}{WHITE}{BOLD} ✖ RELEASE BLOCKED {RESET}  Candidate: {BOLD}{candidate_name}{RESET}")
        safe_print(f"{GRAY}│{RESET}  {RED}{reason}{RESET}")
    elif dec == "REVIEW":
        safe_print(f"{GRAY}│{RESET}  {BG_YELLOW}{WHITE}{BOLD} ▲ REVIEW REQUIRED {RESET}  Candidate: {BOLD}{candidate_name}{RESET}")
        safe_print(f"{GRAY}│{RESET}  {YELLOW}{reason}{RESET}")
    else:
        safe_print(f"{GRAY}│{RESET}  {BG_GREEN}{WHITE}{BOLD} ✓ RELEASE APPROVED {RESET}  Candidate: {BOLD}{candidate_name}{RESET}")
        safe_print(f"{GRAY}│{RESET}  {GREEN}{reason}{RESET}")

    total = summary.get("total_regressions", 0)
    passed = summary.get("passed", 0)
    failed = summary.get("failed", 0)
    review = summary.get("review_required", 0)

    safe_print(f"{GRAY}│{RESET}")
    safe_print(
        f"{GRAY}│{RESET}  {DIM}Total Tests:{RESET} {total}  "
        f"│  {GREEN}Passed:{RESET} {passed}  "
        f"│  {RED}Failed:{RESET} {failed}  "
        f"│  {YELLOW}Review:{RESET} {review}"
    )
    safe_print(f"{GRAY}└─────────────────────────────────────────────────────────────────┘{RESET}\n")
