export const API_ROOT = import.meta.env.VITE_API_ROOT || window.location.origin;
export const API = `${API_ROOT}/api/v1`;
export const AUTH_TOKEN_KEY = "freshfusion.auth.token";

export const getAuthToken = () => localStorage.getItem(AUTH_TOKEN_KEY);
export const setAuthToken = (token) => {
  if (token) localStorage.setItem(AUTH_TOKEN_KEY, token);
  else localStorage.removeItem(AUTH_TOKEN_KEY);
};
export const clearAuthToken = () => localStorage.removeItem(AUTH_TOKEN_KEY);

async function json(url, options = {}) {
  const { timeoutMs = 30000, ...fetchOptions } = options;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  const token = getAuthToken();
  const headers = new Headers(fetchOptions.headers || {});
  if (token && !headers.has("Authorization")) headers.set("Authorization", `Bearer ${token}`);
  try {
    const res = await fetch(url, {
      ...fetchOptions,
      headers,
      signal: controller.signal,
    });
    if (!res.ok) {
      const body = await res.text();
      let detail;
      try {
        detail = JSON.parse(body).detail;
      } catch {
        /* HTTP text response */
      }
      if (res.status === 401 && !url.endsWith("/auth/login") && !url.endsWith("/auth/register")) {
        clearAuthToken();
      }
      throw new Error(
        typeof detail === "string"
          ? detail
          : `HTTP ${res.status}: ${body.slice(0, 240)}`,
      );
    }
    return res.status === 204 ? null : res.json();
  } finally {
    clearTimeout(timer);
  }
}

export const login = (email, password) =>
  json(`${API}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
export const register = (payload) =>
  json(`${API}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
export const authMe = () => json(`${API}/auth/me`);

export const health = () => json(`${API}/health`);
export const ollamaHealth = () => json(`${API}/ai/ollama/health`);
export const createSample = (fruit_type = "Auto") =>
  json(`${API}/samples`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fruit_type }),
  });
export const listSamples = () => json(`${API}/samples?limit=200`);
export const assetUrl = (path) => (path ? new URL(path, API_ROOT).href : null);
export const bundle = async (id) => {
  const result = await json(`${API}/samples/${encodeURIComponent(id)}/bundle`);
  result.images = result.images.map((image) => ({
    ...image,
    url: assetUrl(image.url),
    analysis: {
      ...image.analysis,
      artifacts: Object.fromEntries(
        Object.entries(image.analysis?.artifacts || {}).map(([key, path]) => [
          key,
          assetUrl(path),
        ]),
      ),
    },
  }));
  return result;
};
export const investigation = (id) =>
  json(`${API}/samples/${encodeURIComponent(id)}/investigation`);
export const explainInvestigation = (id, question = "") => {
  const query = question.trim()
    ? `?question=${encodeURIComponent(question.trim())}`
    : "";
  return json(`${API}/samples/${encodeURIComponent(id)}/investigation/explain${query}`, {
    method: "POST",
    timeoutMs: 90000,
  });
};
export const saveInvestigationSnapshot = (id, trigger = "manual") =>
  json(
    `${API}/samples/${encodeURIComponent(id)}/investigation/snapshot?trigger=${encodeURIComponent(trigger)}`,
    { method: "POST" },
  );
export const investigationSnapshots = (id, limit = 20) =>
  json(
    `${API}/samples/${encodeURIComponent(id)}/investigation/snapshots?limit=${limit}`,
  );
export const activeSample = () => json(`${API}/samples/active`);
export const activateSample = (id) =>
  json(`${API}/samples/${encodeURIComponent(id)}/active`, { method: "PUT" });
export const validationSummary = () => json(`${API}/datasets/validation`);
export const createValidationRun = (name = "manual") =>
  json(`${API}/datasets/validation-runs?name=${encodeURIComponent(name)}`, {
    method: "POST",
  });
export const validationRuns = (limit = 20) =>
  json(`${API}/datasets/validation-runs?limit=${limit}`);
export const verifyAssessment = (id, payload) =>
  json(`${API}/samples/${encodeURIComponent(id)}/verification`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
export const fuse = (id) =>
  json(`${API}/samples/${id}/fusion`, { method: "POST" });
export const pushReading = (payload) =>
  json(`${API}/sensors/readings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
export const datasetRegistry = (fruit) =>
  json(
    `${API}/datasets/registry${fruit ? `?fruit_type=${encodeURIComponent(fruit)}` : ""}`,
  );
export const referenceStatus = () => json(`${API}/datasets/reference-status`);

function imageForm(sampleId, angle, truth, file) {
  const fd = new FormData();
  fd.append("sample_id", sampleId);
  fd.append("angle", angle);
  if (truth) fd.append("ground_truth", truth);
  fd.append("file", file, file.name || `frame-${Date.now()}.jpg`);
  return fd;
}

export const uploadImage = (sampleId, angle, truth, file) =>
  json(`${API}/images/upload`, {
    method: "POST",
    body: imageForm(sampleId, angle, truth, file),
  });

export const uploadStreamFrame = (sampleId, view, truth, file) => {
  const fd = imageForm(sampleId, `live-${view}`, truth, file);
  fd.append("view", view);
  return json(`${API}/images/stream-frame`, { method: "POST", body: fd });
};

export const context = (fruit, lat, lon) =>
  json(
    `${API}/external/context?fruit_type=${encodeURIComponent(fruit)}${lat != null ? `&lat=${lat}&lon=${lon}` : ""}`,
  );

export const wsUrl = (id) => {
  const base = new URL(API_ROOT, window.location.origin);
  const protocol = base.protocol === "https:" ? "wss:" : "ws:";
  return `${protocol}//${base.host}/ws/live/${id}`;
};
