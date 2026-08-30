/**
 * CodeInspector Component
 * Renders syntax-highlighted JSON/code with copy-to-clipboard action using Remix Icons.
 */
export function createCodeInspector(data, title = "Contract Payload") {
  const jsonStr = typeof data === "string" ? data : JSON.stringify(data, null, 2);
  const escaped = jsonStr
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  return `
    <div class="code-inspector">
      <div class="code-inspector-header">
        <span class="code-inspector-title mono">${title}</span>
        <button class="btn-dock-tool" onclick="navigator.clipboard.writeText(\`${escaped.replace(/\\/g, '\\\\').replace(/`/g, '\\`')}\`); alert('Copied to clipboard!');">
          <i class="ri-file-copy-line"></i> <span>Copy JSON</span>
        </button>
      </div>
      <pre class="json-viewer"><code>${escaped}</code></pre>
    </div>
  `;
}
