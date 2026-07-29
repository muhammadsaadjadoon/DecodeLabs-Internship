const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

function absoluteAsset(path) {
  if (!path) return "";
  if (/^https?:\/\//i.test(path)) return path;
  return `${BASE_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

function normalizeUser(user) {
  if (!user) return null;
  return { ...user, avatar: absoluteAsset(user.avatar_url || user.avatar || "") };
}

function friendlyNetworkError(error) {
  if (error?.name === "AbortError") return "Batch cancelled before completion.";
  return "Lexora could not connect to the service. Please check your connection and try again.";
}

async function handle(res) {
  if (!res.ok) {
    let detail = res.statusText || "Request failed";
    try {
      const body = await res.json();
      detail = body.detail || body.message || JSON.stringify(body);
    } catch {
      // keep status text
    }
    throw new Error(detail);
  }
  if (res.status === 204) return null;
  return res.json();
}

async function api(path, options = {}) {
  try {
    const res = await fetch(`${BASE_URL}${path}`, {
      credentials: "include",
      ...options,
      headers: options.body instanceof FormData
        ? options.headers
        : { "Content-Type": "application/json", ...(options.headers || {}) },
    });
    return handle(res);
  } catch (error) {
    if (error instanceof TypeError) throw new Error(friendlyNetworkError(error));
    throw error;
  }
}

export async function fetchMeta() {
  try {
    const res = await fetch(`${BASE_URL}/api/meta`, { credentials: "include" });
    return handle(res);
  } catch (error) {
    throw new Error(friendlyNetworkError(error));
  }
}

export async function generateCopy(payload) {
  return api("/api/generate", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function bulkGenerate(file, signal) {
  try {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${BASE_URL}/api/bulk/generate`, {
      method: "POST",
      body: formData,
      signal,
      credentials: "include",
    });
    return handle(res);
  } catch (error) {
    if (error.name === "AbortError") throw new Error(friendlyNetworkError(error));
    if (error instanceof TypeError) throw new Error(friendlyNetworkError(error));
    throw error;
  }
}

export function bulkTemplateUrl() {
  return `${BASE_URL}/api/bulk/template`;
}

export async function getCurrentUser() {
  const data = await api("/api/auth/me");
  return normalizeUser(data.user);
}

export async function signUpAccount(payload) {
  const data = await api("/api/auth/signup", { method: "POST", body: JSON.stringify(payload) });
  return normalizeUser(data.user);
}

export async function signInAccount(payload) {
  const data = await api("/api/auth/signin", { method: "POST", body: JSON.stringify(payload) });
  return normalizeUser(data.user);
}

export async function logoutAccount() {
  await api("/api/auth/logout", { method: "POST" });
}

export async function requestPasswordReset(email) {
  return api("/api/auth/forgot", { method: "POST", body: JSON.stringify({ email }) });
}

export async function resetAccountPassword(payload) {
  return api("/api/auth/reset", { method: "POST", body: JSON.stringify(payload) });
}

export async function updateProfile(payload) {
  const data = await api("/api/profile", { method: "PATCH", body: JSON.stringify(payload) });
  return normalizeUser(data.user);
}

export async function uploadProfilePhoto(file) {
  const formData = new FormData();
  formData.append("file", file);
  const data = await api("/api/profile/photo", { method: "POST", body: formData });
  return normalizeUser(data.user);
}

export async function removeProfilePhoto() {
  const data = await api("/api/profile/photo", { method: "DELETE" });
  return normalizeUser(data.user);
}

export async function changeAccountPassword(payload) {
  return api("/api/profile/password", { method: "POST", body: JSON.stringify(payload) });
}

export async function deleteAccount() {
  return api("/api/profile", { method: "DELETE" });
}

export async function fetchWorkspace() {
  return api("/api/workspace");
}

export async function saveWorkspaceItem(section, item) {
  const data = await api(`/api/workspace/${section}`, { method: "POST", body: JSON.stringify({ item }) });
  return data.item;
}

export async function deleteWorkspaceItem(section, id) {
  await api(`/api/workspace/${section}/${id}`, { method: "DELETE" });
}

export async function clearWorkspaceSection(section) {
  await api(`/api/workspace/${section}`, { method: "DELETE" });
}
