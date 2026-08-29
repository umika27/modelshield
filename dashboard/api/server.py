"""FastAPI backend for ModelShield Developer Dashboard.
Serves CLI state, regression records, failure memories, and release gating decisions.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from regression.runner import RegressionRunner
from regression.schemas import ModelRef

app = FastAPI(title="ModelShield Developer Dashboard API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE_ROOT = Path(__file__).parent.parent.parent
MOCK_FAILURES_PATH = WORKSPACE_ROOT / "examples" / "mock_failures.json"
MOCK_REGRESSIONS_PATH = WORKSPACE_ROOT / "examples" / "mock_regressions.json"

runner = RegressionRunner(
    failures_path=MOCK_FAILURES_PATH,
    regressions_path=MOCK_REGRESSIONS_PATH,
)


class EvaluateRequest(BaseModel):
    candidate_name: str = "candidate-v3"
    candidate_version: str = "v3"
    score_overrides: Optional[Dict[str, float]] = None


@app.get("/api/comparison")
def get_model_comparison():
    """View 1: Model Comparison (Baseline vs Candidate performance deltas)."""
    failures = runner.load_failures(MOCK_FAILURES_PATH)
    items = []
    for f in failures:
        b_score = f.metric.baseline_score
        c_score = f.metric.candidate_score
        delta = c_score - b_score
        items.append({
            "failure_id": f.failure_id,
            "condition": f.condition.type,
            "parameters": f.condition.parameters,
            "baseline_score": b_score,
            "candidate_score": c_score,
            "delta": round(delta, 4),
            "status": "failure" if delta < -0.15 else "passed",
            "severity": f.severity,
            "metric": f.metric.name,
        })
    return {
        "baseline_model": "production-v1",
        "candidate_model": "candidate-v2",
        "total_conditions": len(items),
        "failures_detected": len([i for i in items if i["status"] == "failure"]),
        "comparison_matrix": items,
    }


@app.get("/api/failures")
def get_failure_explorer():
    """View 2: Failure Explorer (Deep-dive into verified failures and capsules)."""
    failures = runner.load_failures(MOCK_FAILURES_PATH)
    return [f.model_dump() for f in failures]


@app.get("/api/memory")
def get_failure_memory():
    """View 3: Failure Memory (Active and remembered regression suites)."""
    regressions = runner.load_regressions(MOCK_REGRESSIONS_PATH)
    return [r.model_dump() for r in regressions]


@app.post("/api/memory/{regression_id}/toggle")
def toggle_regression(regression_id: str):
    """Toggle enabled status of a regression test."""
    regressions = runner.load_regressions(MOCK_REGRESSIONS_PATH)
    matching = [r for r in regressions if r.regression_id == regression_id]
    if not matching:
        raise HTTPException(status_code=404, detail="Regression not found")
    reg = matching[0]
    reg.enabled = not reg.enabled
    return {"regression_id": regression_id, "enabled": reg.enabled}


@app.get("/api/results")
def get_regression_results():
    """View 4: Regression Results (Detailed execution log across regression bank)."""
    candidate = ModelRef(name="candidate-v3", version="v3")
    score_overrides = {
        "regression-147": 0.49,
        "regression-152": 0.78,
        "regression-158": 0.72,
        "regression-163": 0.66,
        "regression-171": 0.75,
    }
    decision = runner.run_regression_suite(
        candidate_model=candidate,
        score_overrides=score_overrides,
    )
    return decision.model_dump()


@app.post("/api/gate/run")
def run_release_gate(req: EvaluateRequest):
    """View 5: Release Gate (Run gate and return BLOCK / REVIEW / PASS decision)."""
    candidate = ModelRef(name=req.candidate_name, version=req.candidate_version)
    overrides = req.score_overrides or {
        "regression-147": 0.49,
        "regression-152": 0.78,
        "regression-158": 0.72,
        "regression-163": 0.66,
        "regression-171": 0.75,
    }
    decision = runner.run_regression_suite(
        candidate_model=candidate,
        score_overrides=overrides,
    )
    return decision.model_dump()


@app.post("/api/replay/{failure_id}")
def replay_failure_endpoint(failure_id: str):
    """Deterministically replay a failure."""
    candidate = ModelRef(name="candidate-v3", version="v3")
    try:
        result = runner.replay_failure(failure_id, candidate, MOCK_FAILURES_PATH)
        return result.model_dump()
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


# Serve static dashboard files
static_dir = WORKSPACE_ROOT / "dashboard"
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
