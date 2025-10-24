"""Dashboard API backend."""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pathlib import Path
import json
from typing import List
from config import settings

# Create dashboard app
dashboard_app = FastAPI(title="OCR Dashboard")

# Setup templates and static files
dashboard_dir = Path(__file__).parent
templates = Jinja2Templates(directory=str(dashboard_dir / "templates"))
dashboard_app.mount("/static", StaticFiles(directory=str(dashboard_dir / "static")), name="static")

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                pass

manager = ConnectionManager()

@dashboard_app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page."""
    return templates.TemplateResponse("index.html", {"request": request})

@dashboard_app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Configuration page."""
    return templates.TemplateResponse("config.html", {"request": request})

@dashboard_app.get("/test", response_class=HTMLResponse)
async def test_page(request: Request):
    """Testing interface page."""
    return templates.TemplateResponse("test.html", {"request": request})

@dashboard_app.get("/agents", response_class=HTMLResponse)
async def agents_page(request: Request):
    """Agent control center page."""
    return templates.TemplateResponse("agents.html", {"request": request})

@dashboard_app.get("/api/config")
async def get_config():
    """Get current configuration."""
    return JSONResponse({
        "ollama_host": settings.ollama_host,
        "ollama_vision_model": settings.ollama_vision_model,
        "ollama_text_model": settings.ollama_text_model,
        "ollama_formatter_model": settings.ollama_formatter_model,
        "enable_autonomous_agents": settings.enable_autonomous_agents,
        "require_approval_for_changes": settings.require_approval_for_changes,
        "max_concurrent_agent_tasks": settings.max_concurrent_agent_tasks,
    })

@dashboard_app.post("/api/config")
async def update_config(config: dict):
    """Update configuration (in-memory for now)."""
    # TODO: Persist configuration changes
    return JSONResponse({"status": "success", "message": "Configuration updated"})

@dashboard_app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time updates."""
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Echo back for now
            await websocket.send_json({"type": "pong", "data": data})
    except WebSocketDisconnect:
        manager.disconnect(websocket)

