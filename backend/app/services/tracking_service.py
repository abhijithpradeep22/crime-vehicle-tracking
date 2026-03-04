from multiprocessing import Process
from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal
from backend.app.models.tracking_session import TrackingSession
from backend.app.workers.video_processor import process_video


def _run_tracking_for_camera(
    video_path,
    case_id,
    camera_id,
    start_time,
    target_plate,
    tracking_session_id,
):

    try:

        process_video(
            video_path=video_path,
            case_id=case_id,
            camera_id=camera_id,
            video_start_time=start_time,
            target_plate=target_plate,
            tracking_session_id=tracking_session_id,
        )

        db: Session = SessionLocal()

        session = db.query(TrackingSession).filter(
            TrackingSession.id == tracking_session_id
        ).first()

        if session:

            session.completed_cameras += 1

            if session.completed_cameras >= session.total_cameras:
                session.status = "completed"
                print("Tracking session marked as completed")

            db.commit()

        db.close()

    except Exception as e:
        print(f"Error in camera {camera_id}: {e}")


def start_tracking(case_id: int, target_plate: str, videos: list):

    print("Tracking requested for case:", case_id)

    db: Session = SessionLocal()

    # -------- Prevent duplicate sessions --------
    existing_session = db.query(TrackingSession).filter(
        TrackingSession.case_id == case_id
    ).first()

    if existing_session:
        print("Tracking already exists for this case. Reusing session.")
        db.close()
        return existing_session.id

    # -------- Create new session --------
    session = TrackingSession(
        case_id=case_id,
        target_plate=target_plate,
        status="running",
        total_cameras=len(videos),
        completed_cameras=0,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    tracking_session_id = session.id

    db.close()

    # -------- Spawn processes --------
    for video_path, camera_id, start_time in videos:

        print("Processing video:", video_path)

        p = Process(
            target=_run_tracking_for_camera,
            args=(
                video_path,
                case_id,
                camera_id,
                start_time,
                target_plate,
                tracking_session_id,
            ),
        )

        p.start()

    return tracking_session_id