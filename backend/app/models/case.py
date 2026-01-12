from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from backend.app.db.base import Base

class InvestigationCase(Base):
    __tablename__ = "investigation_cases"

    id = Column(Integer, primary_key = True, index = True)
    officer_id = Column(String, nullable = False)
    target_vehicle = Column(String, nullable = False)
    created_at = Column(DateTime, default = datetime.utcnow)
