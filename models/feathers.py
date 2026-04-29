from __future__ import annotations

from sqlalchemy import Column, Integer, String, ForeignKey, Index
from sqlalchemy.orm import relationship
from models.base import Base


class Feathers(Base):
    """
    Feathers model representing the 'feathers' table.
    Matches the schema defined in SQL_migration_DB.sql.

    SQL definition:
        idfeathers   SERIAL PRIMARY KEY
        side         VARCHAR(45)
        type         VARCHAR(45)
        body_zone    VARCHAR(45)
        species_id   INT REFERENCES species(idspecies) ON DELETE CASCADE
    """
    __tablename__ = "feathers"

    idfeathers = Column(Integer, primary_key=True, index=True, autoincrement=True)
    side = Column(String(45), nullable=True)
    type = Column(String(45), nullable=True)
    body_zone = Column(String(45), nullable=True)

    species_id = Column(
        Integer,
        ForeignKey("species.idspecies", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    species = relationship("Species", backref="feathers", lazy="joined")


Index("idx_feathers_species", Feathers.species_id)
