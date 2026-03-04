from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

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

    db_case = InvestigationCase(
        user_id=case.user_id,
        target_vehicle=case.target_vehicle
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