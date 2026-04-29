from __future__ import annotations

from sqlalchemy import Column, Integer, String, Text
from models.base import Base


class Species(Base):
    """
    Species model representing the 'species' table.
    Matches the schema defined in SQL_migration_DB.sql.

    SQL definition:
        idspecies            SERIAL PRIMARY KEY
        sex                  CHAR(1)
        region               VARCHAR(100)
        environment          VARCHAR(100)
        information          TEXT
        species_name         VARCHAR(100) UNIQUE
        species_url_picture  TEXT
    """
    __tablename__ = "species"

    idspecies = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sex = Column(String(1), nullable=True)
    region = Column(String(100), nullable=True)
    environment = Column(String(100), nullable=True)
    information = Column(Text, nullable=True)
    species_name = Column(String(100), unique=True, nullable=True)
    species_url_picture = Column(Text, nullable=True)
