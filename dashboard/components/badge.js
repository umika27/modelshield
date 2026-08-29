/**
 * StatusBadge Component
 * Renders developer-styled status indicators using Remix Icons.
 */
export function createStatusBadge(status, labelOverride = null) {
  const st = (status || "").toLowerCase();
  let badgeClass = "badge-neutral";
  let iconClass = "ri-checkbox-blank-circle-line";
  let label = labelOverride || status.toUpperCase();

  if (["pass", "passed", "verified", "enabled", "success"].includes(st)) {
    badgeClass = "badge-pass";
    iconClass = "ri-check-line";
  } else if (["block", "blocked", "fail", "failed", "critical"].includes(st)) {
    badgeClass = "badge-block";
    iconClass = "ri-close-circle-line";
  } else if (["review", "review_required", "warn", "warning", "high", "medium"].includes(st)) {
    badgeClass = "badge-review";
    iconClass = "ri-alert-line";
  } else if (["disabled", "allow", "low", "inactive"].includes(st)) {
    badgeClass = "badge-neutral";
    iconClass = "ri-checkbox-blank-circle-line";
  }

  return `<span class="badge ${badgeClass}"><i class="${iconClass} badge-icon"></i> <span>${label}</span></span>`;
}
