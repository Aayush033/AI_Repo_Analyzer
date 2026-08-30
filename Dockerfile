# ============================================================
# AI Repository Analyzer - Production Dockerfile
# FastAPI + Multi-Agent Pipeline + Gemini AI
# ============================================================

FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    PORT=8000

# Install system dependencies (git is required for repo cloning)
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies first (for Docker layer caching)
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy full project
COPY backend/ ./backend/
COPY static/ ./static/
COPY server.py ./server.py

# Expose port
EXPOSE 8000

# Run using the root launcher (which sets up sys.path and starts uvicorn)
CMD ["python", "server.py"]