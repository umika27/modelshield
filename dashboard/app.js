import { modelShieldApi, ApiError } from "./api.js";
import { normalizeAnalysis, displayValue, formatScore, releaseOverview, measuredComparison } from "./analysis.js";
import { parameterEntries, tracePresentation } from "./investigation.js";
import { FINDING_STATES } from "./findings.js";
import { replayOutcomePresentation } from "./replays.js";
import { analysisSummary, releaseDecisionPresentation } from "./release.js";
import { ANALYSIS_STATES, dashboardStore } from "./state.js";

const main = () => document.getElementById("view-content");
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[character]);
const modelLabel = (model) => model ? [model.name, model.version].filter(Boolean).join(" ") || "Model information unavailable" : "Model information unavailable";
const detail = (label, value) => `<li><span>${escapeHtml(label)}</span><strong>${escapeHtml(displayValue(value))}</strong></li>`;

function renderState(title, message, kind = "info") { main().innerHTML = `<section class="placeholder-view state-${kind}" role="status" aria-live="polite"><h1 class="placeholder-title">${escapeHtml(title)}</h1><p class="placeholder-subtitle">${escapeHtml(message)}</p></section>`; }
function renderModelCard(role, model) {
  return `<article class="release-entity"><p class="eyebrow">${escapeHtml(role)}</p><h3>${escapeHtml(modelLabel(model))}</h3><ul class="metadata-list">${detail("Model ID", model?.id)}${detail("Architecture", model?.architecture)}${detail("Framework", model?.framework)}${detail("Task", model?.task)}</ul></article>`;
}
function renderParameters(parameters) {
  const entries = parameterEntries(parameters);
  return entries.length ? `<dl class="trace-parameters">${entries.map(([key, value]) => `<div><dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd></div>`).join("")}</dl>` : '<p class="trace-muted">No parameters supplied.</p>';
}
function renderTraceEntry(entry) {
  const presentation = tracePresentation(entry), metric = entry.evaluation?.metric;
  const reason = presentation.reason ? `<p class="trace-reason"><strong>Reason:</strong> ${escapeHtml(presentation.reason)}</p>` : "";
  const rationale = presentation.rationale ? `<div class="ai-rationale"><span>AI hypothesis</span><p>${escapeHtml(presentation.rationale)}</p></div>` : "";
  const measurement = presentation.hasMeasurement ? `<div class="trace-measurement"><span>Deterministically evaluated</span><div><strong>${escapeHtml(displayValue(metric?.name, "Metric unavailable"))}</strong><span>Baseline ${formatScore(metric?.baselineScore)} · Candidate ${formatScore(metric?.candidateScore)} · Delta ${formatScore(metric?.delta)}</span></div><p>Measured result: ${escapeHtml(displayValue(entry.evaluation?.status))}</p></div>` : "";
  const stateMessage = entry.state === "rejected" ? "AI proposal rejected" : entry.state === "skipped" ? "Experiment skipped" : "";
  return `<article class="trace-entry trace-${escapeHtml(entry.state || "unavailable")}"><div class="trace-marker"><span>Experiment ${String(entry.order).padStart(2, "0")}</span><strong>${escapeHtml(presentation.state)}</strong></div><div class="trace-content"><h3>${escapeHtml(presentation.title)}</h3><p class="trace-source">${escapeHtml(presentation.source)}</p>${rationale}${renderParameters(entry.action?.challenge?.parameters)}${measurement}${stateMessage ? `<p class="trace-state-message">${escapeHtml(stateMessage)}</p>` : ""}${reason}</div></article>`;
}
function renderInvestigation(investigation) {
  if (!investigation) return `<section class="investigation-section" aria-labelledby="investigation-heading"><div class="section-heading"><p class="eyebrow">Discover</p><h2 id="investigation-heading">AI investigation</h2></div><div class="investigation-unavailable" role="status"><strong>Investigation data unavailable</strong><p>The current backend does not provide an investigation trace for this analysis.</p></div></section>`;
  const summary = `<ul class="investigation-summary">${detail("Investigation ID", investigation.investigationId)}${detail("Experiment budget", investigation.experimentBudget)}${detail("Experiments executed", investigation.experimentsExecuted)}${detail("Termination", investigation.terminationReason)}</ul>`;
  const trace = investigation.trace === null ? '<p class="trace-muted">Trace data unavailable.</p>' : investigation.trace.length === 0 ? '<p class="trace-muted">Investigation completed with no trace entries.</p>' : `<div class="trace-list">${investigation.trace.map(renderTraceEntry).join("")}</div>`;
  return `<section class="investigation-section" aria-labelledby="investigation-heading"><div class="section-heading"><p class="eyebrow">Discover</p><h2 id="investigation-heading">AI investigation</h2><p>Action selection and measured engine results are presented separately.</p></div>${summary}${trace}</section>`;
}
function renderFinding(finding) {
  const parameters = parameterEntries(finding.condition?.parameters);
  const parameterHtml = parameters.length ? `<dl class="trace-parameters">${parameters.map(([key, value]) => `<div><dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd></div>`).join("")}</dl>` : '<p class="trace-muted">No parameters supplied.</p>';
  return `<article class="finding-record"><div class="finding-heading"><div><p class="eyebrow">Verified finding</p><h3>${escapeHtml(displayValue(finding.condition?.type, "Condition unavailable"))}</h3></div><span class="finding-status">Deterministically verified</span></div>${parameterHtml}<section class="finding-measurement"><p class="eyebrow">Measured result</p><ul>${detail("Metric", finding.metric?.name)}${detail("Baseline", formatScore(finding.metric?.baselineScore))}${detail("Candidate", formatScore(finding.metric?.candidateScore))}${detail("Backend-measured delta", formatScore(finding.metric?.delta))}${detail("Threshold", formatScore(finding.threshold))}</ul></section><section class="finding-verification"><p class="eyebrow">Verification</p><ul>${detail("Status", "Deterministically verified")}${detail("Runs", finding.verification?.runs)}${detail("Successful reproductions", finding.verification?.successfulReproductions)}${detail("Seed", finding.seed)}</ul></section><section class="finding-metadata"><p>${escapeHtml(`Fingerprint: ${displayValue(finding.fingerprint)}`)}</p><p>${escapeHtml(`Severity: ${displayValue(finding.severity)}`)}</p></section></article>`;
}
function renderFindings(findings) {
  const heading = `<div class="section-heading"><p class="eyebrow">Verify</p><h2 id="findings-heading">Verified findings</h2><p>Deterministic evaluation and reproduction evidence for the current analysis.</p></div>`;
  if (findings.state === FINDING_STATES.NONE) return `<section class="findings-section" aria-labelledby="findings-heading">${heading}<div class="findings-empty" role="status"><strong>No verified findings.</strong><p>The backend did not report a deterministically verified current failure.</p></div></section>`;
  if (findings.state === FINDING_STATES.UNAVAILABLE) return `<section class="findings-section" aria-labelledby="findings-heading">${heading}<div class="findings-empty" role="status"><strong>Finding evidence unavailable.</strong><p>The analysis response did not include enough verification evidence to present a finding.</p></div></section>`;
  return `<section class="findings-section" aria-labelledby="findings-heading">${heading}<div class="findings-list">${findings.items.map(renderFinding).join("")}</div></section>`;
}
function renderReplay(replay) {
  const outcome = replayOutcomePresentation(replay.outcome), condition = replay.historicalCondition, metric = replay.currentEvaluation?.metric;
  const parameters = parameterEntries(condition?.parameters);
  const parameterHtml = parameters.length ? `<dl class="trace-parameters">${parameters.map(([key, value]) => `<div><dt>${escapeHtml(key)}</dt><dd>${escapeHtml(value)}</dd></div>`).join("")}</dl>` : '<p class="trace-muted">No historical parameters supplied.</p>';
  const currentEvidence = replay.currentEvaluation ? `<section class="replay-current"><p class="eyebrow">Current replay evidence</p><ul>${detail("Metric", metric?.name)}${detail("Production / baseline", formatScore(metric?.baselineScore))}${detail("Candidate", formatScore(metric?.candidateScore))}${detail("Backend-measured delta", formatScore(metric?.delta))}${detail("Measured status", replay.currentEvaluation.status)}</ul></section>` : '<section class="replay-current"><p class="eyebrow">Current replay evidence</p><p class="trace-muted">No current evaluation was supplied for this replay.</p></section>';
  return `<article class="replay-record"><div class="replay-heading"><div><p class="eyebrow">Historical weakness</p><h3>${escapeHtml(displayValue(condition?.type, "Historical condition unavailable"))}</h3></div><span class="replay-outcome">${escapeHtml(outcome.label)}</span></div><p class="replay-context">Fingerprint: <span class="mono">${escapeHtml(displayValue(replay.fingerprint))}</span></p>${parameterHtml}${currentEvidence}<section class="replay-result"><p class="eyebrow">Current replay result</p><strong>${escapeHtml(outcome.label)}</strong><p>${escapeHtml(outcome.explanation)}</p>${replay.reason ? `<p><strong>Reason:</strong> ${escapeHtml(replay.reason)}</p>` : ""}</section></article>`;
}
function renderReplaySurface(replays) {
  const heading = `<div class="section-heading"><p class="eyebrow">Remember → prevent</p><h2 id="replays-heading">Historical regression replay</h2><p>Historical weakness context is separate from current candidate replay evidence.</p></div>`;
  const replayBody = replays === null ? '<div class="replay-empty" role="status"><strong>Historical replay data unavailable.</strong><p>The analysis response did not include replay records.</p></div>' : replays.length === 0 ? '<div class="replay-empty" role="status"><strong>No historical regressions to replay.</strong><p>The backend returned no replay records for this analysis.</p></div>' : `<div class="replay-list">${replays.map(renderReplay).join("")}</div>`;
  return `<section class="replay-section" aria-labelledby="replays-heading">${heading}${replayBody}<section class="memory-unavailable" aria-labelledby="memory-heading"><p class="eyebrow">Failure Memory</p><h3 id="memory-heading">Verified weaknesses become reusable regression tests.</h3><p>Failure Memory records are not available from the current API.</p></section></section>`;
}
function renderReleaseDecision(analysis) {
  const decision = releaseDecisionPresentation(analysis.release), summary = analysisSummary(analysis);
  const certificate = `<section class="analysis-summary" aria-labelledby="summary-heading"><div><p class="eyebrow">Analysis summary</p><h3 id="summary-heading">Release context</h3></div><ul>${detail("Analysis ID", summary.analysisId)}${detail("Production", summary.production)}${detail("Candidate", summary.candidate)}${detail("Dataset", summary.dataset)}${detail("Metric", summary.metric)}${detail("Investigation ID", summary.investigationId)}${detail("Experiments executed", summary.experimentsExecuted)}${detail("Verified findings", summary.verifiedFindings)}${detail("Historical replay records", summary.replayRecords)}</ul><p>Decision issued from ModelShield evaluation results.</p></section>`;
  if (!decision) return `<section class="decision-section" aria-labelledby="decision-heading"><div class="section-heading"><p class="eyebrow">Prevent</p><h2 id="decision-heading">Release decision</h2></div><div class="decision-unavailable" role="status"><strong>Release decision unavailable.</strong><p>The analysis response did not include an authoritative release decision.</p></div>${certificate}</section>`;
  const evidence = decision.findings === null ? '<p class="trace-muted">Decision evidence references unavailable.</p>' : decision.findings.length === 0 ? '<p class="trace-muted">No decision evidence references supplied.</p>' : `<ul class="decision-evidence">${decision.findings.map((finding) => `<li><span class="mono">${escapeHtml(displayValue(finding.fingerprint))}</span><span>${escapeHtml(displayValue(finding.status))}</span><span>${escapeHtml(displayValue(finding.severity))}</span></li>`).join("")}</ul>`;
  return `<section class="decision-section" aria-labelledby="decision-heading"><div class="section-heading"><p class="eyebrow">Prevent</p><h2 id="decision-heading">Release decision</h2><p>Authoritative backend release outcome for this analysis.</p></div><article class="decision-record"><div class="decision-heading"><span>Backend verdict</span><strong>${escapeHtml(decision.verdict)}</strong></div><p class="decision-reason">${escapeHtml(displayValue(decision.rationale, "Decision reason unavailable."))}</p><section class="decision-evidence-section"><p class="eyebrow">Evidence references</p>${evidence}</section></article>${certificate}</section>`;
}
function renderAnalysis(analysis) {
  const overview = releaseOverview(analysis), comparison = measuredComparison(analysis);
  main().innerHTML = `
    <section class="page-intro" aria-labelledby="release-overview-heading"><p class="eyebrow">Release</p><h1 id="release-overview-heading">Release overview</h1><p>Identify the release and the deterministic evidence currently being viewed.</p></section>
    ${analysis.isPartial ? '<div class="partial-notice" role="status">Some optional analysis information is unavailable.</div>' : ""}
    <section class="release-overview" aria-label="Release overview details">
      ${renderModelCard("Production / baseline", overview.production)}
      ${renderModelCard("Candidate", overview.candidate)}
      <article class="release-entity"><p class="eyebrow">Dataset</p><h3>${escapeHtml(displayValue(overview.dataset?.type, "Dataset information unavailable"))}</h3><ul class="metadata-list">${detail("Split", overview.dataset?.split)}${detail("Task", overview.dataset?.task)}${detail("Sample count", overview.dataset?.sampleCount)}</ul></article>
      <article class="release-entity"><p class="eyebrow">Analysis</p><h3 class="mono">${escapeHtml(displayValue(overview.analysisId, "Analysis information unavailable"))}</h3><ul class="metadata-list">${detail("Experiment ID", overview.experimentId)}${detail("Current state", overview.state)}${detail("Condition", overview.condition)}</ul></article>
    </section>
    <section class="comparison-section" aria-labelledby="comparison-heading"><div class="section-heading"><p class="eyebrow">Measured comparison</p><h2 id="comparison-heading">Production versus candidate</h2><p>These are measured values for the current condition. They do not determine release safety.</p></div>
      <div class="comparison-grid">
        <article class="comparison-value"><span>Metric</span><strong>${escapeHtml(displayValue(comparison.metricName, "Metric unavailable"))}</strong></article>
        <article class="comparison-value"><span>Production / baseline</span><strong>${formatScore(comparison.baselineScore)}</strong></article>
        <article class="comparison-value"><span>Candidate</span><strong>${formatScore(comparison.candidateScore)}</strong></article>
        <article class="comparison-value"><span>Backend-measured delta</span><strong>${formatScore(comparison.delta)}</strong></article>
      </div>
      <p class="comparison-footnote">Measured evaluation status: <strong>${escapeHtml(displayValue(comparison.measuredStatus))}</strong>. Release safety is determined by later verified evidence and the backend release decision.</p>
    </section>${renderInvestigation(analysis.investigation)}${renderFindings(analysis.findings)}${renderReplaySurface(analysis.replays)}${renderReleaseDecision(analysis)}`;
}
function syncChrome() {
  const analysis = dashboardStore.analysis, candidate = analysis?.candidate, baseline = analysis?.baseline;
  document.getElementById("crumb-candidate").textContent = candidate?.name || "no analysis";
  document.getElementById("sb-model").textContent = candidate ? modelLabel(candidate) : "unavailable";
  document.getElementById("sb-reg-count").textContent = analysis?.replays === null || !analysis ? "unavailable" : `${analysis.replays.length} replayed`;
  document.getElementById("sb-policy").textContent = analysis?.release?.verdict || "unavailable";
  document.getElementById("model-select").textContent = candidate ? modelLabel(candidate) : "No analysis loaded";
  document.getElementById("baseline-select").textContent = baseline ? modelLabel(baseline) : "No analysis loaded";
}
function render() { syncChrome(); if (dashboardStore.status === ANALYSIS_STATES.LOADING) return renderState("Analysis running", "ModelShield is waiting for the backend analysis response.", "loading"); if (dashboardStore.status === ANALYSIS_STATES.INITIAL || dashboardStore.status === ANALYSIS_STATES.EMPTY) return renderState("No analysis has been run yet", "Run an analysis through the ModelShield API to view real release evidence.", "empty"); if (dashboardStore.status === ANALYSIS_STATES.ERROR) return renderState("Analysis data is unavailable", dashboardStore.error?.message || "Unable to load latest analysis.", "error"); return renderAnalysis(dashboardStore.analysis); }
async function loadLatest() { dashboardStore.setLoading(); render(); try { dashboardStore.setAnalysis(normalizeAnalysis(await modelShieldApi.getLatestAnalysis())); } catch (error) { if (error instanceof ApiError && error.status === 404) dashboardStore.setEmpty(); else dashboardStore.setError(error); } render(); }
document.addEventListener("DOMContentLoaded", () => { document.getElementById("btn-load-latest")?.addEventListener("click", loadLatest); render(); loadLatest(); });
