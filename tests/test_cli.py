from pathlib import Path
import pytest
from typer.testing import CliRunner

from cli.main import app

runner = CliRunner()


def test_cli_info():
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "MODELSHIELD" in result.stdout
    assert "DISCOVER" in result.stdout
    assert "PROTECT" in result.stdout


def test_cli_test_command():
    result = runner.invoke(app, ["test", "--candidate", "candidate-v2", "--baseline", "production-v1"])
    assert result.exit_code == 0
    assert "Comparing Candidate" in result.stdout
    assert "candidate-v2" in result.stdout
    assert "CONDITION" in result.stdout
    assert "DELTA" in result.stdout


def test_cli_failures_list():
    result = runner.invoke(app, ["failures", "list"])
    assert result.exit_code == 0
    assert "FAILURE ID" in result.stdout
    assert "failure-147" in result.stdout


def test_cli_failures_inspect():
    result = runner.invoke(app, ["failures", "inspect", "failure-147"])
    assert result.exit_code == 0
    assert "low_light_blur" in result.stdout
    assert "failure-147" in result.stdout


def test_cli_regression_list():
    result = runner.invoke(app, ["regression", "list"])
    assert result.exit_code == 0
    assert "REGRESSION ID" in result.stdout
    assert "regression-147" in result.stdout


def test_cli_regression_run_blocks_candidate():
    # candidate-v3 fails regression-147 via DemoTestEvaluator (score 0.49 < 0.65 threshold), so release must be blocked (exit code 1)
    result = runner.invoke(app, ["regression", "run", "--candidate", "candidate-v3", "--version", "v3"])
    assert result.exit_code == 1
    assert "RELEASE BLOCKED" in result.stdout
    assert "regression-147" in result.stdout


def test_cli_replay_command():
    result = runner.invoke(app, ["replay", "failure-147", "--candidate", "candidate-v3"])
    assert result.exit_code == 0
    assert "Replaying Failure Test" in result.stdout
    assert "failure-147" in result.stdout
    assert "low_light_blur" in result.stdout
