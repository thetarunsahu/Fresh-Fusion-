# FreshFusion phone + ESP32 connection

FreshFusion uses the laptop as the processing server, ESP32 as the sensor node, and the phone as a live camera node.

The previous LAN-only approach used a self-signed HTTPS certificate. That can fail on phones because mobile browsers require a trusted secure context for `getUserMedia()`. The recommended prototype workflow now uses a Cloudflare Quick Tunnel for the phone while ESP32 stays on the local network.

## Recommended: one command

From the repository root in PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\start_freshfusion.ps1
```

The launcher automatically:

1. creates/checks the Python virtual environment,
2. checks frontend packages,
3. downloads the official portable `cloudflared.exe` if needed,
4. starts the Vite dashboard on `http://localhost:5173`,
5. creates a trusted `https://...trycloudflare.com` phone URL,
6. starts FastAPI with that phone URL configured,
7. opens the laptop dashboard.

Keep that PowerShell window open while FreshFusion is running.

## Phone workflow

The dashboard QR code points to a dedicated `phone.html` page over trusted HTTPS. The phone does not need to be on the same Wi-Fi as the laptop because the HTTPS tunnel is outbound from the laptop.

On the phone:

1. scan the dashboard QR,
2. allow Camera when prompted,
3. if the browser does not auto-start the camera, tap **Start camera** once,
4. choose Front / Back / Left / Right / Top while moving around the fruit,
5. frames are uploaded automatically every 2.5 seconds by default.

The phone page follows the newest active fruit sample on the laptop, so phone images and ESP32 telemetry stay attached to the same sample.

## ESP32 workflow

ESP32 still communicates directly with FastAPI over the local Wi-Fi. The launcher prints the exact endpoint, for example:

```text
http://192.168.1.10:8000/api/v1/sensors/readings
```

Set that URL plus Wi-Fi SSID/password in `esp32/freshfusion_node.ino`.

If ESP32 cannot reach the laptop but the phone works, allow Python/FastAPI through Windows Firewall on **Private networks** and confirm the laptop IP with `ipconfig`.

## Why the phone path is separate

The desktop dashboard stays focused on analysis. The phone opens a dedicated camera interface instead of loading the full desktop UI. This improves camera reliability and makes the scan flow clear on a small screen.

## Continuous vision storage

The backend keeps a rolling buffer of live frames instead of storing unlimited video frames. Each accepted frame is analysed, fused with recent sensor telemetry and broadcast through WebSocket.

Environment variables:

```text
STREAM_KEEP=24
FUSION_KEEP=200
```

Cloudflare Quick Tunnels are suitable for development and demos, not a production SLA. For a final deployed product, use a stable HTTPS domain and hosted backend/object storage.
