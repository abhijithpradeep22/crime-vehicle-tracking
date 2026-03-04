from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from backend.app.db.base import Base


class TrackingSession(Base):
    __tablename__ = "tracking_sessions"

    id = Column(Integer, primary_key=True, index=True)

    case_id = Column(Integer, ForeignKey("investigation_cases.id"), unique=True, nullable=False)

    target_plate = Column(String, nullable=False)

    first_camera = Column(String, nullable=True)
    first_location = Column(String, nullable=True)
    first_event_time = Column(DateTime, nullable=True)

    latest_camera = Column(String, nullable=True)
    latest_location = Column(String, nullable=True)
    latest_event_time = Column(DateTime, nullable=True)

    total_cameras = Column(Integer, default=0)
    completed_cameras = Column(Integer, default=0)

    status = Column(String, default="running")