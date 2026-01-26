from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.sighting import VehicleSighting
from backend.app.models.sighting_schema import (
    SightingCreate,
    SightingResponse
)

router = APIRouter(
    prefix="/sightings",
    tags=["Sightings"]
)

@router.post("/", response_model=SightingResponse)
def create_sighting(
    sighting: SightingCreate,
    db: Session = Depends(get_db)
):
    db_sighting = VehicleSighting(**sighting.model_dump())
    db.add(db_sighting)
    db.commit()
    db.refresh(db_sighting)
    return db_sighting

@router.get("/", response_model=list[SightingResponse])
def list_sightings(db: Session = Depends(get_db)):
    return db.query(VehicleSighting).all()
