"""Typer CLI delegating orchestration to the shared ModelShieldService."""

from __future__ import annotations

import json

import typer

from integration.service import AnalysisRequest, DatasetConfig, ModelConfig, ModelShieldService

app = typer.Typer(name="modelshield", help="Run ModelShield analysis using real local artifacts.")


@app.command("info")
def info() -> None:
    """Print the available real-analysis entry point."""
    typer.echo("Run 'modelshield analyze --help' for local checkpoint analysis.")


@app.command("analyze")
def analyze(
    baseline_checkpoint: str = typer.Option(...),
    candidate_checkpoint: str = typer.Option(...),
    dataset_root: str = typer.Option(...),
    architecture: str = typer.Option("resnet18"),
    challenge: str = typer.Option("clean"),
    max_samples: int | None = typer.Option(None),
) -> None:
    """Evaluate local checkpoints and print the shared service result as JSON."""
    service = ModelShieldService()
    result = service.run_analysis(AnalysisRequest(
        baseline=ModelConfig("baseline", "local", architecture, baseline_checkpoint),
        candidate=ModelConfig("candidate", "local", architecture, candidate_checkpoint),
        dataset=DatasetConfig("cifar10", dataset_root),
        challenge_type=challenge,
        max_samples=max_samples,
    ))
    typer.echo(json.dumps(result.to_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    app()
