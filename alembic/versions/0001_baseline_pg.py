"""baseline postgres schema (matches SQL_migration_DB.sql)

Revision ID: 0001_baseline_pg
Revises:
Create Date: 2026-04-29 00:00:00.000000

This migration recreates the schema defined in `SQL_migration_DB.sql`.
It is intended as the single baseline for PostgreSQL deployments. The DB
container bootstraps the schema directly from the SQL file via
`/docker-entrypoint-initdb.d/`, so in normal operation Alembic just stamps
this revision as `head` (alembic stamp head). For local dev or migrations,
running `alembic upgrade head` will create the same schema.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_baseline_pg"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the full PlumID schema on PostgreSQL."""
    # --- species --------------------------------------------------------
    op.create_table(
        "species",
        sa.Column("idspecies", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("sex", sa.CHAR(length=1), nullable=True),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("environment", sa.String(length=100), nullable=True),
        sa.Column("information", sa.Text(), nullable=True),
        sa.Column("species_name", sa.String(length=100), nullable=True),
        sa.Column("species_url_picture", sa.Text(), nullable=True),
        sa.UniqueConstraint("species_name", name="uq_species_species_name"),
    )

    # --- feathers -------------------------------------------------------
    op.create_table(
        "feathers",
        sa.Column("idfeathers", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("side", sa.String(length=45), nullable=True),
        sa.Column("type", sa.String(length=45), nullable=True),
        sa.Column("body_zone", sa.String(length=45), nullable=True),
        sa.Column("species_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["species_id"],
            ["species.idspecies"],
            name="fk_feathers_species",
            ondelete="CASCADE",
        ),
    )
    op.create_index("idx_feathers_species", "feathers", ["species_id"])

    # --- pictures -------------------------------------------------------
    op.create_table(
        "pictures",
        sa.Column("idpictures", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("date_collected", sa.Date(), nullable=True),
        sa.Column("feathers_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["feathers_id"],
            ["feathers.idfeathers"],
            name="fk_pictures_feathers",
            ondelete="CASCADE",
        ),
    )
    op.create_index("idx_pictures_feathers", "pictures", ["feathers_id"])

    # --- users ----------------------------------------------------------
    op.create_table(
        "users",
        sa.Column("idusers", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=True),
        sa.Column("mail", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
        sa.Column("username", sa.String(length=100), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
        sa.Column("email_verified_at", sa.DateTime(), nullable=True),
        sa.Column(
            "is_verified",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column("pictures_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ["pictures_id"],
            ["pictures.idpictures"],
            name="fk_users_pictures",
            ondelete="SET NULL",
        ),
        sa.UniqueConstraint("mail", name="uniq_users_mail"),
    )


def downgrade() -> None:
    """Drop the entire PlumID schema (reverse order of creation)."""
    op.drop_table("users")
    op.drop_index("idx_pictures_feathers", table_name="pictures")
    op.drop_table("pictures")
    op.drop_index("idx_feathers_species", table_name="feathers")
    op.drop_table("feathers")
    op.drop_table("species")
