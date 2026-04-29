from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


class SpeciesBase(BaseModel):
    """
    Base properties for a Species.
    Matches the columns of the species table.
    """
    sex: Optional[str] = Field(default=None, max_length=1)
    region: Optional[str] = Field(default=None, max_length=100)
    environment: Optional[str] = Field(default=None, max_length=100)
    information: Optional[str] = None
    species_name: Optional[str] = Field(default=None, max_length=100)
    species_url_picture: Optional[str] = None


class SpeciesCreate(SpeciesBase):
    """Payload for creating a new Species."""
    pass


class SpeciesOut(SpeciesBase):
    """Output model representing a Species returned by the API."""
    idspecies: int
    model_config = ConfigDict(from_attributes=True)
