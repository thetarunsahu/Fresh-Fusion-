const API_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(body.detail || `Request failed: ${response.status}`);
  }
  return response.status === 204 ? null : response.json();
}

export const api = {
  health: () => request("/api/health"),
  overview: () => request("/api/overview"),
  readings: (sampleCode) =>
    request(`/api/sensors/readings?limit=24${sampleCode ? `&sample_code=${encodeURIComponent(sampleCode)}` : ""}`),
  createSample: (fruitType = "Banana") =>
    request("/api/samples", {
      method: "POST",
      body: JSON.stringify({ fruit_type: fruitType, notes: "Dashboard development sample" }),
    }),
  pushReading: (sampleCode, payload) =>
    request("/api/sensors/readings", {
      method: "POST",
      body: JSON.stringify({ sample_code: sampleCode, ...payload }),
    }),
};
