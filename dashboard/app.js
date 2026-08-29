/**
 * ModelShield Developer Dashboard Application Logic (Phase 3 Refinement)
 * VS Code / GitHub Actions style workbench with Theme Switcher, Remix Icons,
 * Secondary Config Toolbar, Split Terminal Dock, and Unified Mock State.
 */

import { dashboardState } from "./state.js";
import { createStatusBadge } from "./components/badge.js";
import { createDataTable } from "./components/table.js";
import { createTerminalOutput } from "./components/terminal.js";
import { createCodeInspector } from "./components/inspector.js";
import { createDiffBar } from "./components/diffbar.js";

// UI Controller State
let currentView = "comparison";
let currentDockTab = "terminal";
let isDockMinimized = false;
let isDockMaximized = false;
let latestReplayResult = null;

document.addEventListener("DOMContentLoaded", () => {
  initTheme();
  setupNavigation();
  setupToolbarControls();
  setupBottomDock();
  syncAllUI();
});

// ----------------------------------------------------------------------------
// Theme Switching & Persistence
// ----------------------------------------------------------------------------
function initTheme() {
  const savedTheme = localStorage.getItem("modelshield-theme") || "dark";
  applyTheme(savedTheme);

  const btnDark = document.getElementById("btn-theme-dark");
  const btnLight = document.getElementById("btn-theme-light");

  if (btnDark) {
    btnDark.addEventListener("click", () => applyTheme("dark"));
  }
  if (btnLight) {
    btnLight.addEventListener("click", () => applyTheme("light"));
  }
}

function applyTheme(theme) {
  document.body.setAttribute("data-theme", theme);
  localStorage.setItem("modelshield-theme", theme);

  const btnDark = document.getElementById("btn-theme-dark");
  const btnLight = document.getElementById("btn-theme-light");

  if (btnDark && btnLight) {
    btnDark.classList.toggle("active", theme === "dark");
    btnLight.classList.toggle("active", theme === "light");
  }
}

// ----------------------------------------------------------------------------
// Navigation & Toolbar Controls
// ----------------------------------------------------------------------------
function setupNavigation() {
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(item => {
    item.addEventListener("click", () => {
      navItems.forEach(n => n.classList.remove("active"));
      item.classList.add("active");
      currentView = item.getAttribute("data-view");
      updateBreadcrumbs();
      renderCurrentView();
    });
  });
}

function setupToolbarControls() {
  const candidateSelect = document.getElementById("model-select");
  if (candidateSelect) {
    candidateSelect.addEventListener("change", (e) => {
      dashboardState.setSelectedCandidate(e.target.value);
      syncAllUI();
    });
  }

  const btnRefresh = document.getElementById("btn-refresh-state");
  if (btnRefresh) {
    btnRefresh.addEventListener("click", () => {
      syncAllUI();
    });
  }

  const btnRunGate = document.getElementById("btn-run-gate");
  if (btnRunGate) {
    btnRunGate.addEventListener("click", runReleaseGateWorkflow);
  }
}

function setupBottomDock() {
  const dockTabs = document.querySelectorAll(".dock-tab");
  dockTabs.forEach(tab => {
    tab.addEventListener("click", () => {
      dockTabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      currentDockTab = tab.getAttribute("data-dock");
      renderDockContent();
    });
  });

  const btnToggle = document.getElementById("btn-toggle-dock");
  const btnMax = document.getElementById("btn-max-dock");
  const btnClear = document.getElementById("btn-clear-terminal");
  const dock = document.getElementById("bottom-dock");
  const icon = document.getElementById("dock-toggle-icon");
  const maxIcon = document.getElementById("dock-max-icon");

  if (btnToggle && dock) {
    btnToggle.addEventListener("click", () => {
      isDockMinimized = !isDockMinimized;
      dock.classList.toggle("minimized", isDockMinimized);
      if (icon) {
        icon.className = isDockMinimized ? "ri-arrow-up-s-line" : "ri-arrow-down-s-line";
      }
    });
  }

  if (btnMax && dock) {
    btnMax.addEventListener("click", () => {
      isDockMaximized = !isDockMaximized;
      dock.classList.toggle("maximized", isDockMaximized);
      if (maxIcon) {
        maxIcon.className = isDockMaximized ? "ri-fullscreen-exit-line" : "ri-fullscreen-line";
      }
    });
  }

  if (btnClear) {
    btnClear.addEventListener("click", () => {
      const dockContent = document.getElementById("dock-content");
      if (dockContent) {
        dockContent.innerHTML = `<div class="term-prompt"><span class="term-user">modelshield@devbox</span>:<span class="term-dir">~/modelshield</span>$ <span class="term-cursor">▋</span></div>`;
      }
    });
  }
}

