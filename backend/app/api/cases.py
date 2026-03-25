from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from fastapi import Query, HTTPException
from backend.app.services.geocode_service import search_location, get_coordinates

from backend.app.db.session import get_db
from backend.app.models.case import InvestigationCase
from backend.app.models.case_schema import CaseCreate, CaseResponse


router = APIRouter(
    prefix="/cases",
    tags=["Cases"]
)


# CREATE CASE
@router.post("/", response_model=CaseResponse)
def create_case(case: CaseCreate, db: Session = Depends(get_db)):

    lat, lon = None, None

    if case.incident_location:
        coords = get_coordinates(case.incident_location)

        if not coords:
            raise HTTPException(status_code=400, detail="Location not found")

        lat, lon = coords

    db_case = InvestigationCase(
        user_id=case.user_id,
        target_vehicle=case.target_vehicle,
        incident_location=case.incident_location,
        incident_latitude=lat,
        incident_longitude=lon
    )

    db.add(db_case)
    db.commit()
    db.refresh(db_case)

    return db_case


# LIST ALL CASES
@router.get("/", response_model=list[CaseResponse])
def list_cases(db: Session = Depends(get_db)):

    return db.query(InvestigationCase).all()


# GET CASES FOR A SPECIFIC USER
@router.get("/user/{user_id}", response_model=list[CaseResponse])
def get_cases_by_user(user_id: int, db: Session = Depends(get_db)):

    cases = db.query(InvestigationCase).filter(
        InvestigationCase.user_id == user_id
    ).order_by(
        InvestigationCase.created_at.desc()
    ).all()

    return cases


@router.get("/location/search")
def location_search(q: str = Query(..., min_length=2)):
    return search_location(q)


@router.post("/{case_id}/location")
def set_case_location(
    case_id: int,
    payload: dict,
    db: Session = Depends(get_db)
):

    case = db.query(InvestigationCase).filter(
        InvestigationCase.id == case_id
    ).first()

    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    location_name = payload.get("incident_location")

    if not location_name:
        raise HTTPException(status_code=400, detail="Location is required")

    coords = get_coordinates(location_name)

    if not coords:
        raise HTTPException(status_code=400, detail="Location not found")

    lat, lon = coords

    # Update case
    case.incident_location = location_name
    case.incident_latitude = lat
    case.incident_longitude = lon

    db.commit()

    return {
        "message": "Location updated successfully",
        "incident_location": location_name,
        "latitude": lat,
        "longitude": lon
    }