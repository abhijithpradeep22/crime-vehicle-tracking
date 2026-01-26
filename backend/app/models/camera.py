from sqlalchemy import Column, String, Float
from backend.app.db.base import Base

class Camera(Base):
    __tablename__ = "cameras"

    camera_id = Column(String, primary_key = True, index = True)
    location = Column(String, nullable = False)
    latitude = Column(Float, nullable = False)
    longitude = Column(Float, nullable = False)

