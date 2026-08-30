/**
 * ModelShield Unified Dashboard Mock State Layer (Phase 2 & 3)
 * Primary Source of Truth derived strictly from docs/contracts/ and examples/
 */

// Authoritative Baseline Model
export const BASELINE_MODEL = {
  name: "production-v1",
  version: "v1",
  framework: "pytorch",
  task: "image_classification",
  scores: {
    low_light_blur: 0.82,
    motion_blur: 0.88,
    contrast_drop: 0.79,
    color_jitter: 0.85,
    gaussian_noise: 0.84,
  }
};

// Candidate Models with realistic, internally consistent performance profiles
export const CANDIDATE_PROFILES = {
  "candidate-v2": {
    name: "candidate-v2",
    version: "v2",
    role: "exploration",
    artifact_reference: "models/candidate-v2",
    scores: {
      low_light_blur: 0.49,  // Severe drop (-0.33) -> failure-147
      motion_blur: 0.61,     // Severe drop (-0.27) -> failure-152
      contrast_drop: 0.58,   // Severe drop (-0.21) -> failure-158
      color_jitter: 0.77,    // Drop (-0.08) -> failure-163
      gaussian_noise: 0.62,  // Severe drop (-0.22) -> failure-171
    }
  },
  "candidate-v3": {
    name: "candidate-v3",
    version: "v3",
    role: "release_candidate",
    artifact_reference: "models/candidate-v3",
    scores: {
      low_light_blur: 0.49,  // < 0.65 threshold -> FAILS regression-147 [BLOCK]
      motion_blur: 0.78,     // >= 0.70 threshold -> PASSES regression-152
      contrast_drop: 0.72,   // >= 0.63 threshold -> PASSES regression-158
      color_jitter: 0.66,    // in [0.63, 0.68) margin -> REVIEW regression-163 [WARN]
      gaussian_noise: 0.75,  // >= 0.67 threshold -> PASSES regression-171
    }
  },
  "candidate-v4": {
    name: "candidate-v4",
    version: "v4",
    role: "patched_release",
    artifact_reference: "models/candidate-v4",
    scores: {
      low_light_blur: 0.85,  // >= 0.65 threshold -> PASSES regression-147
      motion_blur: 0.82,     // >= 0.70 threshold -> PASSES regression-152
      contrast_drop: 0.78,   // >= 0.63 threshold -> PASSES regression-158
      color_jitter: 0.80,    // >= 0.68 threshold -> PASSES regression-163
      gaussian_noise: 0.81,  // >= 0.67 threshold -> PASSES regression-171
    }
  }
};