function syncAllUI() {
  updateBreadcrumbs();
  updateStatusBar();
  renderDockContent();
  renderCurrentView();
}

function updateBreadcrumbs() {
  const candidate = dashboardState.getSelectedCandidate();
  const crumbCandidate = document.getElementById("crumb-candidate");
  const crumbView = document.getElementById("crumb-view");
  if (crumbCandidate) crumbCandidate.textContent = candidate;
  if (crumbView) {
    if (currentView === "explorer") {
      const selectedId = dashboardState.getSelectedFailureId();
      crumbView.textContent = `failure-explorer / ${selectedId}`;
    } else {
      const viewNames = {
        comparison: "model-comparison",
        explorer: "failure-explorer",
        memory: "failure-memory",
        results: "regression-results",
        gate: "release-gate",
        pipelines: "pipelines",
        checks: "checks",
        artifacts: "artifacts",
        reports: "reports",
        settings: "settings",
        integrations: "integrations",
        audit: "audit-log"
      };
      crumbView.textContent = viewNames[currentView] || currentView;
    }
  }
}

function updateStatusBar() {
  const candidate = dashboardState.getSelectedCandidate();
  const decision = dashboardState.getReleaseDecision(candidate);
  const regressions = dashboardState.getRegressionBank();

  const sbModel = document.getElementById("sb-model");
  const sbRegCount = document.getElementById("sb-reg-count");
  const sbExit = document.getElementById("sb-exit");

  if (sbModel) sbModel.textContent = `${candidate}:${candidate.slice(-2)}`;
  if (sbRegCount) sbRegCount.textContent = `${regressions.filter(r => r.enabled).length} active`;
  if (sbExit) {
    if (decision.decision === "block") {
      sbExit.textContent = "1 (BLOCKED)";
      sbExit.style.color = "var(--status-block)";
    } else if (decision.decision === "review") {
      sbExit.textContent = "2 (REVIEW)";
      sbExit.style.color = "var(--status-review)";
    } else {
      sbExit.textContent = "0 (PASSED)";
      sbExit.style.color = "var(--status-pass)";
    }
  }
}

function renderCurrentView() {
  const container = document.getElementById("view-content");
  if (!container) return;

  switch (currentView) {
    case "comparison":
      renderModelComparison(container);
      break;
    case "explorer":
      renderFailureExplorer(container);
      break;
    case "memory":
      renderFailureMemory(container);
      break;
    case "results":
      renderRegressionResults(container);
      break;
    case "gate":
      renderReleaseGate(container);
      break;
    default:
      renderPlaceholderView(container, currentView);
      break;
  }
}

function renderPlaceholderView(container, viewKey) {
  const title = viewKey.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
  container.innerHTML = `
    <div class="placeholder-view">
      <i class="ri-terminal-window-line placeholder-icon"></i>
      <div class="placeholder-title">${title} Workspace</div>
      <div class="placeholder-subtitle">Select a verification view from the sidebar to analyze model regressions.</div>
    </div>
  `;
}

// ----------------------------------------------------------------------------
// VIEW 1: Model Comparison
// ----------------------------------------------------------------------------
function renderModelComparison(container) {
  const candidate = dashboardState.getSelectedCandidate();
  const comparisonData = dashboardState.getModelComparison(candidate);

  const headers = ["Condition Type", "Parameters", "Baseline Score", "Candidate Score", "Degradation Delta", "Verdict"];
  const rows = comparisonData.map(item => {
    const params = Object.entries(item.parameters || {}).map(([k, v]) => `${k}=${v}`).join(", ");
    return [
      `<strong class="mono">${item.condition_type}</strong>`,
      `<span class="mono" style="color: var(--text-muted);">${params || "default"}</span>`,
      `<span class="mono">${item.baseline_score.toFixed(2)}</span>`,
      `<span class="mono">${item.candidate_score.toFixed(2)}</span>`,
      createDiffBar(item.delta, -0.15),
      createStatusBadge(item.verdict)
    ];
  });

  container.innerHTML = `
    <div class="view-header">
      <div class="view-title"><i class="ri-git-compare-line"></i> Model Comparison Matrix</div>
      <div class="view-subtitle">Comparing <strong>${candidate}</strong> against <strong>production-v1</strong> across perturbation conditions (Tolerance Threshold: -0.15)</div>
    </div>
    ${createDataTable({ headers, rows })}
  `;
}

