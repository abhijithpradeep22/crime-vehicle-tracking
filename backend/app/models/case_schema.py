from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class CaseBase(BaseModel):
    officer_id: str
    target_vehicle: Optional[str] = None

class CaseCreate(CaseBase):
    pass 

class CaseResponse(CaseBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True