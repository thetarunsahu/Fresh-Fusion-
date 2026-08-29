# Phone + ESP32 local-network setup

FreshFusion is designed so the laptop runs the backend/dashboard while a phone captures fruit images and ESP32 streams telemetry over the same Wi-Fi.

1. Find laptop IPv4 address (`ipconfig` on Windows), e.g. `192.168.1.10`.
2. Backend: `cd backend` then `uvicorn app.main:app --host 0.0.0.0 --reload`.
3. Frontend: `cd frontend` then `npm run dev -- --host 0.0.0.0`.
4. On the phone, open `http://LAPTOP_IP:5173` while connected to the same Wi-Fi.
5. The frontend automatically targets `http://LAPTOP_IP:8000`, so phone image uploads reach the laptop backend.
6. In `esp32/freshfusion_node.ino`, set the same laptop IP in `API_URL`, Wi-Fi credentials, and the current dashboard `SAMPLE_ID`.
7. Use **Capture / upload image** on phone. The HTML camera hint `capture="environment"` opens the rear camera on compatible mobile browsers.

For internet deployment, put uploads in object storage and use PostgreSQL. SQLite/local uploads are intended for prototype development.
