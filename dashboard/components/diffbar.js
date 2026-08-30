/**
 * DiffBar Component
 * Visualizes numeric delta with a restrained, compact inline indicator.
 */
export function createDiffBar(delta, threshold = -0.15) {
  const isNegative = delta < 0;
  const isBreached = delta < threshold;
  const colorClass = isBreached ? "diff-breach" : (isNegative ? "diff-warn" : "diff-good");
  const sign = delta > 0 ? "+" : "";
  const pct = Math.min(Math.abs(delta) * 100, 100);

  return `
    <div class="diff-container mono ${colorClass}">
      <span class="diff-val">${sign}${delta.toFixed(2)}</span>
      <div class="diff-bar-track">
        <div class="diff-bar-fill" style="width: ${pct}%;"></div>
      </div>
    </div>
  `;
}
