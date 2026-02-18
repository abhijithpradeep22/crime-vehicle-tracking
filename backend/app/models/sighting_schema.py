from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SightingBase(BaseModel):
    case_id: int
    camera_id: str
    image_path: Optional[str] = None

    vehicle_type: Optional[str] = None
    confidence: Optional[float] = None
    plate_number: Optional[str] = None
    plate_confidence: Optional[float] = None
    event_time: Optional[datetime] = None

class SightingCreate(SightingBase):
    pass 

class SightingResponse(SightingBase):
    id: int
    detected_at: datetime

    class Config:
        from_attributes = True