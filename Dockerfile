# =====================================================================
# PlumID — API container (FastAPI + SQLAlchemy + PostgreSQL)
# ---------------------------------------------------------------------
# Boot via entrypoint.sh, which:
#   1. Waits for the database
#   2. Runs Alembic migrations (idempotent)
#   3. Execs uvicorn
#
# Railway: detects the Dockerfile automatically. Set DATABASE_URL,
# MIGRATIONS_DATABASE_URL, MODEL_SERVICE_URL, AUTH_SECRET, and friends
# in the service variables. Railway also injects $PORT — the entrypoint
# honours it.
# =====================================================================

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps:
#   - curl                              → healthcheck
#   - libpq-dev                         → psycopg2 (PostgreSQL client lib)
#   - build-essential / libssl / libffi → cryptography / passlib
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
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
RUN chmod +x /app/entrypoint.sh /app/scripts/run_migrations.py

# Drop privileges.
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -fsS http://localhost:8000/health || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
