# api/models/users.py
from __future__ import annotations

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    func,
    Boolean,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from models.base import Base


class Users(Base):
    """
    Users model representing the 'users' table.
    Matches the schema defined in SQL_migration_DB.sql.

    SQL definition:
        idusers           SERIAL PRIMARY KEY
        password_hash     VARCHAR(255) NOT NULL
        role              VARCHAR(50)
        mail              VARCHAR(100) UNIQUE
        created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        username          VARCHAR(100)
        is_active         BOOLEAN DEFAULT TRUE
        email_verified_at TIMESTAMP
        is_verified       BOOLEAN DEFAULT FALSE
        pictures_id       INT REFERENCES pictures(idpictures) ON DELETE SET NULL
    """
    __tablename__ = "users"

    idusers = Column(Integer, primary_key=True, index=True, autoincrement=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=True)
    mail = Column(String(100), nullable=True)
    created_at = Column(
        DateTime,
        server_default=func.current_timestamp(),
        nullable=False,
    )
    username = Column(String(100), nullable=True)

    is_active = Column(
        Boolean,
        nullable=False,
        server_default="true",
        default=True,
    )
    is_verified = Column(
        Boolean,
        nullable=False,
        server_default="false",
        default=False,
    )
    email_verified_at = Column(DateTime, nullable=True)

    # Avatar/profile picture (optional FK toward pictures)
    pictures_id = Column(
        Integer,
        ForeignKey("pictures.idpictures", ondelete="SET NULL"),
        nullable=True,
    )
    avatar = relationship("Pictures", lazy="joined", foreign_keys=[pictures_id])

    __table_args__ = (
        UniqueConstraint("mail", name="uniq_users_mail"),
    )
