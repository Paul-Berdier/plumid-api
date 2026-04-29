# =====================================================================
# PlumID — API container (FastAPI + SQLAlchemy + PostgreSQL)
# ---------------------------------------------------------------------
# Build:
#   docker build -t plumid-api:latest .
#
# Run (locally):
#   docker run --rm -p 8000:8000 \
#     -e DATABASE_URL=postgresql+psycopg2://plumid_app:AppUser123!@host.docker.internal:5432/plumid \
#     plumid-api:latest
#
# Railway: detects the Dockerfile automatically. Set DATABASE_URL,
# MODEL_SERVICE_URL, AUTH_SECRET, and friends in the service variables.
# Railway also injects $PORT — the entrypoint honours it.
# =====================================================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# System deps:
#   - build-essential, libssl-dev, libffi-dev → cryptography / passlib
#   - libpq-dev → psycopg2 (PostgreSQL client lib)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libssl-dev \
        libffi-dev \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps first for better layer caching.
COPY requirements.txt ./requirements.txt
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application source.
COPY . /app

# Drop privileges.
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Honour Railway's $PORT if provided, otherwise default to 8000.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
