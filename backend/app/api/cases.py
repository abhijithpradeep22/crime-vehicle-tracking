from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.db.session import get_db
from backend.app.models.case import InvestigationCase
from backend.app.models.case_schema import CaseCreate, CaseResponse

router = APIRouter(
    prefix = "/cases",
    tags = ["Cases"]
)

@router.post("/", response_model=CaseResponse)
def create_case(case: CaseCreate, db: Session = Depends(get_db)):
    db_case = InvestigationCase(**case.model_dump())
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

@router.get("/", response_model = list[CaseResponse])
def list_cases(db: Session = Depends(get_db)):
    return db.query(InvestigationCase).all()