// ----------------------------------------------------------------------------
// VIEW 2: Failure Explorer
// ----------------------------------------------------------------------------
function renderFailureExplorer(container) {
  const failures = dashboardState.getFailureRecords();
  const selectedFailureId = dashboardState.getSelectedFailureId();
  const selectedFailure = dashboardState.getFailureById(selectedFailureId);
  const activeTab = dashboardState.getActiveFailureTab();
  const candidate = dashboardState.getSelectedCandidate();
  const capsule = dashboardState.getFailureCapsule(selectedFailureId);
  const regression = dashboardState.getLinkedRegression(selectedFailureId);

  // 1. Build Left List Items
  const listItemsHtml = failures.map(f => {
    const isSelected = f.failure_id === selectedFailureId;
    const condTitle = f.condition.type.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
    const delta = f.metric.delta;

    return `
      <div class="explorer-item ${isSelected ? 'active' : ''}" onclick="window.selectFailure('${f.failure_id}')">
        <div class="explorer-item-top">
          <span class="explorer-item-id">#${f.failure_id.replace('failure-', '')}</span>
          ${createStatusBadge(f.severity)}
        </div>
        <div class="explorer-item-title">${condTitle}</div>
        <div class="explorer-item-meta">
          <span>${f.metric.name}</span>
          ${createDiffBar(delta, -0.15)}
        </div>
      </div>
    `;
  }).join("");

  // 2. Build Tab Content based on activeTab
  let tabContentHtml = "";
  if (activeTab === "overview") {
    tabContentHtml = `
      <div class="kv-grid">
        <div class="kv-key">Evaluation ID</div>
        <div class="kv-val mono">${selectedFailure.evaluation_id || 'eval-001'}</div>
        <div class="kv-key">Experiment ID</div>
        <div class="kv-val mono">${selectedFailure.experiment_id || 'exp-001'}</div>
        <div class="kv-key">Originating Model</div>
        <div class="kv-val mono">${selectedFailure.model.name}:${selectedFailure.model.version}</div>
        <div class="kv-key">Artifact Reference</div>
        <div class="kv-val mono">${selectedFailure.model.artifact_reference || 'models/' + selectedFailure.model.name}</div>
        <div class="kv-key">Evaluation Dataset</div>
        <div class="kv-val mono">${selectedFailure.dataset ? selectedFailure.dataset.name + ' (' + selectedFailure.dataset.version + ')' : 'demo-dataset (v1)'}</div>
        <div class="kv-key">Verification Status</div>
        <div class="kv-val mono">${selectedFailure.verification.status.toUpperCase()} (${selectedFailure.verification.verification_runs} runs, consistent: ${selectedFailure.verification.consistent})</div>
        <div class="kv-key">Discovered At</div>
        <div class="kv-val mono">${selectedFailure.created_at}</div>
      </div>

      <div style="margin-top: 12px; font-size: 11px; color: var(--text-muted);">
        <strong>Failure Evidence:</strong> Performance degraded from <strong>${selectedFailure.metric.baseline_score.toFixed(2)}</strong> to <strong>${selectedFailure.metric.candidate_score.toFixed(2)}</strong> under condition <code>${selectedFailure.condition.type}</code> (Delta: <span style="color: var(--status-block); font-weight: 600;">${selectedFailure.metric.delta.toFixed(2)}</span> exceeding tolerance threshold -0.15).
      </div>
    `;
  } else if (activeTab === "parameters") {
    const paramRows = Object.entries(selectedFailure.condition.parameters || {}).map(([k, v]) => `
      <div class="kv-key">${k}</div>
      <div class="kv-val mono">${v}</div>
    `).join("");

    tabContentHtml = `
      <div style="font-size: 11px; font-weight: 600; margin-bottom: 8px; color: var(--text-bright);">Challenge Perturbation Parameters:</div>
      <div class="kv-grid">
        <div class="kv-key">condition_type</div>
        <div class="kv-val mono">${selectedFailure.condition.type}</div>
        ${paramRows}
        <div class="kv-key">randomness.seed</div>
        <div class="kv-val mono">${capsule ? capsule.randomness.seed : 42}</div>
        <div class="kv-key">preprocessing_pipeline</div>
        <div class="kv-val mono">${capsule ? capsule.preprocessing.name + ' (v' + capsule.preprocessing.version + ')' : 'standard-cv-preprocessing:1.0'}</div>
      </div>
    `;
  } else if (activeTab === "reproduction") {
    const isReplaying = latestReplayResult && latestReplayResult.failure_id === selectedFailureId;
    let replayBanner = "";
    if (isReplaying) {
      const isPassed = latestReplayResult.is_passed;
      replayBanner = `
        <div class="replay-alert ${isPassed ? 'passed' : 'failed'}">
          <div style="font-weight: 700; margin-bottom: 4px; display: flex; align-items: center; gap: 5px;">
            <i class="${isPassed ? 'ri-check-line' : 'ri-close-circle-line'}"></i>
            ${isPassed ? 'REPLAY PASSED' : 'REPLAY FAILED (REGRESSION REPRODUCED)'}
          </div>
          <div>Tested on <strong>${latestReplayResult.candidate}</strong>: Observed ${selectedFailure.metric.name} = <strong>${latestReplayResult.observed_score.toFixed(2)}</strong> (Threshold: <strong>${latestReplayResult.minimum_threshold.toFixed(2)}</strong>).</div>
        </div>
      `;
    }

    tabContentHtml = `
      <div class="repro-card">
        <div class="repro-header">
          <div>
            <div style="font-weight: 600; color: var(--text-bright); font-size: 12px;">Reproducibility Capsule: <span class="mono" style="color: var(--accent-blue);">${selectedFailure.reproducibility_capsule_id || 'capsule-147'}</span></div>
            <div style="font-size: 11px; color: var(--text-muted); margin-top: 2px;">Frozen deterministic test harness (Python 3.11 / PyTorch)</div>
          </div>
          <button class="btn-topbar-primary" onclick="window.triggerFailureReplay('${selectedFailure.failure_id}')">
            <i class="ri-play-fill"></i> <span>Replay Failure on ${candidate}</span>
          </button>
        </div>

        <div class="kv-grid" style="margin-bottom: 0;">
          <div class="kv-key">capsule_id</div>
          <div class="kv-val mono">${capsule ? capsule.capsule_id : (selectedFailure.reproducibility_capsule_id || 'capsule-147')}</div>
          <div class="kv-key">target_candidate</div>
          <div class="kv-val mono">${candidate}</div>
          <div class="kv-key">seed</div>
          <div class="kv-val mono">${capsule ? capsule.randomness.seed : 42} (Deterministic)</div>
          <div class="kv-key">verification_runs</div>
          <div class="kv-val mono">${selectedFailure.verification.verification_runs}x (Consistent: true)</div>
          <div class="kv-key">batch_size</div>
          <div class="kv-val mono">${capsule ? capsule.evaluation.batch_size : 32}</div>
        </div>

        ${replayBanner}
      </div>
    `;
  } else if (activeTab === "regression") {
    tabContentHtml = `
      <div style="font-size: 11px; font-weight: 600; margin-bottom: 8px; color: var(--text-bright);">Linked Regression Record (The REMEMBER Layer):</div>
      <div class="kv-grid">
        <div class="kv-key">regression_id</div>
        <div class="kv-val mono" style="color: var(--accent-blue);">${regression ? regression.regression_id : 'regression-147'}</div>
        <div class="kv-key">test_name</div>
        <div class="kv-val">${regression ? regression.name : selectedFailure.condition.type}</div>
        <div class="kv-key">enforced_metric</div>
        <div class="kv-val mono">${regression ? regression.metric.name : selectedFailure.metric.name}</div>
        <div class="kv-key">minimum_threshold</div>
        <div class="kv-val mono" style="font-weight: 600;">${regression ? regression.metric.minimum_threshold.toFixed(2) : '0.65'}</div>
        <div class="kv-key">policy</div>
        <div class="kv-val">${createStatusBadge(regression ? regression.policy : 'block')}</div>
        <div class="kv-key">status</div>
        <div class="kv-val">${createStatusBadge(regression && regression.enabled ? 'ENABLED' : 'DISABLED')}</div>
      </div>

      <div style="margin-top: 12px;">
        <button class="btn-topbar-secondary" onclick="window.navigateToMemory('${regression ? regression.regression_id : 'regression-147'}')">
          <i class="ri-database-2-line"></i> <span>Open in Failure Memory</span>
        </button>
      </div>
    `;
  } else if (activeTab === "raw") {
    tabContentHtml = createCodeInspector(selectedFailure, `FailureRecord: ${selectedFailure.failure_id} (docs/contracts/failure_record.json)`);
  }

  // 3. Render Complete Split Pane
  const condTitle = selectedFailure.condition.type.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());

  container.innerHTML = `
    <div class="view-header">
      <div class="view-title"><i class="ri-search-eye-line"></i> Failure Explorer</div>
      <div class="view-subtitle">Developer inspection workbench for discovered model vulnerabilities, verified failure capsules, and test seeds</div>
    </div>

    <div class="explorer-split">
      
      <!-- Left Master Pane -->
      <aside class="explorer-master">
        <div class="explorer-master-header">
          <span>Discovered Failures</span>
          <span>${failures.length} Records</span>
        </div>
        <div class="explorer-list">
          ${listItemsHtml}
        </div>
      </aside>

      <!-- Center/Right Detail Workspace -->
      <section class="explorer-detail">
        
        <!-- Header Card -->
        <div class="detail-header-card">
          <div class="detail-headline">
            <div class="detail-title-group">
              <span class="detail-id">#${selectedFailure.failure_id.replace('failure-', '')}</span>
              <span class="detail-condition">${condTitle}</span>
              ${createStatusBadge(selectedFailure.severity)}
              ${createStatusBadge(selectedFailure.verification.status)}
            </div>
            <div class="mono" style="font-size: 11px; color: var(--text-muted);">
              ${selectedFailure.failure_id}
            </div>
          </div>

          <div class="detail-quick-stats">
            <div>Baseline: <strong class="mono" style="color: var(--text-bright);">${selectedFailure.metric.baseline_score.toFixed(2)}</strong></div>
            <div>Candidate: <strong class="mono" style="color: var(--status-block);">${selectedFailure.metric.candidate_score.toFixed(2)}</strong></div>
            <div>Delta: <span style="color: var(--status-block); font-weight: 700;">${selectedFailure.metric.delta.toFixed(2)}</span></div>
            <div>Metric: <strong class="mono">${selectedFailure.metric.name}</strong></div>
            <div>Model: <strong class="mono">${selectedFailure.model.name}:${selectedFailure.model.version}</strong></div>
          </div>
        </div>

        <!-- Detail Tabs Navigation -->
        <div class="detail-tab-nav">
          <div class="detail-tab-btn ${activeTab === 'overview' ? 'active' : ''}" onclick="window.setFailureTab('overview')"><i class="ri-file-info-line"></i> Overview</div>
          <div class="detail-tab-btn ${activeTab === 'parameters' ? 'active' : ''}" onclick="window.setFailureTab('parameters')"><i class="ri-sound-module-line"></i> Parameters</div>
          <div class="detail-tab-btn ${activeTab === 'reproduction' ? 'active' : ''}" onclick="window.setFailureTab('reproduction')"><i class="ri-refresh-line"></i> Reproduction</div>
          <div class="detail-tab-btn ${activeTab === 'regression' ? 'active' : ''}" onclick="window.setFailureTab('regression')"><i class="ri-shield-check-line"></i> Regression</div>
          <div class="detail-tab-btn ${activeTab === 'raw' ? 'active' : ''}" onclick="window.setFailureTab('raw')"><i class="ri-code-line"></i> Raw JSON</div>
        </div>

        <!-- Tab Body Content -->
        <div class="detail-pane-content">
          ${tabContentHtml}
        </div>

      </section>

    </div>
  `;
}

