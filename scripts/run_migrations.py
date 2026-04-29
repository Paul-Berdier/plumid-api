"""
scripts/run_migrations.py
--------------------------

Idempotent Alembic runner invoked at container startup. Handles three
real-world scenarios on Railway / docker-compose without requiring any
manual steps:

1. **Fresh database** — no tables exist yet.
   → Run `alembic upgrade head`. The baseline (`0001_baseline_pg`)
     creates the schema, then any subsequent revisions (`0002_…`,
     `0003_…`) apply on top.

2. **Pre-existing database, never touched by Alembic** — tables exist
   (e.g. they were created by an init SQL script or by an earlier
   manual run), but `alembic_version` is missing.
   → Stamp the baseline as already applied, then upgrade. This avoids
     `CREATE TABLE` running against existing tables and crashing.

3. **Database already at head** — `alembic_version` row matches `head`.
   → No-op. Safe to call on every boot.

The script writes its own logs (stdout) so the operator can see what
happened in the deploy logs.

It connects via:
  - `MIGRATIONS_DATABASE_URL` if set (recommended; should point to a
    superuser / DDL-capable account such as `postgres` rather than the
    application role `plumid_app` which lacks CREATE on `public`).
  - Falls back to `DATABASE_URL` otherwise (works when the application
    role does have CREATE — typical in dev / single-role setups).

Usage
-----
    python scripts/run_migrations.py                # auto mode (default)
    python scripts/run_migrations.py --skip         # skip migrations
    python scripts/run_migrations.py --check-only   # just print state

Exit codes
----------
    0  success (or skipped)
    1  migration error
    2  configuration error
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from typing import Optional

# Make the project importable when invoked from the project root.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from alembic.runtime.migration import MigrationContext  # noqa: E402
from alembic.script import ScriptDirectory  # noqa: E402
from sqlalchemy import create_engine, inspect, text  # noqa: E402
from sqlalchemy.engine import Engine  # noqa: E402

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO").upper(),
    format="%(asctime)s %(levelname)s [migrations] %(message)s",
)
log = logging.getLogger("migrations")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALEMBIC_INI = os.path.join(PROJECT_ROOT, "alembic.ini")

# Tables that the baseline migration creates. If they all exist before
# Alembic has stamped anything, we know we're in scenario 2 and need to
# stamp the baseline before upgrading.
BASELINE_TABLES = {"species", "feathers", "pictures", "users"}


def _resolve_database_url() -> str:
    """
    Pick the URL Alembic should use. Prefers MIGRATIONS_DATABASE_URL
    (DDL-capable, e.g. the postgres superuser) so `CREATE TABLE
    alembic_version` works the first time. Falls back to DATABASE_URL.
    """
    url = (os.environ.get("MIGRATIONS_DATABASE_URL") or "").strip()
    if url:
        log.info("Using MIGRATIONS_DATABASE_URL")
    else:
        url = (os.environ.get("DATABASE_URL") or "").strip()
        if url:
            log.info(
                "MIGRATIONS_DATABASE_URL not set — falling back to DATABASE_URL "
                "(make sure this role has CREATE on `public`)"
            )
        else:
            log.error("Neither MIGRATIONS_DATABASE_URL nor DATABASE_URL is set")
            sys.exit(2)

    # Normalise Heroku/Railway-style scheme so SQLAlchemy + psycopg2 are happy.
    if url.startswith("postgres://"):
        url = "postgresql+psycopg2://" + url[len("postgres://"):]
    elif url.startswith("postgresql://") and "+psycopg2" not in url and "+psycopg" not in url:
        url = "postgresql+psycopg2://" + url[len("postgresql://"):]
    return url


def _alembic_config(url: str) -> Config:
    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("script_location", os.path.join(PROJECT_ROOT, "alembic"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def _current_revision(engine: Engine) -> Optional[str]:
    """Return the alembic_version row, or None if the table doesn't exist."""
    with engine.connect() as cx:
        ctx = MigrationContext.configure(cx)
        return ctx.get_current_revision()


