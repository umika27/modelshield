/* Live API hydration for Kartikay's unchanged dashboard components. */

import { BASELINE_MODEL, CANDIDATE_PROFILES, dashboardState } from "./state.js";

export async function hydrateDashboardFromApi() {
  const response = await fetch("/api/analysis/latest");
  if (response.status === 404) return null;
  if (!response.ok) throw new Error((await response.json()).detail || "Live analysis is unavailable.");
  const analysis = await response.json();
  const condition = analysis.condition.type;
  BASELINE_MODEL.name = analysis.baseline.name;
  BASELINE_MODEL.version = analysis.baseline.version;
  BASELINE_MODEL.scores = { [condition]: analysis.metric.baseline_score };
  CANDIDATE_PROFILES[analysis.candidate.name] = {
    name: analysis.candidate.name, version: analysis.candidate.version,
    artifact_reference: analysis.candidate.id, scores: { [condition]: analysis.metric.candidate_score }
  };
  dashboardState.selectedCandidate = analysis.candidate.name;
  const candidateSelect = document.getElementById("model-select");
  if (candidateSelect) {
    candidateSelect.innerHTML = "";
    const option = document.createElement("option");
    option.value = analysis.candidate.name;
    option.textContent = `${analysis.candidate.name} (Live Analysis)`;
    option.selected = true;
    candidateSelect.appendChild(option);
  }
  dashboardState.failures = analysis.failure.fingerprint ? [{
    failure_id: analysis.failure.fingerprint, evaluation_id: analysis.analysis_id,
    experiment_id: analysis.experiment_id, model: { name: analysis.candidate.name, version: analysis.candidate.version },
    condition: analysis.condition, metric: analysis.metric,
    severity: analysis.failure.severity, verification: { status: analysis.verification.verified ? "verified" : "unverified", verification_runs: analysis.verification.runs, consistent: !!analysis.verification.verified },
    reproducibility_capsule_id: null, dataset: analysis.dataset, created_at: new Date().toISOString()
  }] : [];
  dashboardState.selectedFailureId = dashboardState.failures[0]?.failure_id || null;
  dashboardState.regressions = dashboardState.failures.map((failure, index) => ({
    regression_id: `regression-${index + 1}`, failure_id: failure.failure_id, name: `${condition} regression`, condition: analysis.condition,
    metric: { name: analysis.metric.name, minimum_threshold: analysis.metric.baseline_score * 0.8, review_margin: 0.05 },
    policy: analysis.release.verdict === "BLOCK" ? "block" : "warn", enabled: true
  }));
  dashboardState.capsules = {};
  dashboardState.liveDecision = analysis.release;
  return analysis;
}