window.selectFailure = function(failureId) {
  dashboardState.setSelectedFailureId(failureId);
  latestReplayResult = null;
  updateBreadcrumbs();
  renderCurrentView();
};

window.setFailureTab = function(tabKey) {
  dashboardState.setActiveFailureTab(tabKey);
  renderCurrentView();
};

window.triggerFailureReplay = function(failureId) {
  const candidate = dashboardState.getSelectedCandidate();
  const replayRes = dashboardState.replayFailure(failureId, candidate);
  latestReplayResult = replayRes;

  // Stream output to Terminal Dock
  currentDockTab = "terminal";
  const dockTabs = document.querySelectorAll(".dock-tab");
  dockTabs.forEach(t => t.classList.toggle("active", t.getAttribute("data-dock") === "terminal"));

  const dockBody = document.getElementById("dock-content");
  if (dockBody) {
    const lines = [
      `Deterministically replaying ${failureId} on ${candidate}`,
      `Challenge Condition: ${replayRes.condition_type} (seed=${replayRes.seed})`,
      `-------------------------------------------------------------------`,
      ...replayRes.execution_trace,
      `-------------------------------------------------------------------`,
      replayRes.is_passed ? `REPLAY SUCCESS: Candidate meets threshold requirement.` : `REPLAY FAILURE: Candidate vulnerability reproduced.`
    ];
    dockBody.innerHTML = createTerminalOutput(lines, `modelshield replay ${failureId} --candidate ${candidate}`);
  }

  renderCurrentView();
};

