from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.models.camera import Camera
from backend.app.models.camera_schema import CameraCreate, CameraResponse

router = APIRouter(
    prefix="/cameras",
    tags=["Cameras"]
)

@router.post("/", response_model=CameraResponse)
def add_camera(camera: CameraCreate, db: Session = Depends(get_db)):
    existing = db.query(Camera).filter(
        Camera.camera_id == camera.camera_id
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Camera with this ID already exists"
        )

    db_camera = Camera(**camera.model_dump())
    db.add(db_camera)
    db.commit()
    db.refresh(db_camera)

    return db_camera


@router.get("/", response_model=list[CameraResponse])
def list_cameras(db: Session = Depends(get_db)):
    return db.query(Camera).all()