// Verified Failure Records (docs/contracts/failure_record.json)
export const FAILURE_RECORDS = [
  {
    schema_version: "1.0",
    failure_id: "failure-147",
    evaluation_id: "eval-001",
    experiment_id: "exp-001",
    model: { name: "candidate-v2", version: "v2", artifact_reference: "models/candidate-v2" },
    condition: { type: "low_light_blur", parameters: { brightness: 0.3, blur: 0.7 } },
    metric: { name: "accuracy", baseline_score: 0.82, candidate_score: 0.49, delta: -0.33 },
    severity: "critical",
    verification: { status: "verified", verification_runs: 2, consistent: true },
    reproducibility_capsule_id: "capsule-147",
    dataset: { name: "demo-dataset", version: "v1", reference: "data/demo-dataset" },
    created_at: "2026-08-29T10:05:00Z"
  },
  {
    schema_version: "1.0",
    failure_id: "failure-152",
    evaluation_id: "eval-002",
    experiment_id: "exp-001",
    model: { name: "candidate-v2", version: "v2", artifact_reference: "models/candidate-v2" },
    condition: { type: "motion_blur", parameters: { angle: 45, kernel_size: 9 } },
    metric: { name: "accuracy", baseline_score: 0.88, candidate_score: 0.61, delta: -0.27 },
    severity: "critical",
    verification: { status: "verified", verification_runs: 3, consistent: true },
    reproducibility_capsule_id: "capsule-152",
    dataset: { name: "demo-dataset", version: "v1", reference: "data/demo-dataset" },
    created_at: "2026-08-29T10:12:00Z"
  },
  {
    schema_version: "1.0",
    failure_id: "failure-158",
    evaluation_id: "eval-003",
    experiment_id: "exp-002",
    model: { name: "candidate-v2", version: "v2", artifact_reference: "models/candidate-v2" },
    condition: { type: "contrast_drop", parameters: { contrast_factor: 0.25 } },
    metric: { name: "f1_score", baseline_score: 0.79, candidate_score: 0.58, delta: -0.21 },
    severity: "high",
    verification: { status: "verified", verification_runs: 2, consistent: true },
    reproducibility_capsule_id: "capsule-158",
    dataset: { name: "demo-dataset", version: "v1", reference: "data/demo-dataset" },
    created_at: "2026-08-29T10:20:00Z"
  },
  {
    schema_version: "1.0",
    failure_id: "failure-163",
    evaluation_id: "eval-004",
    experiment_id: "exp-002",
    model: { name: "candidate-v2", version: "v2", artifact_reference: "models/candidate-v2" },
    condition: { type: "color_jitter", parameters: { hue: 0.4, saturation: 0.5 } },
    metric: { name: "accuracy", baseline_score: 0.85, candidate_score: 0.77, delta: -0.08 },
    severity: "medium",
    verification: { status: "verified", verification_runs: 2, consistent: true },
    reproducibility_capsule_id: "capsule-163",
    dataset: { name: "demo-dataset", version: "v1", reference: "data/demo-dataset" },
    created_at: "2026-08-29T10:30:00Z"
  },
  {
    schema_version: "1.0",
    failure_id: "failure-171",
    evaluation_id: "eval-005",
    experiment_id: "exp-003",
    model: { name: "candidate-v2", version: "v2", artifact_reference: "models/candidate-v2" },
    condition: { type: "gaussian_noise", parameters: { mean: 0.0, var: 0.05 } },
    metric: { name: "accuracy", baseline_score: 0.84, candidate_score: 0.62, delta: -0.22 },
    severity: "high",
    verification: { status: "verified", verification_runs: 2, consistent: true },
    reproducibility_capsule_id: "capsule-171",
    dataset: { name: "demo-dataset", version: "v1", reference: "data/demo-dataset" },
    created_at: "2026-08-29T10:45:00Z"
  }
];

