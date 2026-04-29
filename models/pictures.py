from __future__ import annotations

from sqlalchemy import Column, Integer, Date, ForeignKey, Index, Numeric, Text
from sqlalchemy.orm import relationship
from models.base import Base


class Pictures(Base):
    """
    Pictures model representing the 'pictures' table.
    Matches the schema defined in SQL_migration_DB.sql.

    SQL definition:
        idpictures      SERIAL PRIMARY KEY
        url             TEXT
        longitude       NUMERIC(9,6)
        latitude        NUMERIC(9,6)
        date_collected  DATE
        feathers_id     INT REFERENCES feathers(idfeathers) ON DELETE CASCADE

    Note: in this schema, pictures DO NOT belong to a user.
    Instead, users have an optional `pictures_id` (avatar/profile picture)
    referencing this table.
    """
    __tablename__ = "pictures"

    idpictures = Column(Integer, primary_key=True, index=True, autoincrement=True)
    url = Column(Text, nullable=True)
    longitude = Column(Numeric(9, 6), nullable=True)
    latitude = Column(Numeric(9, 6), nullable=True)
    date_collected = Column(Date, nullable=True)

    feathers_id = Column(
        Integer,
        ForeignKey("feathers.idfeathers", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    feathers = relationship("Feathers", backref="pictures", lazy="joined")


Index("idx_pictures_feathers", Pictures.feathers_id)
