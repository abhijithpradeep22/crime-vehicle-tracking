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

        ("data/videos/vv_IMG_1447.mp4", "CAM_001", datetime(2026, 2, 4, 8, 30, 0)),
        ("data/videos/vv_IMG_1446.mp4", "CAM_002", datetime(2026, 2, 4, 9, 10, 0)),
        ("data/videos/vv_IMG_1442.mp4", "CAM_003", datetime(2026, 2, 4, 9, 30, 0)),
        ("data/videos/vv_IMG_1443.mp4", "CAM_004", datetime(2026, 2, 4, 10, 10, 0)),

        ("data/videos/b_IMG_1365.mp4", "CAM_005", datetime(2026, 3, 2, 11, 10, 0)),
        ("data/videos/b_IMG_1366.mp4", "CAM_008", datetime(2026, 3, 2, 11, 30, 0)),
        ("data/videos/b_IMG_1367.mp4", "CAM_012", datetime(2026, 3, 2, 11, 40, 0)),
        ("data/videos/b_IMG_1368.mp4", "CAM_016", datetime(2026, 3, 2, 11, 55, 0)),
        ("data/videos/b_IMG_1370.mp4", "CAM_020", datetime(2026, 3, 2, 12, 10, 0)),
        ("data/videos/b_IMG_1372.mp4", "CAM_024", datetime(2026, 3, 2, 12, 35, 0)),

        ("data/videos/t_IMG_1352.mp4", "CAM_006", datetime(2026, 3, 6, 13, 15, 0)),
        ("data/videos/t_IMG_1353.mp4", "CAM_007", datetime(2026, 3, 6, 13, 45, 0)),
        ("data/videos/t_IMG_1356.mp4", "CAM_009", datetime(2026, 3, 6, 14, 0, 0)),
        ("data/videos/t_IMG_1360.mp4", "CAM_010", datetime(2026, 3, 6, 14, 20, 0)),
        ("data/videos/t_IMG_1398.mp4", "CAM_011", datetime(2026, 3, 6, 15, 15, 0)),

        ("data/videos/ss_IMG_1453.mp4", "CAM_013", datetime(2026, 6, 3, 12, 0, 0)),
        ("data/videos/ss_IMG_1455.mp4", "CAM_014", datetime(2026, 6, 3, 12, 20, 0)),
        ("data/videos/ss_IMG_1456.mp4", "CAM_015", datetime(2026, 6, 3, 12, 45, 0)),
        ("data/videos/ss_IMG_1457.mp4", "CAM_017", datetime(2026, 6, 3, 13, 10, 0)),
        ("data/videos/ss_IMG_1458.mp4", "CAM_018", datetime(2026, 6, 3, 13, 35, 0)),
        ("data/videos/ss_IMG_1459.mp4", "CAM_019", datetime(2026, 6, 3, 14, 10, 0)),
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

        session = (
            db.query(TrackingSession)
            .filter(TrackingSession.case_id == case_id)
            .order_by(TrackingSession.id.desc())
            .first()
        )

        if not session:
            return {"message": "No tracking session found"}

        return {
            "target_plate": session.target_plate,

            "first_camera": session.first_camera,
            "first_location": session.first_location,
            "first_event_time": session.first_event_time,

            "latest_camera": session.latest_camera,
            "latest_location": session.latest_location,
            "latest_event_time": session.latest_event_time,

            "total_cameras": session.total_cameras,
            "completed_cameras": session.completed_cameras,

            "match_found": session.match_found,
            "status": session.status
        }

    finally:
        db.close()