window.navigateToMemory = function(regressionId) {
  currentView = "memory";
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(n => {
    n.classList.toggle("active", n.getAttribute("data-view") === "memory");
  });
  updateBreadcrumbs();
  renderCurrentView();
};

// ----------------------------------------------------------------------------
// VIEW 3: Failure Memory
// ----------------------------------------------------------------------------
function renderFailureMemory(container) {
  const regressions = dashboardState.getRegressionBank();

  const headers = ["Regression ID", "Name", "Linked Failure", "Metric", "Min Threshold", "Policy", "Status", "Action"];
  const rows = regressions.map(r => {
    return [
      `<strong class="mono">${r.regression_id}</strong>`,
      `<span>${r.name}</span>`,
      `<span class="mono" style="color: var(--accent-blue);">${r.failure_id}</span>`,
      `<span class="mono">${r.metric.name}</span>`,
      `<span class="mono">${r.metric.minimum_threshold.toFixed(2)}</span>`,
      createStatusBadge(r.policy),
      createStatusBadge(r.enabled ? "ENABLED" : "DISABLED"),
      `<button class="btn-topbar-secondary" onclick="window.toggleRegressionState('${r.regression_id}')">${r.enabled ? 'Disable' : 'Enable'}</button>`
    ];
  });

  container.innerHTML = `
    <div class="view-header">
      <div class="view-title"><i class="ri-database-2-line"></i> Failure Memory (Regression Bank)</div>
      <div class="view-subtitle">Active regression tests compiled from verified failure records (The REMEMBER Layer)</div>
    </div>
    ${createDataTable({ headers, rows })}
  `;
}

