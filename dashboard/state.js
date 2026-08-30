/** Production-only dashboard state. Backend evidence is never synthesized here. */
export const ANALYSIS_STATES = Object.freeze({ INITIAL: "INITIAL", LOADING: "LOADING", SUCCESS: "SUCCESS", EMPTY: "EMPTY", ERROR: "ERROR", PARTIAL: "PARTIAL" });

export class DashboardStore {
  constructor() { this.status = ANALYSIS_STATES.INITIAL; this.analysis = null; this.error = null; }
  setLoading() { this.status = ANALYSIS_STATES.LOADING; this.error = null; }
  setAnalysis(analysis) { this.analysis = analysis; this.error = null; this.status = analysis ? (analysis.isPartial ? ANALYSIS_STATES.PARTIAL : ANALYSIS_STATES.SUCCESS) : ANALYSIS_STATES.EMPTY; }
  setEmpty() { this.analysis = null; this.error = null; this.status = ANALYSIS_STATES.EMPTY; }
  setError(error) { this.analysis = null; this.error = error instanceof Error ? error : new Error("Analysis data is unavailable."); this.status = ANALYSIS_STATES.ERROR; }
}
export const dashboardStore = new DashboardStore();
