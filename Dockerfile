# ==============================================================================
# Backend Dockerfile - FastAPI + Dual-Store LTM (SQLite + ChromaDB)
# ==============================================================================

FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH="/app:/app/app" \
    DATABASE_PATH="/app/data/chatbot.db" \
    CHROMA_PATH="/app/data/chroma_db"

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first for caching efficiency
COPY requirement.txt .
RUN pip install --no-cache-dir -r requirement.txt

# Copy application and API code
COPY app/ /app/app/
COPY api/ /app/api/

# Create persistent data directory for SQLite & ChromaDB
RUN mkdir -p /app/data

# Expose API port
EXPOSE 8000

# Container healthcheck
HEALTHCHECK --interval=15s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start FastAPI application with Uvicorn
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
