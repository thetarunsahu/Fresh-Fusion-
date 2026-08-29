import socket
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .api import external, images, samples, sensors
from .config import CORS_ORIGINS, UPLOAD_DIR
from .database import Base, engine
from .realtime import manager

Base.metadata.create_all(bind=engine)
app = FastAPI(title="FreshFusion API", version="2.0.0", description="Multimodal fruit intelligence backend for ESP32 telemetry, phone image capture, computer vision and fusion scoring.")
app.add_middleware(CORSMiddleware, allow_origins=CORS_ORIGINS, allow_credentials=CORS_ORIGINS != ["*"], allow_methods=["*"], allow_headers=["*"])
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.include_router(samples.router, prefix="/api/v1")
app.include_router(sensors.router, prefix="/api/v1")
app.include_router(images.router, prefix="/api/v1")
app.include_router(external.router, prefix="/api/v1")

@app.get("/api/v1/health")
def health():
    try:
        probe = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        probe.connect(("8.8.8.8", 80))
        lan_ip = probe.getsockname()[0]
        probe.close()
    except Exception:
        lan_ip = "127.0.0.1"
    return {"status": "online", "service": "FreshFusion", "version": "2.0.0", "lan_ip": lan_ip, "phone_dashboard": f"http://{lan_ip}:5173"}

@app.websocket("/ws/live/{sample_id}")
async def live(websocket: WebSocket, sample_id: str):
    await manager.connect(sample_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(sample_id, websocket)
