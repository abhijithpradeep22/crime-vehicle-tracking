from fastapi import APIRouter
from backend.app.db.session import SessionLocal
from backend.app.models.report import InvestigationReport
from backend.app.services.route_service import build_live_route
import json

router = APIRouter(prefix="/reports", tags=["reports"])


# SAVE REPORT
@router.post("/save/{case_id}")
def save_report(case_id: int):

    db = SessionLocal()

    try:

        route = build_live_route(db, case_id)

        report_data = {
            "case_id": case_id,
            "stops": route
        }

        report = InvestigationReport(
            case_id=case_id,
            report_json=json.dumps(report_data, default=str)
        )

        db.add(report)
        db.commit()

        return {"message": "Report saved"}

    finally:
        db.close()


# GET REPORTS FOR CASE
@router.get("/case/{case_id}")
def get_reports_for_case(case_id: int):

    db = SessionLocal()

    try:

        reports = (
            db.query(InvestigationReport)
            .filter(InvestigationReport.case_id == case_id)
            .order_by(InvestigationReport.id.desc())
            .all()
        )

        return [
            {
                "id": r.id,
                "created_at": r.created_at
            }
            for r in reports
        ]

    finally:
        db.close()


# GET SINGLE REPORT
@router.get("/{report_id}")
def get_report(report_id: int):

    db = SessionLocal()

    try:

        report = (
            db.query(InvestigationReport)
            .filter(InvestigationReport.id == report_id)
            .first()
        )

        if not report:
            return {"error": "Report not found"}

        return json.loads(report.report_json)

    finally:
        db.close()