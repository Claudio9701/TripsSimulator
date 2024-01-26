from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import StreamingResponse
from typing import List
from models.geojson import GeoJSON, Trips
from services import trips_service

router = APIRouter()


@router.post("/trips/")
async def generate_trips(
    geojson: GeoJSON, population_size: int = None, trips_per_person: int = 2
):
    try:
        return StreamingResponse(
            trips_service.generate_trips(geojson, population_size, trips_per_person),
            media_type="application/json",
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
