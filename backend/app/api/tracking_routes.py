from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.route_service import build_live_route

router = APIRouter(prefix="/tracking", tags=["Tracking"])


@router.get("/route/{case_id}")
def get_live_route(case_id: int, db: Session = Depends(get_db)):
    route = build_live_route(db, case_id)
    return {
        "case_id": case_id,
        "stops": route,
    }
