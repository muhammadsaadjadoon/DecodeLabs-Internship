const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function absoluteAssetUrl(value) {
  if (!value) return "";
  if (/^https?:\/\//i.test(value)) return value;
  return `${API_BASE}${value}`;
}

function detailMessage(detail) {
  if (!detail) return "";
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    const first = detail.find((item) => item?.msg || item?.message);
    return first?.msg || first?.message || "The submitted information could not be validated.";
  }
  if (typeof detail === "object") {
    return detail.message || detail.msg || "The submitted information could not be validated.";
  }
  return String(detail);
}

async function safeFetch(url, options = {}) {
  try {
    return await fetch(url, options);
  } catch {
    throw new Error("CodeFix AI could not reach the analysis service. Confirm that the server is running and try again.");
  }
}

async function readResponse(res) {
  const data = await res.json().catch(() => null);
  if (!res.ok) {
    const provided = detailMessage(data?.detail || data?.error);
    const fallbacks = {
      400: "The review request could not be processed.",
      401: "This workspace session is no longer valid. Refresh the page and try again.",
      403: "This workspace is not authorized to perform that action.",
      404: "The requested workspace resource could not be found.",
      413: "The submitted source is larger than the supported review limit.",
      422: "The submitted source or language selection could not be validated.",
      429: "The analysis service is currently at capacity. Please try again shortly.",
      500: "CodeFix AI encountered an unexpected service error. Please try again.",
      502: "CodeFix AI could not verify the analysis response. Please run the review again.",
      503: "The analysis engine is temporarily unavailable. Please try again shortly.",
    };
    throw new Error(provided || fallbacks[res.status] || "The analysis request could not be completed.");
  }
  return data;
}

export async function getWorkspace() {
  const res = await safeFetch(`${API_BASE}/api/workspace`, { credentials: "include" });
  const data = await readResponse(res);
  if (data?.settings?.profile?.avatarUrl) {
    data.settings.profile.avatarUrl = absoluteAssetUrl(data.settings.profile.avatarUrl);
  }
  return data;
}

export async function saveWorkspaceSettings(settings) {
  const res = await safeFetch(`${API_BASE}/api/settings`, {
    method: "PUT",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      profile: settings.profile,
      focus: settings.focus,
      detail: settings.detail,
      auto_explain: settings.autoExplain,
      theme: settings.theme,
    }),
  });
  const data = await readResponse(res);
  if (data?.profile?.avatarUrl) data.profile.avatarUrl = absoluteAssetUrl(data.profile.avatarUrl);
  return data;
}

export async function uploadProfileAvatar(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await safeFetch(`${API_BASE}/api/profile/avatar`, {
    method: "POST",
    credentials: "include",
    body: form,
  });
  const data = await readResponse(res);
  return { ...data, avatarUrl: absoluteAssetUrl(data.avatarUrl) };
}

export async function clearReviewHistory() {
  const res = await safeFetch(`${API_BASE}/api/reviews`, {
    method: "DELETE",
    credentials: "include",
  });
  return readResponse(res);
}

export async function reviewCode({ file, code, language, filename, focus = "balanced", detail = "standard" }) {
  const form = new FormData();
  if (file) form.append("file", file);
  else form.append("code", code);
  if (language) form.append("language", language);
  if (filename) form.append("filename", filename);
  form.append("focus", focus);
  form.append("detail", detail);

  const res = await safeFetch(`${API_BASE}/api/review`, {
    method: "POST",
    credentials: "include",
    body: form,
  });
  return readResponse(res);
}

export async function explainCode({ code, language, filename, detail = "standard", sessionId = null }) {
  const res = await safeFetch(`${API_BASE}/api/explain`, {
    method: "POST",
    credentials: "include",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code, language, filename, detail, session_id: sessionId }),
  });
  return readResponse(res);
}

export async function checkHealth() {
  try {
    const res = await safeFetch(`${API_BASE}/api/health`, { credentials: "include" });
    return res.ok;
  } catch {
    return false;
  }
}
