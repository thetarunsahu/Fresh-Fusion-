from collections import defaultdict
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.connections: dict[str, set[WebSocket]] = defaultdict(set)

    async def connect(self, sample_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections[sample_id].add(websocket)

    def disconnect(self, sample_id: str, websocket: WebSocket):
        self.connections[sample_id].discard(websocket)

    async def broadcast(self, sample_id: str, payload: dict):
        stale = []
        for socket in list(self.connections[sample_id]):
            try:
                await socket.send_json(payload)
            except Exception:
                stale.append(socket)
        for socket in stale:
            self.disconnect(sample_id, socket)

manager = ConnectionManager()
