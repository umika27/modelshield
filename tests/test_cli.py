from pathlib import Path
import zipfile
import pytest
from typer.testing import CliRunner

from cli import __version__
from cli.main import app

runner = CliRunner()


def test_cli_version_flag():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert f"modelshield version {__version__}" in result.stdout


def test_cli_version_command():
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert f"modelshield version {__version__}" in result.stdout


def test_cli_info():
    result = runner.invoke(app, ["info"])
    assert result.exit_code == 0
    assert "MODELSHIELD" in result.stdout
    assert "DISCOVER" in result.stdout
    assert "PROTECT" in result.stdout


def test_cli_scan_valid_model():
    result = runner.invoke(app, ["scan", "examples/resnet50-v3.pkl"])
    assert result.exit_code == 0
    assert "ModelShield" in result.stdout
    assert "Model" in result.stdout
    assert "resnet50-v3.pkl" in result.stdout
    assert "Pickle" in result.stdout
    assert "SHA-256" in result.stdout
    assert "Model loading" in result.stdout
    assert "Integrity verification" in result.stdout
    assert "Security checks" in result.stdout
    assert "Policy evaluation" in result.stdout
    assert "VERIFIED" in result.stdout
    assert "RELEASE APPROVED" in result.stdout


def test_cli_scan_missing_model_error():
    result = runner.invoke(app, ["scan", "totally_missing_model_file.pkl"])
    assert result.exit_code == 1
    assert "ERROR" in result.stdout
    assert "MODEL FILE NOT FOUND" in result.stdout


def test_cli_scan_security_violation_blocks():
    result = runner.invoke(app, ["scan", "examples/malicious_model.pkl"])
    assert result.exit_code == 1
    assert "RELEASE BLOCKED" in result.stdout
    assert "SECURITY VIOLATION" in result.stdout
    assert "os.system" in result.stdout


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
    # candidate-v3 fails regression-147 via DemoTestEvaluator (score 0.40 < 0.65 threshold), so release must be blocked (exit code 1)
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


def test_packaged_wheel_artifact_contents():
    wheel_files = list(Path("dist").glob("*.whl"))
    assert len(wheel_files) > 0, "Built wheel file must exist in dist/"
    wheel_path = wheel_files[0]
    
    with zipfile.ZipFile(wheel_path, "r") as zf:
        namelist = zf.namelist()
        assert any("cli/main.py" in n for n in namelist)
        assert any("core/scanner.py" in n for n in namelist)
        assert any("entry_points.txt" in n for n in namelist)
        
        # Verify console script entry point
        ep_entry = [n for n in namelist if "entry_points.txt" in n][0]
        ep_content = zf.read(ep_entry).decode("utf-8")
        assert "modelshield = cli.main:main" in ep_content