// Reproducibility Capsules (docs/contracts/reproducibility_capsule.json)
export const REPRODUCIBILITY_CAPSULES = {
  "capsule-147": {
    schema_version: "1.0",
    capsule_id: "capsule-147",
    failure_id: "failure-147",
    model: { name: "candidate-v2", version: "v2", artifact_reference: "models/candidate-v2" },
    dataset: { name: "demo-dataset", version: "v1", reference: "data/demo-dataset" },
    preprocessing: { name: "standard-cv-preprocessing", version: "1.0" },
    challenge: { type: "low_light_blur", parameters: { brightness: 0.3, blur: 0.7 } },
    evaluation: { metric: "accuracy", batch_size: 32 },
    randomness: { seed: 42 },
    environment: { python: "3.11", framework: "pytorch" },
    results: { baseline_score: 0.82, candidate_score: 0.49, delta: -0.33 },
    created_at: "2026-08-29T10:05:00Z"
  },
  "capsule-152": {
    schema_version: "1.0",
    capsule_id: "capsule-152",
    failure_id: "failure-152",
    model: { name: "candidate-v2", version: "v2", artifact_reference: "models/candidate-v2" },
    dataset: { name: "demo-dataset", version: "v1", reference: "data/demo-dataset" },
    preprocessing: { name: "standard-cv-preprocessing", version: "1.0" },
    challenge: { type: "motion_blur", parameters: { angle: 45, kernel_size: 9 } },
    evaluation: { metric: "accuracy", batch_size: 32 },
    randomness: { seed: 42 },
    environment: { python: "3.11", framework: "pytorch" },
    results: { baseline_score: 0.88, candidate_score: 0.61, delta: -0.27 },
    created_at: "2026-08-29T10:12:00Z"
  },
  "capsule-158": {
    schema_version: "1.0",
    capsule_id: "capsule-158",
    failure_id: "failure-158",
    model: { name: "candidate-v2", version: "v2", artifact_reference: "models/candidate-v2" },
    dataset: { name: "demo-dataset", version: "v1", reference: "data/demo-dataset" },
    preprocessing: { name: "standard-cv-preprocessing", version: "1.0" },
    challenge: { type: "contrast_drop", parameters: { contrast_factor: 0.25 } },
    evaluation: { metric: "f1_score", batch_size: 32 },
    randomness: { seed: 42 },
    environment: { python: "3.11", framework: "pytorch" },
    results: { baseline_score: 0.79, candidate_score: 0.58, delta: -0.21 },
    created_at: "2026-08-29T10:20:00Z"
  },
  "capsule-163": {
    schema_version: "1.0",
    capsule_id: "capsule-163",
    failure_id: "failure-163",
    model: { name: "candidate-v2", version: "v2", artifact_reference: "models/candidate-v2" },
    dataset: { name: "demo-dataset", version: "v1", reference: "data/demo-dataset" },
    preprocessing: { name: "standard-cv-preprocessing", version: "1.0" },
    challenge: { type: "color_jitter", parameters: { hue: 0.4, saturation: 0.5 } },
    evaluation: { metric: "accuracy", batch_size: 32 },
    randomness: { seed: 42 },
    environment: { python: "3.11", framework: "pytorch" },
    results: { baseline_score: 0.85, candidate_score: 0.77, delta: -0.08 },
    created_at: "2026-08-29T10:30:00Z"
  },
  "capsule-171": {
    schema_version: "1.0",
    capsule_id: "capsule-171",
    failure_id: "failure-171",
    model: { name: "candidate-v2", version: "v2", artifact_reference: "models/candidate-v2" },
    dataset: { name: "demo-dataset", version: "v1", reference: "data/demo-dataset" },
    preprocessing: { name: "standard-cv-preprocessing", version: "1.0" },
    challenge: { type: "gaussian_noise", parameters: { mean: 0.0, var: 0.05 } },
    evaluation: { metric: "accuracy", batch_size: 32 },
    randomness: { seed: 42 },
    environment: { python: "3.11", framework: "pytorch" },
    results: { baseline_score: 0.84, candidate_score: 0.62, delta: -0.22 },
    created_at: "2026-08-29T10:45:00Z"
  }
};

