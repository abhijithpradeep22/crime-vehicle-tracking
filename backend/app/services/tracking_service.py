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
    """
    Worker process for a single camera
    """
    try:
        process_video(
            video_path=video_path,
            case_id=case_id,
            camera_id=camera_id,
            video_start_time=start_time,
            target_plate=target_plate,
            tracking_session_id=tracking_session_id, 
        )

    except Exception as e:
        print(f"Error in camera {camera_id}: {e}")


def start_tracking(case_id: int, target_plate: str, videos: list):
    """
    videos = [
        (video_path, camera_id, start_time),
        ...
    ]
    """

    db: Session = SessionLocal()

    # Create new tracking session
    session = TrackingSession(
        case_id=case_id,
        target_plate=target_plate,
        status="running"
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    tracking_session_id = session.id   #store id

    db.close()

    processes = []

    for video_path, camera_id, start_time in videos:

        p = Process(
            target=_run_tracking_for_camera,
            args=(
                video_path,
                case_id,
                camera_id,
                start_time,
                target_plate,
                tracking_session_id,   #pass to worker
            ),
        )

        p.start()
        processes.append(p)

    return tracking_session_id
