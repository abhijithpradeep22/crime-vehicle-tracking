from pydantic import BaseModel

class CameraBase(BaseModel):
    camera_id: str
    location: str
    latitude: float
    logtitude: float

class CameraCreate(CameraBase):
    pass 

class CameraResponse(CameraBase):
    class Config:
        from_attributes = True