def _alembic_table_exists(engine: Engine) -> bool:
    insp = inspect(engine)
    return insp.has_table("alembic_version")


def _baseline_tables_exist(engine: Engine) -> bool:
    insp = inspect(engine)
    existing = set(insp.get_table_names())
    return BASELINE_TABLES.issubset(existing)


def _head_revision(cfg: Config) -> str:
    return ScriptDirectory.from_config(cfg).get_current_head() or ""


def _check_only(engine: Engine, cfg: Config) -> int:
    """Print the diagnostic without changing anything."""
    head = _head_revision(cfg)
    has_alembic = _alembic_table_exists(engine)
    has_tables = _baseline_tables_exist(engine)
    current = _current_revision(engine) if has_alembic else None

    log.info("=== Migration state ===")
    log.info("  alembic_version table: %s", "yes" if has_alembic else "no")
    log.info("  baseline tables present: %s", "yes" if has_tables else "no")
    log.info("  current revision: %s", current or "(none)")
    log.info("  head revision: %s", head)

    if has_alembic and current == head:
        log.info("  → up to date")
    elif has_alembic and current != head:
        log.info("  → upgrade needed: %s -> %s", current, head)
    elif has_tables and not has_alembic:
        log.info("  → pre-existing schema; will stamp baseline + upgrade")
    else:
        log.info("  → fresh DB; will run full upgrade from scratch")
    return 0


def _run(engine: Engine, cfg: Config) -> int:
    head = _head_revision(cfg)
    if not head:
        log.error("No Alembic head found — is `alembic/versions/` empty?")
        return 1

    has_alembic = _alembic_table_exists(engine)
    has_tables = _baseline_tables_exist(engine)
    current = _current_revision(engine) if has_alembic else None

    log.info(
        "DB state: alembic_version=%s baseline_tables=%s current=%s head=%s",
        has_alembic, has_tables, current, head,
    )

    # Scenario 3 — already at head.
    if has_alembic and current == head:
        log.info("Database is already at head (%s); nothing to do", head)
        return 0

    # Scenario 2 — schema exists, never stamped.
    if has_tables and not has_alembic:
        # Stamp the baseline only. Then upgrade for any 0002+ revisions.
        baseline = "0001_baseline_pg"
        log.info(
            "Pre-existing schema detected; stamping baseline %s", baseline
        )
        try:
            command.stamp(cfg, baseline)
        except Exception as exc:  # noqa: BLE001
            log.exception("Stamp failed: %s", exc)
            return 1

    # Scenarios 1 + the post-stamp continuation of scenario 2.
    log.info("Running alembic upgrade head")
    try:
        command.upgrade(cfg, "head")
    except Exception as exc:  # noqa: BLE001
        log.exception("Upgrade failed: %s", exc)
        return 1

    new_current = _current_revision(engine)
    log.info("Migrations OK; database is at %s", new_current)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Plum'ID migration runner")
    parser.add_argument(
        "--skip",
        action="store_true",
        help="Skip migrations entirely (useful when RUN_MIGRATIONS=0)",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Print diagnostic info without changing the database",
    )
    args = parser.parse_args()

    if args.skip or os.environ.get("RUN_MIGRATIONS", "1") in {"0", "false", "False"}:
        log.info("Migrations skipped (RUN_MIGRATIONS=0)")
        return 0

    url = _resolve_database_url()
    engine = create_engine(url, pool_pre_ping=True)

    # Quick connectivity probe — clearer error than a stack trace.
    try:
        with engine.connect() as cx:
            cx.execute(text("SELECT 1"))
    except Exception as exc:  # noqa: BLE001
        log.error("Cannot reach database: %s", exc)
        return 1

    cfg = _alembic_config(url)

    if args.check_only:
        return _check_only(engine, cfg)
    return _run(engine, cfg)


if __name__ == "__main__":
    sys.exit(main())
