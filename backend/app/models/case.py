from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from datetime import datetime
from backend.app.db.base import Base


class InvestigationCase(Base):
    __tablename__ = "investigation_cases"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=False)

    target_vehicle = Column(String, nullable=False)

    status = Column(String, default="active")

    created_at = Column(DateTime, default=datetime.utcnow)

    incident_location = Column(String, nullable=True)
    incident_latitude = Column(Float, nullable=True)
    incident_longitude = Column(Float, nullable=True)