# Phone + ESP32 local-network setup

FreshFusion is designed so the laptop runs the backend/dashboard while a phone captures fruit images and ESP32 streams telemetry over the same Wi-Fi.

1. Find laptop IPv4 address (`ipconfig` on Windows), e.g. `192.168.1.10`.
2. Backend: `cd backend` then `uvicorn app.main:app --host 0.0.0.0 --reload`.
3. Frontend: `cd frontend` then `npm run dev -- --host 0.0.0.0`.
4. On the phone, open `http://LAPTOP_IP:5173` while connected to the same Wi-Fi, or scan the dashboard QR code.
5. The frontend automatically targets `http://LAPTOP_IP:8000`, so phone image uploads reach the laptop backend.
6. In `esp32/freshfusion_node.ino`, set Wi-Fi credentials and the laptop IP in `API_URL`.
7. Create/select a fruit sample on the dashboard. The ESP32 no longer needs a hard-coded sample ID: telemetry without `sample_id` is automatically attached to the newest sample. A specific integration can still POST an explicit `sample_id`.
8. Use **Capture / upload image** on phone. The HTML camera hint `capture="environment"` opens the rear camera on compatible mobile browsers.

For internet deployment, put uploads in object storage and use PostgreSQL. SQLite/local uploads are intended for prototype development.
