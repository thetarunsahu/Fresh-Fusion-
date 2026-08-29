const host = window.location.hostname;
export const API_ROOT = import.meta.env.VITE_API_ROOT || `${window.location.protocol}//${host}:8000`;
export const API = `${API_ROOT}/api/v1`;

async function json(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error((await res.text()) || `HTTP ${res.status}`);
  return res.status === 204 ? null : res.json();
}
export const health = () => json(`${API}/health`);
export const createSample = (fruit_type = "Banana") => json(`${API}/samples`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({fruit_type})});
export const listSamples = () => json(`${API}/samples?limit=20`);
export const bundle = (id) => json(`${API}/samples/${id}/bundle`);
export const fuse = (id) => json(`${API}/samples/${id}/fusion`, {method:"POST"});
export const pushReading = (payload) => json(`${API}/sensors/readings`, {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload)});
export const uploadImage = (sampleId, angle, file) => { const fd = new FormData(); fd.append("sample_id", sampleId); fd.append("angle", angle); fd.append("file", file); return json(`${API}/images/upload`, {method:"POST", body:fd}); };
export const context = (fruit, lat, lon) => json(`${API}/external/context?fruit_type=${encodeURIComponent(fruit)}${lat != null ? `&lat=${lat}&lon=${lon}` : ""}`);
export const wsUrl = (id) => `${window.location.protocol === "https:" ? "wss" : "ws"}://${host}:8000/ws/live/${id}`;
