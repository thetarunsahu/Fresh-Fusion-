import os
import socket
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .api import external, images, samples, sensors
from .config import CORS_ORIGINS, UPLOAD_DIR
from .database import Base, engine
from .realtime import manager

Base.metadata.create_all(bind=engine)
app = FastAPI(
    title="FreshFusion API",
    version="2.2.0",
    description="Multimodal fruit intelligence backend for ESP32 telemetry, continuous phone vision, computer vision and fusion scoring.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_ORIGINS != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.include_router(samples.router, prefix="/api/v1")
app.include_router(sensors.router, prefix="/api/v1")
app.include_router(images.router, prefix="/api/v1")
app.include_router(external.router, prefix="/api/v1")


def _lan_ip() -> str:
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("8.8.8.8", 80))
        value = probe.getsockname()[0]
        probe.close()
        return value
    except Exception:
        return "127.0.0.1"


@app.get("/api/v1/health")
def health():
    lan_ip = _lan_ip()
    public_phone_url = os.getenv("PHONE_DASHBOARD_URL", "").strip()
    if public_phone_url:
        phone_dashboard = public_phone_url
        phone_mode = "trusted-https-tunnel" if public_phone_url.startswith("https://") else "configured"
        camera_secure = public_phone_url.startswith("https://")
    else:
        phone_dashboard = f"http://{lan_ip}:5173/phone.html"
        phone_mode = "lan-fallback"
        camera_secure = False

    return {
        "status": "online",
        "service": "FreshFusion",
        "version": "2.2.0",
        "lan_ip": lan_ip,
        "phone_dashboard": phone_dashboard,
        "phone_mode": phone_mode,
        "camera_secure": camera_secure,
        "esp32_endpoint": f"http://{lan_ip}:8000/api/v1/sensors/readings",
    }


@app.websocket("/ws/live/{sample_id}")
async def live(websocket: WebSocket, sample_id: str):
    await manager.connect(sample_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(sample_id, websocket)