window.toggleRegressionState = function(regressionId) {
  dashboardState.toggleRegression(regressionId);
  syncAllUI();
};

// ----------------------------------------------------------------------------
// VIEW 4: Regression Results
// ----------------------------------------------------------------------------
function renderRegressionResults(container) {
  const candidate = dashboardState.getSelectedCandidate();
  const results = dashboardState.getRegressionResults(candidate);

  const headers = ["Regression ID", "Name", "Metric", "Observed", "Threshold", "Policy", "Status"];
  const rows = results.map(res => {
    let scoreColor = "var(--text-muted)";
    if (res.enabled) {
      scoreColor = res.status === "passed" ? "var(--status-pass)" : (res.status === "review_required" ? "var(--status-review)" : "var(--status-block)");
    }

    return [
      `<strong class="mono">${res.regression_id}</strong>`,
      `<span>${res.name}</span>`,
      `<span class="mono">${res.metric_name}</span>`,
      `<span class="mono" style="color: ${scoreColor}; font-weight: 600;">${res.observed_score.toFixed(2)}</span>`,
      `<span class="mono">${res.minimum_threshold.toFixed(2)}</span>`,
      createStatusBadge(res.policy),
      createStatusBadge(res.status)
    ];
  });

  container.innerHTML = `
    <div class="view-header">
      <div class="view-title"><i class="ri-list-check-3"></i> Regression Execution Log</div>
      <div class="view-subtitle">Evaluation telemetry of <strong>${candidate}</strong> against active regression tests</div>
    </div>
    ${createDataTable({ headers, rows })}
  `;
}

