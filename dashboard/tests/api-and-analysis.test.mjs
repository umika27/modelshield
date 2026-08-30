import test from "node:test";
import assert from "node:assert/strict";
import { createModelShieldApi, ApiError, sanitizeApiErrorDetail } from "../api.js";
import { normalizeAnalysis, formatScore, releaseOverview, measuredComparison } from "../analysis.js";
import { ANALYSIS_STATES, DashboardStore } from "../state.js";
import { normalizeInvestigation, parameterEntries, sourceLabel, tracePresentation } from "../investigation.js";
import { FINDING_STATES, normalizeVerifiedFindings } from "../findings.js";
import { normalizeHistoricalReplays, replayOutcomePresentation } from "../replays.js";
import { analysisSummary, releaseDecisionPresentation } from "../release.js";

const response = (body, status = 200) => ({ ok: status >= 200 && status < 300, status, json: async () => body });
const fixture = () => ({ analysis_id: "analysis-1", experiment_id: "exp-1", baseline: { id: "base:v1", name: "base", version: "v1", score: 0 }, candidate: { id: "candidate:v2", name: "candidate", version: "v2", score: 0 }, dataset: { type: "cifar10" }, condition: { type: "clean", parameters: {} }, metric: { name: "accuracy", baseline_score: 0, candidate_score: 0, delta: 0 }, status: "pass", verification: { required: false, verified: null, runs: 0, successful_reproductions: 0 }, failure: { fingerprint: null, severity: null }, release: { verdict: "PASS", rationale: "No verified failures.", findings: [] }, historical_replays: [] });

