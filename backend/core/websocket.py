from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active_connections.add(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self.active_connections:
            self.active_connections.remove(ws)

    async def send_log(self, ws: WebSocket, message: str):
        if ws not in self.active_connections:
            return
        try:
            await ws.send_json({"type": "log", "msg": message})
        except Exception:
            self.disconnect(ws)

manager = ConnectionManager()