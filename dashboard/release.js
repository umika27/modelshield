export function releaseDecisionPresentation(release) {
  if (!release || !release.verdict) return null;
  return { verdict: release.verdict, rationale: release.rationale ?? null, findings: Array.isArray(release.findings) ? release.findings.map((finding) => ({ fingerprint: typeof finding?.failure_fingerprint === "string" ? finding.failure_fingerprint : null, status: typeof finding?.status === "string" ? finding.status : null, severity: typeof finding?.severity === "string" ? finding.severity : null })) : null };
}

export function analysisSummary(analysis) {
  if (!analysis) return null;
  return { analysisId: analysis.analysisId ?? null, production: analysis.baseline ? [analysis.baseline.name, analysis.baseline.version].filter(Boolean).join(" ") || null : null, candidate: analysis.candidate ? [analysis.candidate.name, analysis.candidate.version].filter(Boolean).join(" ") || null : null, dataset: analysis.dataset?.type ?? null, metric: analysis.metric?.name ?? null, investigationId: analysis.investigation?.investigationId ?? null, experimentsExecuted: analysis.investigation?.experimentsExecuted ?? null, verifiedFindings: analysis.findings?.state === "VERIFIED" ? analysis.findings.items.length : null, replayRecords: Array.isArray(analysis.replays) ? analysis.replays.length : null, decision: releaseDecisionPresentation(analysis.release) };
}
