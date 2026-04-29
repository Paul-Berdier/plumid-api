from __future__ import annotations
from pydantic import BaseModel, ConfigDict
from typing import Optional


class FeathersBase(BaseModel):
    """Base properties for a Feather."""
    side: Optional[str] = None
    type: Optional[str] = None
    body_zone: Optional[str] = None
    species_id: Optional[int] = None


class FeathersCreate(FeathersBase):
    """Payload for creating a new Feather."""
    pass


class FeathersOut(FeathersBase):
    """Output model representing a Feather returned by the API."""
    idfeathers: int
    model_config = ConfigDict(from_attributes=True)
