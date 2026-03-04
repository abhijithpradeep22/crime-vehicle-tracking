from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from backend.app.db.base import Base


class InvestigationCase(Base):
    __tablename__ = "investigation_cases"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False)

    target_vehicle = Column(String, nullable=False)

    status = Column(String, default="active")

    created_at = Column(DateTime, default=datetime.utcnow)