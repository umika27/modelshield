const objectOrNull = (value) => value && typeof value === "object" && !Array.isArray(value) ? value : null;
const finiteOrNull = (value) => typeof value === "number" && Number.isFinite(value) ? value : null;
const stringOrNull = (value) => typeof value === "string" && value.trim() ? value : null;
function evaluation(raw) {
  const value = objectOrNull(raw), metric = objectOrNull(value?.metric);
  if (!value) return null;
  return { status: stringOrNull(value.status), baseline: objectOrNull(value.baseline), candidate: objectOrNull(value.candidate), metric: metric ? { name: stringOrNull(metric.name), baselineScore: finiteOrNull(metric.baseline_score), candidateScore: finiteOrNull(metric.candidate_score), delta: finiteOrNull(metric.delta) } : null };
}
export function normalizeHistoricalReplays(raw) {
  if (!Array.isArray(raw)) return null;
  return raw.map((replay) => ({ fingerprint: stringOrNull(replay?.fingerprint), sourceFailureId: finiteOrNull(replay?.source_failure_id), historicalCondition: objectOrNull(replay?.condition), currentEvaluation: evaluation(replay?.evaluation), outcome: stringOrNull(replay?.outcome), reason: stringOrNull(replay?.reason) }));
}
export function replayOutcomePresentation(outcome) {
  if (outcome === "PASS") return { label: "PASS", explanation: "Current replay passed." };
  if (outcome === "FAIL") return { label: "FAIL", explanation: "Historical regression reproduced in the current replay." };
  if (outcome === "SKIPPED") return { label: "SKIPPED", explanation: "Replay was not executed." };
  return { label: "UNAVAILABLE", explanation: "Replay outcome unavailable." };
}
