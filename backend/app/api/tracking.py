from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from datetime import datetime

from backend.app.services.tracking_service import start_tracking
from backend.app.db.session import SessionLocal
from backend.app.models.tracking_session import TrackingSession

from sqlalchemy import desc
from backend.app.models.sighting import VehicleSighting
from backend.app.models.camera import Camera


router = APIRouter(prefix="/tracking", tags=["tracking"])


class TrackingRequest(BaseModel):
    case_id: int
    target_plate: str
    camera_ids: list[str] | None = None


# START TRACKING
@router.post("/start")
def start_tracking_endpoint(payload: TrackingRequest, background_tasks: BackgroundTasks):

    db = SessionLocal()

    existing = db.query(TrackingSession).filter(
        TrackingSession.case_id == payload.case_id
    ).first()

    db.close()

    if existing:
        return {
            "message": "Tracking already exists for this case",
            "session_id": existing.id,
            "status": existing.status
        }

    all_videos = [
        ("data/videos/IMG_1178.mp4", "CAM_001", datetime(2026, 2, 4, 8, 30, 0)),
        ("data/videos/IMG_1179.mp4", "CAM_002", datetime(2026, 2, 4, 10, 15, 0)),
        ("data/videos/IMG_1180.mp4", "CAM_003", datetime(2026, 2, 4, 13, 45, 0)),
        ("data/videos/IMG_1182.mp4", "CAM_004", datetime(2026, 2, 4, 17, 10, 0)),
    ]

    if payload.camera_ids:
        videos = [v for v in all_videos if v[1] in payload.camera_ids]
    else:
        videos = all_videos

    print("Selected cameras:", [v[1] for v in videos])

    background_tasks.add_task(
        start_tracking,
        payload.case_id,
        payload.target_plate,
        videos
    )

    return {"message": "Tracking started"}


# STOP TRACKING
@router.post("/stop/{case_id}")
def stop_tracking(case_id: int):

    db = SessionLocal()

    try:

        session = (
            db.query(TrackingSession)
            .filter(
                TrackingSession.case_id == case_id,
                TrackingSession.status == "active"
            )
            .order_by(TrackingSession.id.desc())
            .first()
        )

        if not session:
            raise HTTPException(status_code=404, detail="No active tracking session")

        session.status = "stopped"

        db.commit()

        return {"message": "Tracking stopped"}

    finally:
        db.close()


# GET LIVE STATUS
@router.get("/latest/{case_id}")
def get_latest(case_id: int):

    db = SessionLocal()

    try:

        session = db.query(TrackingSession).filter(
            TrackingSession.case_id == case_id
        ).first()

        if not session:
            return {"message": "No tracking session found"}

        latest_sighting = (
            db.query(VehicleSighting)
            .filter(VehicleSighting.tracking_session_id == session.id)
            .order_by(desc(VehicleSighting.event_time))
            .first()
        )

        latest_camera = None
        latest_location = None
        latest_time = None

        if latest_sighting:
            latest_camera = latest_sighting.camera_id

            camera = db.query(Camera).filter(
                Camera.camera_id == latest_camera
            ).first()

            if camera:
                latest_location = camera.location

            latest_time = latest_sighting.event_time

        return {
            "target_plate": session.target_plate,

            "first_camera": session.first_camera,
            "first_location": session.first_location,
            "first_event_time": session.first_event_time,

            "latest_camera": latest_camera,
            "latest_location": latest_location,
            "latest_event_time": latest_time,

            "total_cameras": session.total_cameras,
            "completed_cameras": session.completed_cameras,

            "status": session.status
        }

    finally:
        db.close()