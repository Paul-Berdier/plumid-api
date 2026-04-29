#!/bin/sh
# =====================================================================
# PlumID API — runtime entrypoint
# ---------------------------------------------------------------------
# Boot sequence:
#   1. Resolve $PORT (Railway / Heroku style).
#   2. Wait until the database is reachable (avoids a crash loop on
#      cold boot when the Postgres container is still initialising).
#   3. Run Alembic migrations (idempotent — handles fresh DB,
#      pre-existing schema, and already-migrated DB cases).
#   4. Exec uvicorn.
#
# Toggles
# -------
#   WAIT_FOR_DB=0           Skip step 2 (default 1).
#   RUN_MIGRATIONS=0        Skip step 3 (default 1).
#   MIGRATIONS_DATABASE_URL Optional URL for the migration step. Should
#                           point to a DDL-capable account (e.g. the
#                           Postgres superuser). Defaults to DATABASE_URL.
# =====================================================================
set -e

PORT="${PORT:-8000}"
WAIT_FOR_DB="${WAIT_FOR_DB:-1}"
WAIT_FOR_DB_TIMEOUT="${WAIT_FOR_DB_TIMEOUT:-60}"
RUN_MIGRATIONS="${RUN_MIGRATIONS:-1}"

echo "⟡ PlumID API starting…"
echo "⟡ Binding to PORT=${PORT}"

# ---------------------------------------------------------------------
# 1. Wait for the database to accept connections
# ---------------------------------------------------------------------
if [ "$WAIT_FOR_DB" = "1" ]; then
    echo "⟡ Waiting for database (timeout ${WAIT_FOR_DB_TIMEOUT}s)…"
    python - <<'PYEOF' || { echo "⟡ Database not reachable — aborting"; exit 1; }
import os, sys, time
from sqlalchemy import create_engine, text
sys.path.insert(0, "/app")
from settings import settings  # noqa: E402

deadline = time.time() + int(os.environ.get("WAIT_FOR_DB_TIMEOUT", "60"))
last = None
while time.time() < deadline:
    try:
        with create_engine(settings.db_url, pool_pre_ping=True).connect() as cx:
            cx.execute(text("SELECT 1"))
        print("⟡ Database OK")
        sys.exit(0)
    except Exception as e:
        last = e
        time.sleep(1)
print(f"⟡ Database unreachable: {last}", file=sys.stderr)
sys.exit(1)
PYEOF
else
    echo "⟡ Skipping DB wait (WAIT_FOR_DB=0)"
fi

# ---------------------------------------------------------------------
# 2. Apply database migrations (idempotent)
# ---------------------------------------------------------------------
if [ "$RUN_MIGRATIONS" = "1" ]; then
    echo "⟡ Running database migrations"
    python /app/scripts/run_migrations.py || {
        echo "⟡ Migrations FAILED — see traceback above"
        exit 1
    }
    echo "⟡ Migrations OK"
else
    echo "⟡ Skipping migrations (RUN_MIGRATIONS=0)"
fi

# ---------------------------------------------------------------------
# 3. Hand off to uvicorn
# ---------------------------------------------------------------------
echo "⟡ Handing off to uvicorn"
exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT}"
