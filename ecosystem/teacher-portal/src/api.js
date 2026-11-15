// One way to talk to the API. Errors come back in plain words for the screen.
const TOKEN_KEY = "hilys-teacher-token";

export function getToken() {
  try { return localStorage.getItem(TOKEN_KEY); } catch { return null; }
}
export function setToken(t) {
  try { t ? localStorage.setItem(TOKEN_KEY, t) : localStorage.removeItem(TOKEN_KEY); } catch { /* private mode */ }
}

export class ApiError extends Error {
  constructor(message, fields = {}, status = 0) { super(message); this.fields = fields; this.status = status; }
}

function plainError(status, data) {
  if (status === 0) return new ApiError("We could not reach the server. Check your internet and try again.");
  if (status === 401) return new ApiError("Please sign in again.", {}, 401);
  if (status === 403) return new ApiError(data?.detail || "Your role cannot do this.", {}, 403);
  if (status >= 500) return new ApiError("Something went wrong on our side. Try again in a minute.", {}, status);
  const fields = {};
  let message = "";
  if (data && typeof data === "object") {
    for (const [k, v] of Object.entries(data)) {
      const text = Array.isArray(v) ? v.join(" ") : typeof v === "string" ? v : JSON.stringify(v);
      if (k === "detail" || k === "non_field_errors") message = text; else fields[k] = text;
    }
  }
  if (!message) message = Object.values(fields)[0] || "Please check the form.";
  return new ApiError(message, fields, status);
}

export async function api(path, { method = "GET", body, raw = false } = {}) {
  const headers = { Accept: "application/json" };
  const token = getToken();
  if (token) headers.Authorization = `Token ${token}`;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  let res;
  try {
    res = await fetch(`/api${path}`, { method, headers, body: body !== undefined ? JSON.stringify(body) : undefined });
  } catch {
    throw plainError(0);
  }
  if (res.status === 401) { setToken(null); window.dispatchEvent(new Event("hilys-signed-out")); }
  if (raw) { if (!res.ok) throw plainError(res.status, await res.json().catch(() => null)); return res; }
  const data = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw plainError(res.status, data);
  return data;
}

// Opens a PDF from an authenticated endpoint in a new tab.
export async function openPdf(path) {
  const win = window.open("", "_blank");
  try {
    const res = await api(path, { raw: true });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    if (win) win.location = url; else window.location = url;
  } catch (e) {
    if (win) win.close();
    throw e;
  }
}

export function qs(params) {
  const p = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) if (v !== "" && v !== undefined && v !== null) p.set(k, v);
  const s = p.toString();
  return s ? `?${s}` : "";
}
