import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Import the initialized FastAPI app from backend.server
from server import app
import uvicorn

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    print("\n" + "="*60)
    print("🚀 AI REPOSITORY ANALYZER - EXECUTIVE WEB SERVER LAUNCHED")
    print(f"📍 Local UI Dashboard: http://0.0.0.0:{port}")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
