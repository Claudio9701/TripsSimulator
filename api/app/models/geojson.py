from typing import List, Optional
from pydantic import BaseModel


class Properties(BaseModel):
    tile_id: Optional[str] = None
    denspob: float
    desc_zoni: str
    sclas_zoni: Optional[str] = None


class Geometry(BaseModel):
    type: str
    coordinates: List[List[List[float]]]


class Feature(BaseModel):
    id: Optional[str] = None
    type: str
    properties: Properties
    geometry: Geometry
    bbox: Optional[List[float]] = None


class GeoJSON(BaseModel):
    type: str
    features: List[Feature]
    crs: Optional[dict] = None
    bbox: Optional[List[float]] = None


class Trips(BaseModel):
    start_time: int
    path: List[List[float]]
    timestamps: List[int]
    type: str
