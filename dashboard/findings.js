const objectOrNull = (value) => value && typeof value === "object" && !Array.isArray(value) ? value : null;
const finiteOrNull = (value) => typeof value === "number" && Number.isFinite(value) ? value : null;
const stringOrNull = (value) => typeof value === "string" && value.trim() ? value : null;

export const FINDING_STATES = Object.freeze({ VERIFIED: "VERIFIED", NONE: "NONE", UNAVAILABLE: "UNAVAILABLE" });

export function normalizeVerifiedFindings(raw) {
  const value = objectOrNull(raw);
  if (!value) return { state: FINDING_STATES.UNAVAILABLE, items: [] };
  const verification = objectOrNull(value.verification), failure = objectOrNull(value.failure), metric = objectOrNull(value.metric), condition = objectOrNull(value.condition);
  if (!verification) return { state: FINDING_STATES.UNAVAILABLE, items: [] };
  if (verification.verified !== true) {
    if (verification.verified === false || verification.required === false) return { state: FINDING_STATES.NONE, items: [] };
    return { state: FINDING_STATES.UNAVAILABLE, items: [] };
  }
  return {
    state: FINDING_STATES.VERIFIED,
    items: [{ condition: condition ? { type: stringOrNull(condition.type), parameters: objectOrNull(condition.parameters) } : null, metric: metric ? { name: stringOrNull(metric.name), baselineScore: finiteOrNull(metric.baseline_score), candidateScore: finiteOrNull(metric.candidate_score), delta: finiteOrNull(metric.delta) } : null, threshold: finiteOrNull(value.threshold?.value ?? value.threshold), seed: finiteOrNull(value.reproducibility?.seed), verification: { required: typeof verification.required === "boolean" ? verification.required : null, verified: true, runs: finiteOrNull(verification.runs), successfulReproductions: finiteOrNull(verification.successful_reproductions) }, fingerprint: stringOrNull(failure?.fingerprint), severity: stringOrNull(failure?.severity) }],
  };
}
