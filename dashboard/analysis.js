import { normalizeInvestigation } from "./investigation.js";
import { normalizeVerifiedFindings } from "./findings.js";
import { normalizeHistoricalReplays } from "./replays.js";
import { releaseDecisionPresentation } from "./release.js";

const objectOrNull = (value) => value && typeof value === "object" && !Array.isArray(value) ? value : null;
const finiteOrNull = (value) => typeof value === "number" && Number.isFinite(value) ? value : null;
const stringOrNull = (value) => typeof value === "string" && value.trim() ? value : null;
const hasOwn = (value, key) => Object.prototype.hasOwnProperty.call(value ?? {}, key);
function model(raw) { const value = objectOrNull(raw); return value ? { id: stringOrNull(value.id ?? value.model_id), name: stringOrNull(value.name), version: stringOrNull(value.version), architecture: stringOrNull(value.architecture), framework: stringOrNull(value.framework), task: stringOrNull(value.task), score: finiteOrNull(value.score) } : null; }
export function normalizeAnalysis(raw) {
  const value = objectOrNull(raw); if (!value) return null;
  const metric = objectOrNull(value.metric), verification = objectOrNull(value.verification), failure = objectOrNull(value.failure), release = objectOrNull(value.release);
  const replays = normalizeHistoricalReplays(value.historical_replays);
  const requiredMissing = !stringOrNull(value.analysis_id) || !model(value.baseline) || !model(value.candidate) || !metric;
  const dataset = objectOrNull(value.dataset);
  const investigation = normalizeInvestigation(value.investigation);
  const findings = normalizeVerifiedFindings(value);
  return { analysisId: stringOrNull(value.analysis_id), experimentId: stringOrNull(value.experiment_id), baseline: model(value.baseline), candidate: model(value.candidate), dataset: dataset ? { type: stringOrNull(dataset.type ?? dataset.dataset_type), split: stringOrNull(dataset.split), task: stringOrNull(dataset.task), sampleCount: finiteOrNull(dataset.sample_count) } : null, condition: objectOrNull(value.condition), metric: metric ? { name: stringOrNull(metric.name), baselineScore: finiteOrNull(metric.baseline_score), candidateScore: finiteOrNull(metric.candidate_score), delta: finiteOrNull(metric.delta) } : null, status: stringOrNull(value.status), threshold: finiteOrNull(value.threshold?.value ?? value.threshold), verification: verification ? { required: typeof verification.required === "boolean" ? verification.required : null, verified: typeof verification.verified === "boolean" ? verification.verified : null, runs: finiteOrNull(verification.runs), successfulReproductions: finiteOrNull(verification.successful_reproductions) } : null, failure: failure ? { fingerprint: stringOrNull(failure.fingerprint), severity: stringOrNull(failure.severity) } : null, release: releaseDecisionPresentation(release ? { verdict: stringOrNull(release.verdict), rationale: stringOrNull(release.rationale), findings: Array.isArray(release.findings) ? release.findings : null } : null), replays, investigation, findings, isPartial: requiredMissing || !hasOwn(value, "historical_replays") || !release };
}
export const displayValue = (value, fallback = "Unavailable") => value === null || value === undefined || value === "" ? fallback : String(value);
export const formatScore = (value) => value === null || value === undefined ? "Unavailable" : `${(value * 100).toFixed(1)}%`;
export function releaseOverview(analysis) {
  return { production: analysis?.baseline ?? null, candidate: analysis?.candidate ?? null, dataset: analysis?.dataset ?? null, analysisId: analysis?.analysisId ?? null, experimentId: analysis?.experimentId ?? null, state: analysis?.status ?? null, condition: analysis?.condition?.type ?? null };
}
export function measuredComparison(analysis) {
  const metric = analysis?.metric ?? null;
  return { metricName: metric?.name ?? null, baselineScore: metric?.baselineScore ?? null, candidateScore: metric?.candidateScore ?? null, delta: metric?.delta ?? null, measuredStatus: analysis?.status ?? null, releaseVerdict: analysis?.release?.verdict ?? null };
}
