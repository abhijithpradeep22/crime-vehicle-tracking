from sqlalchemy import Column, Integer, ForeignKey, DateTime, Text
from datetime import datetime
from backend.app.db.base import Base

class InvestigationReport(Base):
    __tablename__ = "investigation_reports"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("investigation_cases.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    report_json = Column(Text)   # store route reconstruction JSON