// ----------------------------------------------------------------------------
// VIEW 5: Release Gate
// ----------------------------------------------------------------------------
function renderReleaseGate(container) {
  const candidate = dashboardState.getSelectedCandidate();
  const decision = dashboardState.getReleaseDecision(candidate);

  const isBlocked = decision.decision === "block";
  const isReview = decision.decision === "review";
  const statusClass = isBlocked ? "block" : (isReview ? "review" : "pass");
  const verdictText = isBlocked ? "RELEASE BLOCKED" : (isReview ? "RELEASE REVIEW REQUIRED" : "RELEASE APPROVED");
  const iconClass = isBlocked ? "ri-close-circle-line" : (isReview ? "ri-alert-line" : "ri-check-line");

  const contractPayload = {
    schema_version: decision.schema_version,
    decision_id: decision.decision_id,
    model: decision.model,
    decision: decision.decision,
    summary: decision.summary,
    failures: decision.failures,
    reason: decision.reason,
    timestamp: decision.timestamp
  };

  container.innerHTML = `
    <div class="view-header">
      <div class="view-title"><i class="ri-shield-check-line"></i> Release Gatekeeper</div>
      <div class="view-subtitle">Automated CI/CD Gating for <strong>${candidate}</strong> release verification</div>
    </div>

    <div class="gate-card ${statusClass}">
      <div class="gate-headline">
        <div class="gate-status-text ${statusClass}">
          <i class="${iconClass}"></i> <span>${verdictText}</span>
        </div>
        <div class="mono" style="color: var(--text-muted); font-size: 11px;">${decision.decision_id} • ${decision.timestamp.slice(0, 19)}Z</div>
      </div>
      <div style="font-size: 13px; color: var(--text-bright); margin-bottom: 6px;">
        ${decision.reason}
      </div>
      <div style="font-size: 11px; color: var(--text-muted);">
        Enforced Rule: ${isBlocked ? 'Any failure under <code>block</code> policy immediately blocks deployment.' : 'All blocking regression policies met safety criteria.'}
      </div>
      <div class="gate-stats">
        <div>Total Regressions: <strong>${decision.summary.total_regressions}</strong></div>
        <div style="color: var(--status-pass);">Passed: <strong>${decision.summary.passed}</strong></div>
        <div style="color: var(--status-block);">Failed: <strong>${decision.summary.failed}</strong></div>
        <div style="color: var(--status-review);">Review Required: <strong>${decision.summary.review_required}</strong></div>
        <div style="margin-left: auto; font-weight: 700; color: ${isBlocked ? 'var(--status-block)' : (isReview ? 'var(--status-review)' : 'var(--status-pass)')};">
          CI EXIT CODE: ${decision.exit_code}
        </div>
      </div>
    </div>

    ${createCodeInspector(contractPayload, `Release Decision Payload (docs/contracts/release_decision.json)`)}
  `;
}

