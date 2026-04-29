# Database Migrations (Alembic)

Plum'ID uses [Alembic](https://alembic.sqlalchemy.org/) to manage the
PostgreSQL schema and seed data. Migrations run **automatically at
container startup** via `entrypoint.sh` → `scripts/run_migrations.py`.

## TL;DR for Railway

You don't have to do anything manually. On every deploy:

1. The container waits for the database to accept connections.
2. `scripts/run_migrations.py` runs:
   - **Fresh DB** → applies the full chain (baseline + every revision).
   - **Pre-existing DB without `alembic_version`** → stamps the baseline
     as already applied, then runs only the newer revisions.
   - **Already at head** → no-op.
3. `uvicorn` starts.

To make this work on Railway, set **one extra variable** on the
`plumid-api` service the first time:

```
MIGRATIONS_DATABASE_URL=postgresql+psycopg2://postgres:<password>@<host>:5432/<db>
```

This URL must point to a Postgres role with `CREATE` privileges on the
`public` schema (typically the `postgres` superuser created by
Railway's Postgres plugin). The application role `plumid_app` cannot
create the `alembic_version` table, so trying to run migrations as
that role would fail.

The application **runtime** still uses `DATABASE_URL` (which can stay
as the restricted `plumid_app` account). `MIGRATIONS_DATABASE_URL` is
read only during the migration step.

If you don't want to set both, you can put the superuser DSN in
`DATABASE_URL` and skip `MIGRATIONS_DATABASE_URL` — Alembic will fall
back to it.

## Toggles

| Variable | Default | Purpose |
| --- | --- | --- |
| `RUN_MIGRATIONS` | `1` | Set to `0` to skip migrations on a given boot. |
| `WAIT_FOR_DB` | `1` | Set to `0` to skip the connectivity probe. |
| `WAIT_FOR_DB_TIMEOUT` | `60` | Seconds to wait before aborting the boot. |

## Local commands

Inspect the current state without touching anything:

```bash
python scripts/run_migrations.py --check-only
```

Apply pending migrations:

```bash
python scripts/run_migrations.py
```

Or use Alembic directly:

```bash
alembic current                     # what revision is the DB at?
alembic history --verbose           # full revision graph
alembic upgrade head                # apply pending migrations
alembic downgrade -1                # roll back one revision
alembic revision -m "add_X_to_Y"    # create a new revision skeleton
```

## Adding a new migration

1. Create a revision file in `alembic/versions/`. The naming convention
   is `NNNN_short_description.py` (e.g. `0003_add_geolocation_index.py`).
   You can either hand-edit a copy of an existing file or run
   `alembic revision -m "..."` — the autogenerate (`--autogenerate`)
   flag works once the DB is in sync with the SQLAlchemy models.
2. Set `down_revision` to the previous revision's ID.
3. Implement `upgrade()` and `downgrade()`. Use `op.execute(...)` for
   raw SQL or the typed Alembic helpers (`op.add_column`,
   `op.create_table`, …) for portability.
4. Test locally against SQLite (`DATABASE_URL=sqlite:////tmp/test.db
   python scripts/run_migrations.py`) and against a real Postgres
   instance.
5. Push. The next deploy applies the migration automatically.

## Existing revisions

| Revision | Description |
| --- | --- |
| `0001_baseline_pg` | Schema baseline matching `SQL_migration_DB.sql` (tables `species`, `feathers`, `pictures`, `users` + indexes + FKs). |
| `0002_add_non_identifie` | Inserts `species` row with `idspecies = 0` ("Non identifié") used by the model fallback when it returns `Non_plumes`. |

## What if migrations fail?

The container exits with code 1 and Railway will retry per the
restart policy. Look at the deploy logs:

```
⟡ Running database migrations
...
⟡ Migrations FAILED — see traceback above
```

The most common causes:

- **`MIGRATIONS_DATABASE_URL` not set** and the application role can't
  create tables → set the variable to a superuser DSN.
- **Network blip while the DB was restarting** → bump
  `WAIT_FOR_DB_TIMEOUT`.
- **A revision contains broken SQL** → fix and redeploy. The
  `alembic_version` row only updates on successful runs, so the
  half-applied revision will be retried on the next boot.
