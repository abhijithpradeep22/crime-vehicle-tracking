from pydantic import BaseModel
from datetime import datetime


class CaseCreate(BaseModel):
    user_id: int
    target_vehicle: str


class CaseResponse(BaseModel):
    id: int
    user_id: int
    target_vehicle: str
    created_at: datetime

    class Config:
        from_attributes = True