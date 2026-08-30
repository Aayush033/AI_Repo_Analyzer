import os
from pathlib import Path
from dotenv import load_dotenv

# Base Directory paths
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent

# Load .env from backend or root
if (BACKEND_DIR / ".env").exists():
    load_dotenv(BACKEND_DIR / ".env")
elif (PROJECT_ROOT / ".env").exists():
    load_dotenv(PROJECT_ROOT / ".env")
else:
    load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
DATA_DIR = PROJECT_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_FILE = PROJECT_ROOT / ".analyzer_history.json"
MEMORY_FILE = PROJECT_ROOT / "memory.json"