// Active Regression Bank (docs/contracts/regression_record.json)
export const REGRESSION_BANK = [
  {
    schema_version: "1.0",
    regression_id: "regression-147",
    failure_id: "failure-147",
    name: "Low Light + Blur regression",
    condition: { type: "low_light_blur", parameters: { brightness: 0.3, blur: 0.7 } },
    metric: { name: "accuracy", minimum_threshold: 0.65, review_margin: 0.05 },
    policy: "block",
    enabled: true,
    created_at: "2026-08-29T10:10:00Z"
  },
  {
    schema_version: "1.0",
    regression_id: "regression-152",
    failure_id: "failure-152",
    name: "Motion Blur regression",
    condition: { type: "motion_blur", parameters: { angle: 45, kernel_size: 9 } },
    metric: { name: "accuracy", minimum_threshold: 0.70, review_margin: 0.05 },
    policy: "block",
    enabled: true,
    created_at: "2026-08-29T10:15:00Z"
  },
  {
    schema_version: "1.0",
    regression_id: "regression-158",
    failure_id: "failure-158",
    name: "Contrast Drop regression",
    condition: { type: "contrast_drop", parameters: { contrast_factor: 0.25 } },
    metric: { name: "f1_score", minimum_threshold: 0.63, review_margin: 0.05 },
    policy: "block",
    enabled: true,
    created_at: "2026-08-29T10:25:00Z"
  },
  {
    schema_version: "1.0",
    regression_id: "regression-163",
    failure_id: "failure-163",
    name: "Color Jitter regression",
    condition: { type: "color_jitter", parameters: { hue: 0.4, saturation: 0.5 } },
    metric: { name: "accuracy", minimum_threshold: 0.68, review_margin: 0.05 },
    policy: "warn",
    enabled: true,
    created_at: "2026-08-29T10:35:00Z"
  },
  {
    schema_version: "1.0",
    regression_id: "regression-171",
    failure_id: "failure-171",
    name: "Gaussian Noise regression",
    condition: { type: "gaussian_noise", parameters: { mean: 0.0, var: 0.05 } },
    metric: { name: "accuracy", minimum_threshold: 0.67, review_margin: 0.05 },
    policy: "block",
    enabled: true,
    created_at: "2026-08-29T10:50:00Z"
  }
];

// Single Unified Store State
class DashboardStateStore {
  constructor() {
    this.selectedCandidate = "candidate-v3";
    this.selectedFailureId = "failure-147";
    this.activeFailureTab = "overview";
    this.thresholdTolerance = -0.15;
    this.regressions = JSON.parse(JSON.stringify(REGRESSION_BANK));
    this.failures = JSON.parse(JSON.stringify(FAILURE_RECORDS));
    this.capsules = JSON.parse(JSON.stringify(REPRODUCIBILITY_CAPSULES));
  }

  getSelectedCandidate() {
    return this.selectedCandidate;
  }

  setSelectedCandidate(candidateName) {
    if (CANDIDATE_PROFILES[candidateName]) {
      this.selectedCandidate = candidateName;
    }
  }

  getSelectedFailureId() {
    return this.selectedFailureId;
  }

  setSelectedFailureId(failureId) {
    if (this.failures.some(f => f.failure_id === failureId)) {
      this.selectedFailureId = failureId;
    }
  }

  getActiveFailureTab() {
    return this.activeFailureTab;
  }

  setActiveFailureTab(tabKey) {
    this.activeFailureTab = tabKey;
  }

  // --------------------------------------------------------------------------
  // View 1: Model Comparison State
  // --------------------------------------------------------------------------
  getModelComparison(candidateName = this.selectedCandidate) {
    const candidate = CANDIDATE_PROFILES[candidateName] || CANDIDATE_PROFILES["candidate-v3"];
    return this.failures.map(f => {
      const condType = f.condition.type;
      const bScore = BASELINE_MODEL.scores[condType] || f.metric.baseline_score;
      const cScore = candidate.scores[condType] !== undefined ? candidate.scores[condType] : f.metric.candidate_score;
      const delta = cScore - bScore;
      const isFail = delta < this.thresholdTolerance;

      return {
        condition_type: condType,
        parameters: f.condition.parameters,
        baseline_score: bScore,
        candidate_score: cScore,
        delta: Math.round(delta * 10000) / 10000,
        is_failure: isFail,
        verdict: isFail ? "FAIL" : "PASS",
        metric_name: f.metric.name
      };
    });
  }

  // --------------------------------------------------------------------------
  // View 2: Failure Explorer State & Capsule Lookups
  // --------------------------------------------------------------------------
  getFailureRecords() {
    return this.failures;
  }

  getFailureById(failureId) {
    return this.failures.find(f => f.failure_id === failureId) || this.failures[0];
  }

