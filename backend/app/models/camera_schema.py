from pydantic import BaseModel

class CameraBase(BaseModel):
    camera_id: str
    location: str
    latitude: float
    longitude: float

class CameraCreate(CameraBase):
    pass 

class CameraResponse(CameraBase):
    class Config:
        from_attributes = True