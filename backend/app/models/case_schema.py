from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class CaseCreate(BaseModel):
    user_id: int
    target_vehicle: str
    incident_location: Optional[str] = None


class CaseResponse(BaseModel):
    id: int
    user_id: int
    target_vehicle: str
    created_at: datetime

    class Config:
        from_attributes = True