  getFailureCapsule(failureId) {
    const failure = this.getFailureById(failureId);
    if (!failure) return null;
    const capsuleId = failure.reproducibility_capsule_id;
    return this.capsules[capsuleId] || null;
  }

  getLinkedRegression(failureId) {
    return this.regressions.find(r => r.failure_id === failureId) || null;
  }

  // Deterministic mock replay helper for Failure Explorer
  replayFailure(failureId, targetCandidateName = this.selectedCandidate) {
    const failure = this.getFailureById(failureId);
    const capsule = this.getFailureCapsule(failureId);
    const candidate = CANDIDATE_PROFILES[targetCandidateName] || CANDIDATE_PROFILES["candidate-v3"];
    const regression = this.getLinkedRegression(failureId);

    const condType = failure.condition.type;
    const observedScore = candidate.scores[condType] !== undefined ? candidate.scores[condType] : 0.50;
    const threshold = regression ? regression.metric.minimum_threshold : (failure.metric.baseline_score * 0.80);
    const isPassed = observedScore >= threshold;

    return {
      failure_id: failure.failure_id,
      capsule_id: capsule ? capsule.capsule_id : "n/a",
      condition_type: condType,
      parameters: failure.condition.parameters,
      seed: capsule ? capsule.randomness.seed : 42,
      candidate: candidate.name,
      observed_score: observedScore,
      minimum_threshold: threshold,
      is_passed: isPassed,
      status: isPassed ? "PASSED" : "FAILED",
      execution_trace: [
        `[1/4] Loaded model artifact: ${candidate.artifact_reference}`,
        `[2/4] Initialized deterministic challenge transform: ${condType} (seed=${capsule ? capsule.randomness.seed : 42})`,
        `[3/4] Applied transform on dataset: ${capsule ? capsule.dataset.reference : 'data/demo-dataset'}`,
        `[4/4] Evaluated ${failure.metric.name}: ${observedScore.toFixed(2)} (Threshold: ${threshold.toFixed(2)})`,
        isPassed ? `Result: ✓ PASSED (Candidate fixed the regression)` : `Result: ✖ FAILED (Regression reproduced on candidate)`
      ]
    };
  }

  // --------------------------------------------------------------------------
  // View 3: Failure Memory State
  // --------------------------------------------------------------------------
  getRegressionBank() {
    return this.regressions;
  }

  toggleRegression(regressionId) {
    const reg = this.regressions.find(r => r.regression_id === regressionId);
    if (reg) {
      reg.enabled = !reg.enabled;
      return reg.enabled;
    }
    return false;
  }

  // --------------------------------------------------------------------------
  // View 4: Regression Results State
  // --------------------------------------------------------------------------
  getRegressionResults(candidateName = this.selectedCandidate) {
    const candidate = CANDIDATE_PROFILES[candidateName] || CANDIDATE_PROFILES["candidate-v3"];

    return this.regressions.map(r => {
      const condType = r.condition.type;
      const observedScore = candidate.scores[condType] !== undefined ? candidate.scores[condType] : 0.50;
      const minThreshold = r.metric.minimum_threshold;
      const reviewMargin = r.metric.review_margin || 0.05;

      let status = "passed";
      let msg = `Observed score (${observedScore.toFixed(2)}) satisfied threshold (${minThreshold.toFixed(2)}).`;

      if (observedScore < minThreshold - reviewMargin) {
        status = "failed";
        msg = `Observed score (${observedScore.toFixed(2)}) failed minimum threshold (${minThreshold.toFixed(2)}).`;
      } else if (observedScore < minThreshold) {
        status = "review_required";
        msg = `Observed score (${observedScore.toFixed(2)}) fell into review margin [${(minThreshold - reviewMargin).toFixed(2)}, ${minThreshold.toFixed(2)}].`;
      }

      return {
        regression_id: r.regression_id,
        failure_id: r.failure_id,
        name: r.name,
        condition_type: condType,
        parameters: r.condition.parameters,
        metric_name: r.metric.name,
        observed_score: observedScore,
        minimum_threshold: minThreshold,
        policy: r.policy,
        enabled: r.enabled,
        status: r.enabled ? status : "disabled",
        message: msg
      };
    });
  }

