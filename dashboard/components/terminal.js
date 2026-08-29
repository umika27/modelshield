/**
 * TerminalOutput Component
 * Renders developer CLI interactive output with GitHub Actions CI checks overview.
 */
export function createTerminalOutput(lines, command = "modelshield regression run", ciContext = null) {
  const lineHtml = lines.map(line => {
    let formatted = line
      .replace(/\[✓ PASS\]/g, `<span class="term-green"><i class="ri-check-line"></i> PASS</span>`)
      .replace(/\[✖ FAIL\]/g, `<span class="term-red"><i class="ri-close-line"></i> FAIL</span>`)
      .replace(/\[▲ REVIEW\]/g, `<span class="term-yellow"><i class="ri-alert-line"></i> REVIEW</span>`)
      .replace(/RELEASE BLOCKED/g, `<span class="term-red term-bold"><i class="ri-close-circle-fill"></i> RELEASE BLOCKED</span>`)
      .replace(/RELEASE APPROVED/g, `<span class="term-green term-bold"><i class="ri-checkbox-circle-fill"></i> RELEASE APPROVED</span>`)
      .replace(/RELEASE REVIEW REQUIRED/g, `<span class="term-yellow term-bold"><i class="ri-alert-fill"></i> RELEASE REVIEW REQUIRED</span>`)
      .replace(/INFO/g, `<span class="term-blue">INFO</span>`)
      .replace(/WARN/g, `<span class="term-yellow">WARN</span>`)
      .replace(/ERROR/g, `<span class="term-red">ERROR</span>`);
    return `<div class="term-line">${formatted}</div>`;
  }).join("");

  // Build CI overview pane if ciContext provided
  let ciOverviewHtml = "";
  if (ciContext) {
    const isBlocked = ciContext.decision === "block";
    const isReview = ciContext.decision === "review";
    const statusBadgeClass = isBlocked ? "badge-block" : (isReview ? "badge-review" : "badge-pass");
    const statusText = isBlocked ? "FAILED" : (isReview ? "REVIEW" : "PASSED");

    const checksRows = (ciContext.detailed_checks || []).map(chk => {
      const isChkPassed = chk.status === "passed";
      const statusCls = isChkPassed ? "passed" : (chk.status === "review_required" ? "review" : "failed");
      const icon = isChkPassed ? '<i class="ri-check-line"></i> Passed' : (chk.status === "review_required" ? '<i class="ri-alert-line"></i> Review' : '<i class="ri-close-line"></i> Failed');

      return `
        <div class="ci-check-row">
          <span class="ci-check-name mono">${chk.regression_id}</span>
          <span class="ci-check-cond mono">${chk.condition_type}</span>
          <span class="ci-check-status ${statusCls}">${icon}</span>
        </div>
      `;
    }).join("");

    ciOverviewHtml = `
      <div class="ci-overview-pane">
        <div class="ci-run-meta-col">
          <div class="ci-run-header">
            <span class="ci-meta-label">Latest Run:</span>
            <span class="ci-run-id mono">#1287</span>
            <span class="badge ${statusBadgeClass}">${statusText}</span>
          </div>
          <div class="ci-meta-grid">
            <span class="ci-meta-label">Workflow</span>
            <span class="ci-meta-val mono">modelshield-regression.yml</span>
            <span class="ci-meta-label">Trigger</span>
            <span class="ci-meta-val mono">push</span>
            <span class="ci-meta-label">Branch</span>
            <span class="ci-meta-val mono">main</span>
            <span class="ci-meta-label">Commit</span>
            <span class="ci-meta-val mono">a1b2c3d</span>
            <span class="ci-meta-label">Duration</span>
            <span class="ci-meta-val mono">00:02:31</span>
            <span class="ci-meta-label">Finished</span>
            <span class="ci-meta-val">2m ago</span>
          </div>
        </div>
        <div class="ci-checks-col">
          <div class="ci-checks-title">Checks (${ciContext.detailed_checks ? ciContext.detailed_checks.length : 5})</div>
          ${checksRows}
        </div>
      </div>
    `;
  }

  return `
    <div class="dock-split-container">
      <div class="terminal-pane">
        <div class="term-prompt"><span class="term-green">modelshield@devbox</span>:<span class="term-dir">~/modelshield</span><span class="term-symbol">$</span> ${command}</div>
        ${lineHtml}
        <div class="term-prompt" style="margin-top: 6px;"><span class="term-green">modelshield@devbox</span>:<span class="term-dir">~/modelshield</span><span class="term-symbol">$</span> <span class="term-cursor"></span></div>
      </div>
      ${ciOverviewHtml}
    </div>
  `;
}
