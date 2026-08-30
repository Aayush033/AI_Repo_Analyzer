import json
import os
from core.config import MEMORY_FILE

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_memory(data):
    try:
        with open(MEMORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"Memory save error: {e}")

def remember(key, value):
    data = load_memory()
    data[key] = value
    save_memory(data)

def recall(key):
    data = load_memory()
    return data.get(key)