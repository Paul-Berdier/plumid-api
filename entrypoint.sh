#!/bin/sh
# =====================================================================
# PlumID API — runtime entrypoint
# ---------------------------------------------------------------------
# Resolves the listening port from $PORT (Railway / Heroku style),
# falling back to 8000. Uses Python directly to avoid every shell-vs-exec
# quirk with platform start-command overrides.
# =====================================================================
set -e

PORT="${PORT:-8000}"

echo "[plumid-api] starting uvicorn on 0.0.0.0:${PORT}"
exec python -m uvicorn main:app --host 0.0.0.0 --port "${PORT}"
