import sys
import os
import warnings
import logging
from pathlib import Path

warnings.filterwarnings("ignore")
logging.getLogger("google").setLevel(logging.ERROR)
logging.getLogger("google.genai").setLevel(logging.ERROR)

class WarningFilterStderr:
    def __init__(self, original_stderr):
        self.original_stderr = original_stderr

    def write(self, s):
        if "automatic function calling" in s or "AFC" in s or "Models.generate_content" in s:
            return
        if self.original_stderr:
            self.original_stderr.write(s)

    def flush(self):
        if self.original_stderr and hasattr(self.original_stderr, "flush"):
            self.original_stderr.flush()

    def isatty(self):
        return getattr(self.original_stderr, "isatty", lambda: False)()

if not isinstance(sys.stderr, WarningFilterStderr):
    sys.stderr = WarningFilterStderr(sys.stderr)

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = CURRENT_FILE.parent if CURRENT_FILE.parent.name == "backend" else CURRENT_FILE.parent / "backend"
PROJECT_ROOT = BACKEND_DIR.parent if CURRENT_FILE.parent.name == "backend" else CURRENT_FILE.parent

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import uuid
import datetime
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from core.graph import run_workflow
from core.config import HISTORY_FILE

app = FastAPI(title="AI Repository Analyzer API", version="2.0.0")

STATIC_DIR = PROJECT_ROOT / "static"
if not STATIC_DIR.exists():
    STATIC_DIR = BACKEND_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

def load_history():
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []
    return []

def save_history(history_list):
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history_list, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving history: {e}")

def save_history_item(record: dict):
    history = load_history()
    history.insert(0, record)
    history = history[:30] # Retain latest 30
    save_history(history)

class AuditRequest(BaseModel):
    repo_url: str
    requirement: str = "Comprehensive system profile metric scan"

RunRequest = AuditRequest

class DeleteRequest(BaseModel):
    id: str

class WebSocketLogger:
    def __init__(self, websocket: WebSocket):
        self.ws = websocket

    async def send_json(self, data: dict):
        try:
            await self.ws.send_json(data)
        except Exception:
            pass

WebSocketLogAdapter = WebSocketLogger

@app.get("/favicon.ico")
async def get_favicon():
    return Response(status_code=204)

@app.get("/")
async def get_index():
    index_path = STATIC_DIR / "index.html"
    return FileResponse(
        str(index_path),
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "2.0.0"}

@app.get("/api/history")
async def get_history():
    return load_history()

@app.post("/api/history/delete")
async def delete_history_post(req: DeleteRequest):
    history = load_history()
    target = req.id.strip()
    updated = [
        item for item in history 
        if str(item.get("id")) != target 
        and str(item.get("display_name")) != target 
        and str(item.get("repo_url")) != target
    ]
    save_history(updated)
    return {"status": "deleted", "id": req.id, "remaining": len(updated)}

@app.delete("/api/history/{item_id:path}")
async def delete_history_item(item_id: str):
    history = load_history()
    target = item_id.strip()
    updated = [
        item for item in history 
        if str(item.get("id")) != target 
        and str(item.get("display_name")) != target 
        and str(item.get("repo_url")) != target
    ]
    save_history(updated)
    return {"status": "deleted", "id": item_id, "remaining": len(updated)}

@app.post("/api/run")
async def trigger_audit_http(req: AuditRequest):
    class NullWS:
        async def send_json(self, data: dict):
            pass

    try:
        result = await run_workflow(req.requirement, req.repo_url, NullWS())
        clean_name = req.repo_url.split("github.com/")[-1].replace(".git", "")
        
        record = {
            "id": str(uuid.uuid4()),
            "display_name": clean_name,
            "jd_input": req.requirement,
            "repo_url": req.repo_url,
            "score": result.get("score", 0),
            "runtime": result.get("runtime", 0.0),
            "time": datetime.datetime.now().strftime("%I:%M %p"),
            "pinned": False,
            "results": result.get("results", []),
            "analytics_data": result.get("analytics_data", {}),
            "security_findings": result.get("security_findings", []),
            "ast_metrics": result.get("ast_metrics", {}),
            "verification_data": result.get("verification_data", {}),
            "jd_match_data": result.get("jd_match_data", {}),
            "executive_report": result.get("executive_report", ""),
            "mermaid_diagram": result.get("mermaid_diagram", "")
        }
        history = load_history()
        history.insert(0, record)
        save_history(history)
        return record
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.websocket("/ws/audit")
async def websocket_audit_endpoint(websocket: WebSocket):
    await websocket.accept()
    log_adapter = WebSocketLogAdapter(websocket)
    try:
        data = await websocket.receive_json()
        repo_url = data.get("repo_url", "").strip()
        requirement = data.get("requirement", "Comprehensive system profile metric scan").strip()

        if not repo_url:
            await websocket.send_json({"type": "error", "msg": "No repository URL provided."})
            return

        result = await run_workflow(requirement, repo_url, log_adapter)
        clean_name = repo_url.split("github.com/")[-1].replace(".git", "")

        record = {
            "id": str(uuid.uuid4()),
            "display_name": clean_name,
            "jd_input": requirement,
            "repo_url": repo_url,
            "score": result.get("score", 0),
            "runtime": result.get("runtime", 0.0),
            "time": datetime.datetime.now().strftime("%I:%M %p"),
            "pinned": False,
            "results": result.get("results", []),
            "analytics_data": result.get("analytics_data", {}),
            "security_findings": result.get("security_findings", []),
            "ast_metrics": result.get("ast_metrics", {}),
            "verification_data": result.get("verification_data", {}),
            "jd_match_data": result.get("jd_match_data", {}),
            "executive_report": result.get("executive_report", ""),
            "mermaid_diagram": result.get("mermaid_diagram", "")
        }

        history = load_history()
        history.insert(0, record)
        save_history(history)

        await websocket.send_json({
            "type": "result",
            "payload": record
        })

    except WebSocketDisconnect:
        print("[WS] Client disconnected")
    except Exception as e:
        print(f"[WS ERROR] {e}")
        try:
            await websocket.send_json({"type": "error", "msg": str(e)})
        except Exception:
            pass

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 AI REPOSITORY ANALYZER - EXECUTIVE WEB SERVER LAUNCHED")
    print("📍 Local UI Dashboard: http://localhost:8000")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
