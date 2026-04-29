"""add non-identifié species (id=0) used by model fallback

Revision ID: 0002_add_non_identifie
Revises: 0001_baseline_pg
Create Date: 2026-04-29 00:00:00.000000

The model service may return the `Non_plumes` class when it cannot
identify a feather. The inference layer (plumid-model) maps that
label to species_id=0, so the API needs a corresponding row in the
`species` table.

This migration is idempotent (uses ON CONFLICT on PostgreSQL,
INSERT OR IGNORE on SQLite) and safe to re-run.
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0002_add_non_identifie"
down_revision: Union[str, Sequence[str], None] = "0001_baseline_pg"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Insert the reserved id=0 'Non identifié' row."""
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        # ON CONFLICT (idspecies) is the idiomatic Postgres idempotent insert.
        op.execute(
            """
            INSERT INTO species (
                idspecies, sex, region, environment, information,
                species_name, species_url_picture
            )
            VALUES (
                0, NULL, NULL, NULL,
                'Espèce non identifiée par le modèle.',
                'Non identifié',
                NULL
            )
            ON CONFLICT (idspecies) DO NOTHING
            """
        )

        # Re-align the SERIAL sequence so subsequent INSERTs don't try
        # to reuse id=0. Only meaningful on Postgres.
        op.execute(
            """
            SELECT setval(
                pg_get_serial_sequence('species', 'idspecies'),
                GREATEST((SELECT MAX(idspecies) FROM species), 1),
                true
            )
            """
        )

    elif dialect == "sqlite":
        # SQLite doesn't have ON CONFLICT (idspecies) DO NOTHING in
        # older versions — INSERT OR IGNORE is the portable form.
        op.execute(
            """
            INSERT OR IGNORE INTO species (
                idspecies, sex, region, environment, information,
                species_name, species_url_picture
            )
            VALUES (
                0, NULL, NULL, NULL,
                'Espèce non identifiée par le modèle.',
                'Non identifié',
                NULL
            )
            """
        )
        # No sequence re-alignment on SQLite — AUTOINCREMENT logic is
        # different and tests don't care about ID collisions.

    else:
        # MySQL / others — best-effort idempotent INSERT. The unit tests
        # use SQLite and prod uses Postgres, so this branch is just a
        # safety net.
        op.execute(
            """
            INSERT IGNORE INTO species (
                idspecies, sex, region, environment, information,
                species_name, species_url_picture
            )
            VALUES (
                0, NULL, NULL, NULL,
                'Espèce non identifiée par le modèle.',
                'Non identifié',
                NULL
            )
            """
        )


def downgrade() -> None:
    """Remove the id=0 row."""
    op.execute("DELETE FROM species WHERE idspecies = 0")
