from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from backend.app.db.base import Base

class VehicleSighting(Base):
    __tablename__ = "vehicle_sightings"

    id = Column(Integer, primary_key = True, index = True)

    case_id = Column(Integer, ForeignKey("investigation_cases.id"), nullable = False)
    camera_id = Column(Integer, ForeignKey("cameras.camera_id"), nullable = False)

    image_path = Column(String, nullable = False)
    detected_at = Column(DateTime, default = datetime.utcnow)

    vehicle_type = Column(String, nullable = True)
    confidence = Column(String, nullable = True)