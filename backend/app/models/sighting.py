from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from datetime import datetime
from backend.app.db.base import Base


class VehicleSighting(Base):
    __tablename__ = "vehicle_sightings"

    id = Column(Integer, primary_key=True, index=True)

    case_id = Column(
        Integer,
        ForeignKey("investigation_cases.id"),
        index=True,
        nullable=False
    )

    tracking_session_id = Column(
        Integer,
        ForeignKey("tracking_sessions.id"),
        index=True
    )

    camera_id = Column(
        String,
        ForeignKey("cameras.camera_id"),
        nullable=False
    )

    # saved images
    vehicle_image_path = Column(String, nullable=True)
    plate_image_path = Column(String, nullable=True)

    # timestamps
    event_time = Column(DateTime, index=True, nullable=True)
    detected_at = Column(DateTime, default=datetime.utcnow)

    # vehicle detection
    vehicle_type = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)

    # plate detection
    plate_number = Column(String, nullable=True, index=True)
    plate_confidence = Column(Float, nullable=True)