/**
 * TerminalOutput Component
 * Renders monospaced ANSI/CLI output inside the developer bottom dock.
 */
export function createTerminalOutput(lines, command = "modelshield regression run") {
  const lineHtml = lines.map(line => {
    let formatted = line
      .replace(/\[✓ PASS\]|✓ PASSED|PASSED/g, `<span class="term-green">✓ PASSED</span>`)
      .replace(/\[✖ FAIL\]|FAILED \(BLOCK\)|✖ FAILED/g, `<span class="term-red">FAILED (BLOCK)</span>`)
      .replace(/\[▲ REVIEW\]|REVIEW REQUIRED/g, `<span class="term-yellow">▲ REVIEW</span>`)
      .replace(/RELEASE BLOCKED/g, `<span class="term-red-bg"> RELEASE BLOCKED </span>`)
      .replace(/RELEASE APPROVED/g, `<span class="term-green-bg"> RELEASE APPROVED </span>`)
      .replace(/ⓘ/g, `<span class="term-blue">ⓘ</span>`)
      .replace(/INFO/g, `<span class="term-blue">INFO</span>`)
      .replace(/WARN/g, `<span class="term-yellow">WARN</span>`)
      .replace(/ERROR/g, `<span class="term-red">ERROR</span>`);
    return `<div class="term-line">${formatted}</div>`;
  }).join("");

  return `
    <div class="terminal-content">
      <div class="term-prompt"><span class="term-user">modelshield@devbox</span>:<span class="term-dir">~/modelshield</span>$ <span class="term-cmd">${command}</span></div>
      ${lineHtml}
      <div class="term-prompt" style="margin-top: 8px;"><span class="term-user">modelshield@devbox</span>:<span class="term-dir">~/modelshield</span>$ <span class="term-cursor">▋</span></div>
    </div>
  `;
}
