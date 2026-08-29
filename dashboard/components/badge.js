/**
 * StatusBadge Component
 * Renders developer-styled status indicators (VS Code / GitHub Actions style)
 * Clean glyphs and Remix Icon integration, zero emojis.
 */
export function createStatusBadge(status, labelOverride = null) {
  const st = (status || "").toLowerCase();
  let badgeClass = "badge-neutral";
  let iconHtml = '<i class="ri-checkbox-blank-circle-line"></i>';
  let label = labelOverride || status.toUpperCase();

  if (["pass", "passed", "verified", "enabled", "success"].includes(st)) {
    badgeClass = "badge-pass";
    iconHtml = '<i class="ri-check-line"></i>';
  } else if (["block", "blocked", "fail", "failed", "critical"].includes(st)) {
    badgeClass = "badge-block";
    iconHtml = '<i class="ri-close-line"></i>';
  } else if (["review", "review_required", "warn", "warning", "high", "medium"].includes(st)) {
    badgeClass = "badge-review";
    iconHtml = '<i class="ri-alert-line"></i>';
  } else if (["disabled", "allow", "low", "inactive"].includes(st)) {
    badgeClass = "badge-neutral";
    iconHtml = '<i class="ri-subtract-line"></i>';
  }

  return `<span class="badge ${badgeClass}">${iconHtml} <span>${label}</span></span>`;
}
