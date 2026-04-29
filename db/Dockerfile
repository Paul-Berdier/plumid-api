# =====================================================================
# PlumID — Custom PostgreSQL image
# ---------------------------------------------------------------------
# Builds a postgres:16 image preloaded with the PlumID schema + roles
# + seed data (cf. db/initdb/01-schema.sql).
#
# Build:
#   docker build -f db/Dockerfile -t plumid-db:latest db/
#
# Run (locally):
#   docker run --rm --name plumid-db \
#     -e POSTGRES_USER=postgres \
#     -e POSTGRES_PASSWORD=rootpassword \
#     -e POSTGRES_DB=plumid \
#     -p 5432:5432 plumid-db:latest
#
# Railway: deploy this directory as its own service. Provide the env
# vars POSTGRES_USER / POSTGRES_PASSWORD / POSTGRES_DB. On the FIRST
# boot the init script creates schema + roles + seeds.
# =====================================================================

FROM postgres:16-alpine

# Mount the schema file so the official entrypoint runs it on first boot.
COPY initdb/01-schema.sql /docker-entrypoint-initdb.d/01-schema.sql

# Default DB / user — overridden by env at runtime.
ENV POSTGRES_DB=plumid \
    POSTGRES_USER=postgres \
    POSTGRES_PASSWORD=rootpassword

EXPOSE 5432
