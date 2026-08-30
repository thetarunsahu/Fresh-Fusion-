export const API_ROOT = import.meta.env.VITE_API_ROOT || window.location.origin;
export const API = `${API_ROOT}/api/v1`;

async function json(url, options = {}) {
  const res = await fetch(url, options);
  if (!res.ok) throw new Error((await res.text()) || `HTTP ${res.status}`);
  return res.status === 204 ? null : res.json();
}

export const health = () => json(`${API}/health`);
export const createSample = (fruit_type = 'Banana') => json(`${API}/samples`, {
  method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({fruit_type})
});
export const listSamples = () => json(`${API}/samples?limit=20`);
export const bundle = id => json(`${API}/samples/${id}/bundle`);
export const fuse = id => json(`${API}/samples/${id}/fusion`, {method:'POST'});
export const pushReading = payload => json(`${API}/sensors/readings`, {
  method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)
});

function imageForm(sampleId, angle, truth, file) {
  const fd = new FormData();
  fd.append('sample_id', sampleId);
  fd.append('angle', angle);
  if (truth) fd.append('ground_truth', truth);
  fd.append('file', file, file.name || `frame-${Date.now()}.jpg`);
  return fd;
}

export const uploadImage = (sampleId, angle, truth, file) => json(`${API}/images/upload`, {
  method:'POST', body:imageForm(sampleId, angle, truth, file)
});

export const uploadStreamFrame = (sampleId, view, truth, file) => {
  const fd = imageForm(sampleId, `live-${view}`, truth, file);
  fd.append('view', view);
  return json(`${API}/images/stream-frame`, {method:'POST', body:fd});
};

export const context = (fruit, lat, lon) => json(`${API}/external/context?fruit_type=${encodeURIComponent(fruit)}${lat != null ? `&lat=${lat}&lon=${lon}` : ''}`);

export const wsUrl = id => {
  const base = new URL(API_ROOT, window.location.origin);
  const protocol = base.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${base.host}/ws/live/${id}`;
};