test("analyze posts the backend request and returns its JSON", async () => {
  let call; const api = createModelShieldApi(async (...args) => { call = args; return response(fixture()); });
  const result = await api.analyze({ baseline: {} });
  assert.equal(call[0], "/api/analyze"); assert.equal(call[1].method, "POST"); assert.deepEqual(result, fixture());
});
test("latest analysis returns a truthful API error", async () => {
  const api = createModelShieldApi(async () => response({ detail: "No real analysis has been run yet." }, 404));
  await assert.rejects(api.getLatestAnalysis(), (error) => error instanceof ApiError && error.status === 404 && error.message === "No real analysis has been run yet.");
});
test("API error sanitizer preserves useful detail while redacting paths and secrets", () => {
  assert.equal(sanitizeApiErrorDetail("Dataset could not be loaded from C:\\Users\\model\\data", "Analysis request failed."), "Dataset could not be loaded from [redacted path]");
  assert.equal(sanitizeApiErrorDetail("Dataset could not be loaded from /home/model/data", "Analysis request failed."), "Dataset could not be loaded from [redacted path]");
  assert.equal(sanitizeApiErrorDetail("Dataset could not be loaded from \\\\server\\share\\project\\file.txt", "Analysis request failed."), "Dataset could not be loaded from [redacted path]");
  assert.equal(sanitizeApiErrorDetail("Dataset could not be loaded from \\\\server\\share\\project\\file.txt; retry with a supported dataset.", "Analysis request failed."), "Dataset could not be loaded from [redacted path]; retry with a supported dataset.");
  assert.equal(sanitizeApiErrorDetail("Model checkpoint incompatible.", "Analysis request failed."), "Model checkpoint incompatible.");
  assert.equal(sanitizeApiErrorDetail("Authorization: Bearer private-token", "Analysis request failed."), "Analysis request failed.");
  assert.equal(sanitizeApiErrorDetail("token=private-token", "Analysis request failed."), "Analysis request failed.");
  assert.equal(sanitizeApiErrorDetail("secret=private-value", "Analysis request failed."), "Analysis request failed.");
  assert.equal(sanitizeApiErrorDetail("password=private-value", "Analysis request failed."), "Analysis request failed.");
  assert.equal(sanitizeApiErrorDetail('Traceback (most recent call last): File "internal.py"', "Analysis request failed."), "Analysis request failed.");
});
test("normalization preserves zero scores and backend release/replay values", () => {
  const analysis = normalizeAnalysis(fixture());
  assert.equal(analysis.metric.baselineScore, 0); assert.equal(analysis.metric.delta, 0); assert.equal(analysis.release.verdict, "PASS"); assert.deepEqual(analysis.replays, []); assert.equal(formatScore(0), "0.0%");
});
test("normalization marks missing optional fields partial without inventing values", () => {
  const raw = fixture(); delete raw.historical_replays; delete raw.release;
  const analysis = normalizeAnalysis(raw);
  assert.equal(analysis.isPartial, true); assert.equal(analysis.replays, null); assert.equal(analysis.release, null); assert.equal(formatScore(null), "Unavailable");
});
test("state distinguishes initial, loading, empty, error, and partial analysis", () => {
  const store = new DashboardStore();
  assert.equal(store.status, ANALYSIS_STATES.INITIAL);
  store.setLoading(); assert.equal(store.status, ANALYSIS_STATES.LOADING);
  store.setEmpty(); assert.equal(store.status, ANALYSIS_STATES.EMPTY);
  store.setError(new Error("request failed")); assert.equal(store.status, ANALYSIS_STATES.ERROR);
  store.setAnalysis({ isPartial: true }); assert.equal(store.status, ANALYSIS_STATES.PARTIAL);
});
test("overview and comparison use backend-provided model, dataset, metric, and delta", () => {
  const raw = fixture();
  raw.baseline.framework = "pytorch"; raw.candidate.architecture = "resnet18";
  raw.dataset.split = "test"; raw.dataset.sample_count = 100;
  raw.metric.baseline_score = 0.8; raw.metric.candidate_score = 0.9; raw.metric.delta = -0.25;
  const analysis = normalizeAnalysis(raw), overview = releaseOverview(analysis), comparison = measuredComparison(analysis);
  assert.equal(overview.production.framework, "pytorch"); assert.equal(overview.candidate.architecture, "resnet18"); assert.equal(overview.dataset.sampleCount, 100);
  assert.equal(comparison.metricName, "accuracy"); assert.equal(comparison.baselineScore, 0.8); assert.equal(comparison.candidateScore, 0.9); assert.equal(comparison.delta, -0.25);
});
test("candidate improvement does not manufacture a release PASS", () => {
  const raw = fixture(); raw.metric.baseline_score = 0.8; raw.metric.candidate_score = 0.9; raw.metric.delta = 0.1; raw.release.verdict = "BLOCK";
  const comparison = measuredComparison(normalizeAnalysis(raw));
  assert.equal(comparison.delta, 0.1); assert.equal(comparison.releaseVerdict, "BLOCK");
});
test("missing overview and metric data remains unavailable", () => {
  const raw = { analysis_id: "analysis-2", baseline: null, candidate: null, dataset: null, metric: null };
  const analysis = normalizeAnalysis(raw), overview = releaseOverview(analysis), comparison = measuredComparison(analysis);
  assert.equal(overview.production, null); assert.equal(overview.dataset, null); assert.equal(comparison.metricName, null); assert.equal(formatScore(comparison.baselineScore), "Unavailable");
});
test("missing investigation remains unavailable without synthetic trace data", () => {
  assert.equal(normalizeInvestigation(undefined), null);
  assert.equal(normalizeAnalysis(fixture()).investigation, null);
});
test("investigation summary and executed trace preserve real-shaped measured data", () => {
  const investigation = normalizeInvestigation({ investigation_id: "inv-1", experiment_budget: 3, experiments_executed: 1, termination_reason: "agent_terminated", trace: [{ state: "executed", action: { rationale: "Inspect illumination sensitivity.", challenge: { challenge_id: "c-1", type: "low_light", parameters: { brightness: 0 }, source: "ai_investigation", seed: 42 } }, evaluation: { status: "failure", metric: { name: "accuracy", baseline_score: 0, candidate_score: 0, delta: 0 } }] });
  const entry = investigation.trace[0], presentation = tracePresentation(entry);
  assert.equal(investigation.investigationId, "inv-1"); assert.equal(investigation.experimentBudget, 3); assert.equal(presentation.isAiSelected, true); assert.equal(presentation.source, "AI-selected experiment"); assert.equal(presentation.hasMeasurement, true); assert.equal(entry.evaluation.metric.delta, 0); assert.deepEqual(parameterEntries(entry.action.challenge.parameters), [["brightness", "0"]]);
});
test("rejected and skipped trace entries never gain evaluations", () => {
  const investigation = normalizeInvestigation({ trace: [{ state: "rejected", action: { challenge: { type: "blur", parameters: {} } }, reason: "Invalid severity." }, { state: "skipped", action: { challenge: { type: "blur", parameters: {} } }, reason: "Duplicate effective experiment." }] });
  for (const entry of investigation.trace) { assert.equal(entry.evaluation, null); assert.equal(tracePresentation(entry).hasMeasurement, false); }
  assert.equal(tracePresentation(investigation.trace[0]).state, "REJECTED"); assert.equal(tracePresentation(investigation.trace[1]).state, "SKIPPED");
});
test("adaptive fallback and absent rationale have truthful labels", () => {
  assert.equal(sourceLabel("adaptive_investigation"), "Deterministic investigation fallback");
  const entry = normalizeInvestigation({ trace: [{ state: "executed", action: { challenge: { type: "noise", parameters: null, source: "adaptive_investigation" } }] }).trace[0];
  assert.equal(tracePresentation(entry).rationale, null); assert.deepEqual(parameterEntries(entry.action.challenge.parameters), []);
});
test("verified finding preserves real deterministic evidence", () => {
  const raw = fixture(); raw.status = "failure"; raw.condition = { type: "low_light", parameters: { brightness: 0 } }; raw.metric = { name: "accuracy", baseline_score: 0, candidate_score: 0, delta: 0 }; raw.threshold = -0.15; raw.reproducibility = { seed: 42 }; raw.verification = { required: true, verified: true, runs: 3, successful_reproductions: 3 }; raw.failure = { fingerprint: "sha256:real", severity: "HIGH" };
  const findings = normalizeVerifiedFindings(raw), finding = findings.items[0];
  assert.equal(findings.state, FINDING_STATES.VERIFIED); assert.equal(finding.condition.type, "low_light"); assert.equal(finding.metric.delta, 0); assert.equal(finding.verification.runs, 3); assert.equal(finding.fingerprint, "sha256:real"); assert.equal(finding.severity, "HIGH");
});
test("authoritative non-verified state yields no verified findings, not a synthetic finding", () => {
  const raw = fixture(); raw.status = "failure"; raw.metric.delta = -0.5; raw.verification = { required: true, verified: false, runs: 3, successful_reproductions: 1 };
  const findings = normalizeVerifiedFindings(raw);
  assert.equal(findings.state, FINDING_STATES.NONE); assert.deepEqual(findings.items, []);
});
test("missing verification evidence keeps findings unavailable and makes no memory claim", () => {
  const raw = fixture(); delete raw.verification; raw.failure = { fingerprint: null, severity: null };
  const findings = normalizeVerifiedFindings(raw);
  assert.equal(findings.state, FINDING_STATES.UNAVAILABLE); assert.deepEqual(findings.items, []);
});
test("historical context remains separate from current replay evidence", () => {
  const replays = normalizeHistoricalReplays([{ fingerprint: "sha256:historical", source_failure_id: 12, condition: { type: "low_light", parameters: { brightness: 0 } }, outcome: "PASS", evaluation: { status: "pass", baseline: { name: "production", version: "v1" }, candidate: { name: "candidate", version: "v3" }, metric: { name: "accuracy", baseline_score: 0, candidate_score: 0, delta: 0 } } }]);
  const replay = replays[0];
  assert.equal(replay.historicalCondition.type, "low_light"); assert.equal(replay.currentEvaluation.metric.delta, 0); assert.equal(replayOutcomePresentation(replay.outcome).label, "PASS"); assert.equal(replay.currentEvaluation.candidate.name, "candidate");
});
test("backend replay outcomes remain authoritative for pass, fail, and skipped", () => {
  assert.equal(replayOutcomePresentation("PASS").label, "PASS");
  assert.equal(replayOutcomePresentation("FAIL").label, "FAIL");
  assert.equal(replayOutcomePresentation("SKIPPED").label, "SKIPPED");
  assert.equal(replayOutcomePresentation("SKIPPED").explanation, "Replay was not executed.");
});
test("missing replay evidence and no replay records remain distinct", () => {
  assert.equal(normalizeHistoricalReplays(undefined), null);
  assert.deepEqual(normalizeHistoricalReplays([]), []);
  const skipped = normalizeHistoricalReplays([{ fingerprint: "sha256:x", outcome: "SKIPPED", reason: "Unsupported condition." }])[0];
  assert.equal(skipped.currentEvaluation, null); assert.equal(skipped.reason, "Unsupported condition.");
});
test("replay and fingerprint never create a Failure Memory storage claim", () => {
  const replay = normalizeHistoricalReplays([{ fingerprint: "sha256:x", outcome: "FAIL" }])[0];
  assert.equal(Object.prototype.hasOwnProperty.call(replay, "memoryStored"), false);
});
test("release decision passes through backend PASS, REVIEW, BLOCK, and unknown verdicts", () => {
  for (const verdict of ["PASS", "REVIEW", "BLOCK", "HOLD"]) {
    const decision = releaseDecisionPresentation({ verdict, rationale: "Backend reason.", findings: [] });
    assert.equal(decision.verdict, verdict); assert.equal(decision.rationale, "Backend reason.");
  }
  assert.equal(releaseDecisionPresentation(null), null);
});
test("certificate uses available analysis metadata without fabricating optional fields", () => {
  const raw = fixture(); raw.release = { verdict: "BLOCK", rationale: "Backend evidence.", findings: [] }; raw.historical_replays = []; raw.investigation = { investigation_id: "inv-1", experiments_executed: 0, trace: [] };
  const summary = analysisSummary(normalizeAnalysis(raw));
  assert.equal(summary.analysisId, "analysis-1"); assert.equal(summary.decision.verdict, "BLOCK"); assert.equal(summary.investigationId, "inv-1"); assert.equal(summary.experimentsExecuted, 0); assert.equal(summary.replayRecords, 0);
});
test("metrics never determine frontend release verdict", () => {
  const raw = fixture(); raw.metric = { name: "accuracy", baseline_score: 0, candidate_score: 1, delta: 1 }; raw.release = { verdict: "BLOCK", rationale: "Backend decision.", findings: [] };
  assert.equal(analysisSummary(normalizeAnalysis(raw)).decision.verdict, "BLOCK");
});
