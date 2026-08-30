import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Import the initialized FastAPI app from backend.server
from server import app
import uvicorn

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 AI REPOSITORY ANALYZER - EXECUTIVE WEB SERVER LAUNCHED")
    print("📍 Local UI Dashboard: http://localhost:8000")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)
