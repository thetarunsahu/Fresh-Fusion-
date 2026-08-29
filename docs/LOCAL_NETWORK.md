# FreshFusion local phone + ESP32 mode

FreshFusion now treats the laptop as the processing server, the ESP32 as a continuous sensor node, and the phone as a continuous vision node.

## 1. Backend

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --reload
```

## 2. HTTPS dashboard

The phone camera API requires a secure context. The Vite development server uses `@vitejs/plugin-basic-ssl` and proxies API/WebSocket/upload traffic to the FastAPI backend.

```powershell
cd frontend
npm install
npm run dev
```

Open the HTTPS network URL printed by Vite, for example `https://192.168.1.10:5173`. A development certificate warning may appear. Accept it for local prototype use. On the first visit, the browser asks for camera permission; after permission is granted, supported phones automatically start the rear camera and send JPEG frames every 2.5 seconds by default.

For a production/demo deployment, use a trusted HTTPS domain rather than a development certificate.

## 3. ESP32

In `esp32/freshfusion_node.ino`, set Wi-Fi credentials and the laptop IPv4 address in `API_URL`. The board posts telemetry every few seconds as soon as it boots and joins Wi-Fi. `sample_id` is intentionally omitted; FastAPI automatically attaches incoming telemetry to the newest active fruit sample.

Phone and ESP32 should be able to reach the laptop over the same network.

## 4. Continuous vision storage

The backend keeps a rolling buffer of live frames (`STREAM_KEEP`, default 24) instead of storing an unlimited camera stream. Each accepted live frame is analysed, fused with recent sensor telemetry, broadcast through WebSocket, and displayed on the dashboard.

Environment variables:

```text
STREAM_KEEP=24
FUSION_KEEP=200
```

This keeps the prototype responsive while still preserving enough recent frames for vision trends and debugging.
