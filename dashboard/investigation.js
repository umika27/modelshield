const objectOrNull = (value) => value && typeof value === "object" && !Array.isArray(value) ? value : null;
const finiteOrNull = (value) => typeof value === "number" && Number.isFinite(value) ? value : null;
const stringOrNull = (value) => typeof value === "string" && value.trim() ? value : null;

function normalizeEvaluation(raw) {
  const value = objectOrNull(raw), metric = objectOrNull(value?.metric);
  if (!value) return null;
  return { status: stringOrNull(value.status), metric: metric ? { name: stringOrNull(metric.name), baselineScore: finiteOrNull(metric.baseline_score), candidateScore: finiteOrNull(metric.candidate_score), delta: finiteOrNull(metric.delta) } : null };
}
function normalizeAction(raw) {
  const value = objectOrNull(raw), challenge = objectOrNull(value?.challenge);
  if (!value) return null;
  return { rationale: stringOrNull(value.rationale), challenge: challenge ? { challengeId: stringOrNull(challenge.challenge_id), type: stringOrNull(challenge.type), parameters: objectOrNull(challenge.parameters), parentChallengeId: stringOrNull(challenge.parent_challenge_id), source: stringOrNull(challenge.source), reason: stringOrNull(challenge.reason), reproducible: typeof challenge.reproducible === "boolean" ? challenge.reproducible : null, seed: finiteOrNull(challenge.seed) } : null };
}

export function normalizeInvestigation(raw) {
  const value = objectOrNull(raw);
  if (!value) return null;
  const trace = Array.isArray(value.trace) ? value.trace.map((entry, index) => ({ order: index + 1, state: stringOrNull(entry?.state), action: normalizeAction(entry?.action), evaluation: normalizeEvaluation(entry?.evaluation), reason: stringOrNull(entry?.reason) })) : null;
  return { investigationId: stringOrNull(value.investigation_id), initialAction: normalizeAction(value.initial_action), trace, evaluations: Array.isArray(value.evaluations) ? value.evaluations.map(normalizeEvaluation) : null, experimentBudget: finiteOrNull(value.experiment_budget), experimentsExecuted: finiteOrNull(value.experiments_executed), terminationReason: stringOrNull(value.termination_reason), baseline: objectOrNull(value.baseline), candidate: objectOrNull(value.candidate) };
}
export function sourceLabel(source) {
  if (source === "ai_investigation") return "AI-selected experiment";
  if (source === "adaptive_investigation") return "Deterministic investigation fallback";
  return source ? `Experiment source: ${source}` : "Experiment source unavailable";
}
export function tracePresentation(entry) {
  const state = entry?.state?.toUpperCase() || "STATE UNAVAILABLE";
  return { state, source: sourceLabel(entry?.action?.challenge?.source), isAiSelected: entry?.action?.challenge?.source === "ai_investigation", title: entry?.action?.challenge?.type || "Challenge unavailable", hasMeasurement: entry?.state === "executed" && Boolean(entry?.evaluation), reason: entry?.reason ?? null, rationale: entry?.action?.rationale ?? null };
}
export function parameterEntries(parameters) {
  if (!parameters || Object.keys(parameters).length === 0) return [];
  return Object.entries(parameters).map(([key, value]) => [key, typeof value === "object" ? JSON.stringify(value) : String(value)]);
}