  // --------------------------------------------------------------------------
  // View 5: Release Gate State
  // --------------------------------------------------------------------------
  getReleaseDecision(candidateName = this.selectedCandidate) {
    if (this.liveDecision) {
      const decision = this.liveDecision;
      const checks = decision.findings.map((finding, index) => ({
        regression_id: `regression-${index + 1}`,
        failure_id: finding.failure_fingerprint,
        name: "Verified regression",
        condition_type: "live",
        parameters: {},
        metric_name: "accuracy",
        observed_score: finding.observed_score,
        minimum_threshold: finding.minimum_threshold,
        policy: finding.internal_policy,
        enabled: true,
        status: finding.status,
        message: "Derived from real ModelShield analysis."
      }));
      const failed = checks.filter(check => check.status === "failed").length;
      const review = checks.filter(check => check.status === "review_required").length;
      return {
        schema_version: "1.0", decision_id: decision.analysis_id || "live-analysis",
        model: decision.candidate, decision: decision.verdict.toLowerCase(),
        summary: { total_regressions: checks.length, passed: checks.filter(check => check.status === "passed").length, failed, review_required: review },
        failures: checks.filter(check => check.status !== "passed"), reason: decision.rationale,
        exit_code: decision.verdict === "BLOCK" ? 1 : (decision.verdict === "REVIEW" ? 2 : 0), detailed_checks: checks,
        timestamp: new Date().toISOString()
      };
    }
    const candidate = CANDIDATE_PROFILES[candidateName] || CANDIDATE_PROFILES["candidate-v3"];
    const checkResults = this.getRegressionResults(candidateName).filter(r => r.enabled);

    let passedCount = 0;
    let failedCount = 0;
    let reviewCount = 0;
    let hasBlockFailure = false;
    let hasReview = false;
    const failuresList = [];

    for (const chk of checkResults) {
      if (chk.status === "passed") {
        passedCount++;
      } else if (chk.status === "review_required") {
        reviewCount++;
        hasReview = true;
        failuresList.push({
          regression_id: chk.regression_id,
          failure_id: chk.failure_id,
          status: "review_required",
          policy: chk.policy
        });
      } else if (chk.status === "failed") {
        failedCount++;
        failuresList.push({
          regression_id: chk.regression_id,
          failure_id: chk.failure_id,
          status: "failed",
          policy: chk.policy
        });
        if (chk.policy === "block") {
          hasBlockFailure = true;
        } else {
          hasReview = true;
        }
      }
    }

    let decision = "pass";
    let reason = `All ${checkResults.length} active regression checks passed successfully.`;
    let exitCode = 0;

    if (hasBlockFailure) {
      decision = "block";
      reason = `Candidate failed ${failedCount} regression test(s) under policy 'block'.`;
      exitCode = 1;
    } else if (hasReview || reviewCount > 0) {
      decision = "review";
      reason = `Candidate requires review: ${reviewCount} review item(s), ${failedCount} warning item(s).`;
      exitCode = 2;
    }

    return {
      schema_version: "1.0",
      decision_id: `decision-${candidate.name}-${Date.now().toString().slice(-4)}`,
      model: {
        name: candidate.name,
        version: candidate.version,
        artifact_reference: candidate.artifact_reference
      },
      decision: decision,
      summary: {
        total_regressions: checkResults.length,
        passed: passedCount,
        failed: failedCount,
        review_required: reviewCount
      },
      failures: failuresList,
      reason: reason,
      exit_code: exitCode,
      detailed_checks: checkResults,
      timestamp: new Date().toISOString()
    };
  }
}

export const dashboardState = new DashboardStateStore();