// ----------------------------------------------------------------------------
// Bottom Dock Rendering (Split Terminal & GitHub/CI Run Status)
// ----------------------------------------------------------------------------
function renderDockContent() {
  const dockBody = document.getElementById("dock-content");
  if (!dockBody) return;

  const candidate = dashboardState.getSelectedCandidate();
  const decision = dashboardState.getReleaseDecision(candidate);

  if (currentDockTab === "terminal") {
    const lines = [
      `Initializing ModelShield regression runner...`,
      `Loaded ${decision.detailed_checks.length} active regression checks`
    ];

    decision.detailed_checks.forEach(chk => {
      const isPass = chk.status === "passed";
      const icon = isPass ? "✓" : "✖";
      const verdict = isPass ? "PASSED" : (chk.status === "review_required" ? "REVIEW REQUIRED" : `FAILED (${chk.policy.toUpperCase()})`);
      lines.push(`${icon} ${chk.regression_id.padEnd(16)} ${chk.condition_type.padEnd(20)} ${chk.observed_score.toFixed(2)} / ${chk.minimum_threshold.toFixed(2)}  ${verdict}`);
    });

    if (decision.decision === "block") {
      lines.push(`✖ ${decision.summary.failed}/${decision.summary.total_regressions} checks failed (blocking)`);
      lines.push(`RELEASE BLOCKED`);
      lines.push(`Process exited with code 1`);
    } else if (decision.decision === "review") {
      lines.push(`▲ ${decision.summary.review_required} check(s) require review`);
      lines.push(`RELEASE REVIEW REQUIRED`);
      lines.push(`Process exited with code 2`);
    } else {
      lines.push(`✓ All ${decision.summary.total_regressions} checks passed`);
      lines.push(`RELEASE APPROVED`);
      lines.push(`Process exited with code 0`);
    }

    const checksHtml = decision.detailed_checks.map(chk => {
      const isPass = chk.status === "passed";
      return `
        <div class="ci-check-item">
          <span class="mono">${chk.regression_id}</span>
          <span style="color: var(--text-muted);">${chk.condition_type}</span>
          <span style="color: ${isPass ? 'var(--status-pass)' : 'var(--status-block)'}; font-weight: 600;">
            ${isPass ? '<i class="ri-check-line"></i> Passed' : '<i class="ri-close-circle-line"></i> Failed'}
          </span>
        </div>
      `;
    }).join("");

    dockBody.innerHTML = `
      <div class="terminal-split">
        <div class="terminal-left">
          ${createTerminalOutput(lines, `modelshield regression run --candidate ${candidate}`)}
        </div>
        <div class="terminal-right">
          <div class="ci-run-card">
            <div class="ci-run-header">
              <span>Latest Run: <strong>#1287</strong></span>
              <span class="badge ${decision.decision === 'block' ? 'badge-block' : 'badge-pass'}">
                ${decision.decision.toUpperCase()}
              </span>
            </div>
            <div class="ci-run-meta-row"><span>Workflow</span> <span class="ci-run-meta-val mono">modelshield-regression.yml</span></div>
            <div class="ci-run-meta-row"><span>Trigger</span> <span class="ci-run-meta-val">push</span></div>
            <div class="ci-run-meta-row"><span>Branch</span> <span class="ci-run-meta-val mono">main</span></div>
            <div class="ci-run-meta-row"><span>Commit</span> <span class="ci-run-meta-val mono">a1b2c3d</span></div>
            <div class="ci-run-meta-row"><span>Duration</span> <span class="ci-run-meta-val mono">00:02:31</span></div>
            <div class="ci-run-meta-row"><span>Finished</span> <span class="ci-run-meta-val">2m ago</span></div>
          </div>
          <div class="ci-checks-list">
            <div class="ci-checks-header">Checks (${decision.detailed_checks.length})</div>
            ${checksHtml}
          </div>
        </div>
      </div>
    `;
  } else if (currentDockTab === "logs") {
    dockBody.innerHTML = `
      <div style="color: var(--text-muted); font-size: 11px; line-height: 1.6;">
        <div>[${new Date().toISOString()}] <span style="color: var(--accent-blue);">INFO</span>  Evaluated candidate '${candidate}' against active regression bank</div>
        <div>[${new Date().toISOString()}] <span style="color: var(--accent-blue);">INFO</span>  Summary: ${decision.summary.passed} passed, ${decision.summary.failed} failed, ${decision.summary.review_required} review required</div>
        <div>[${new Date().toISOString()}] <span style="${decision.decision === 'block' ? 'color: var(--status-block);' : 'color: var(--status-pass);'}">${decision.decision === 'block' ? 'ERROR' : 'INFO'}</span> Gating Verdict: ${decision.decision.toUpperCase()} (Exit code ${decision.exit_code})</div>
      </div>
    `;
  } else if (currentDockTab === "ci") {
    const isBlocked = decision.decision === "block";
    dockBody.innerHTML = `
      <div style="display: flex; gap: 24px; font-size: 11px; padding: 6px 0;">
        <div>Pipeline: <strong>modelshield-gate.yml</strong></div>
        <div>Target Model: <strong>${candidate}</strong></div>
        <div>Verdict: <span class="badge ${isBlocked ? 'badge-block' : (decision.decision === 'review' ? 'badge-review' : 'badge-pass')}">${decision.decision.toUpperCase()} (EXIT ${decision.exit_code})</span></div>
        <div>Policy Enforced: <strong class="mono">strict_block</strong></div>
      </div>
    `;
  }
}

function runReleaseGateWorkflow() {
  currentView = "gate";
  const navItems = document.querySelectorAll(".nav-item");
  navItems.forEach(n => {
    n.classList.toggle("active", n.getAttribute("data-view") === "gate");
  });
  syncAllUI();

  currentDockTab = "terminal";
  const dockTabs = document.querySelectorAll(".dock-tab");
  dockTabs.forEach(t => t.classList.toggle("active", t.getAttribute("data-dock") === "terminal"));
  renderDockContent();
}
