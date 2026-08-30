export class ApiError extends Error { constructor(message, status = null) { super(message); this.name = "ApiError"; this.status = status; } }

export function sanitizeApiErrorDetail(detail, fallbackMessage) {
  if (typeof detail !== "string" || !detail.trim() || detail.length > 300) return fallbackMessage;
  if (/\b(?:authorization|bearer|api[ _-]?key|token|secret|password)\b\s*[:=]?\s*\S+/i.test(detail)) return fallbackMessage;
  if (/traceback|\bfile\s+"|\bat\s+.+\(/i.test(detail)) return fallbackMessage;
  return detail.replace(/(?:\\\\|\/\/)[^\\/\s]+[\\/][^\\/\s]+(?:[\\/][^,'"`\r\n]*)?|[A-Za-z]:[\\/][^,'"`\r\n]*|\/(?:home|users|var|etc|tmp|private|opt|mnt|workspace|app|srv|builds|runner)(?:\/[^,'"`\r\n]*)?/gi, "[redacted path]");
}

async function readResponse(response, fallbackMessage) {
  let body = null;
  try { body = await response.json(); } catch { /* Non-JSON responses have no safe detail. */ }
  if (!response.ok) throw new ApiError(sanitizeApiErrorDetail(body?.detail, fallbackMessage), response.status);
  return body;
}

export function createModelShieldApi(fetchImpl = globalThis.fetch) {
  if (typeof fetchImpl !== "function") throw new TypeError("A fetch implementation is required.");
  return {
    async getLatestAnalysis() { return readResponse(await fetchImpl("/api/analysis/latest", { headers: { Accept: "application/json" } }), "Unable to load latest analysis."); },
    async analyze(request) { return readResponse(await fetchImpl("/api/analyze", { method: "POST", headers: { "Content-Type": "application/json", Accept: "application/json" }, body: JSON.stringify(request) }), "Analysis request failed."); },
  };
}
export const modelShieldApi = createModelShieldApi();
