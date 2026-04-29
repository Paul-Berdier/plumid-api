from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from datetime import date
from decimal import Decimal
from typing import Optional


class PicturesBase(BaseModel):
    """Base properties for a Picture."""
    url: Optional[str] = None
    longitude: Optional[Decimal] = None
    latitude: Optional[Decimal] = None
    date_collected: Optional[date] = None
    feathers_id: Optional[int] = None


class PicturesCreate(PicturesBase):
    """Payload for creating a new Picture."""
    pass


class PicturesOut(PicturesBase):
    """Output model representing a Picture returned by the API."""
    idpictures: int
    model_config = ConfigDict(from_attributes=True)
