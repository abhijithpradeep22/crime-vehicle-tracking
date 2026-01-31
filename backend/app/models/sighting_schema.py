from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SightingBase(BaseModel):
    case_id: int
    camera_id: str
    image_path: str
    vehicle_type: Optional[str] = None
    confidence: Optional[str] = None

class SightingCreate(SightingBase):
    pass 

class SightingResponse(SightingBase):
    id: int
    detected_at: datetime

    class Config:
        from_attributes = True