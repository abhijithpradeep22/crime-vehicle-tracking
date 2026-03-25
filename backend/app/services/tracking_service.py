from multiprocessing import Process
from sqlalchemy.orm import Session
import time

from backend.app.db.session import SessionLocal
from backend.app.models.tracking_session import TrackingSession
from backend.app.workers.video_processor import process_video


MAX_PARALLEL_CAMERAS = 4


def _run_tracking_for_camera(
    video_path,
    case_id,
    camera_id,
    start_time,
    target_plate,
    tracking_session_id,
):

    try:

        print(f"Starting processing for camera {camera_id}")

        process_video(
            video_path=video_path,
            case_id=case_id,
            camera_id=camera_id,
            video_start_time=start_time,
            target_plate=target_plate,
            tracking_session_id=tracking_session_id,
        )

        print(f"Camera {camera_id} processing finished")

    except Exception as e:

        print(f"Error processing camera {camera_id}: {e}")


def start_tracking(case_id: int, target_plate: str, videos: list):

    print("Tracking requested for case:", case_id)
    print("Target number plate:", target_plate)

    db: Session = SessionLocal()

    # -------- Prevent duplicate sessions --------
    existing_session = db.query(TrackingSession).filter(
        TrackingSession.case_id == case_id
    ).first()

    if existing_session:
        print("Tracking already exists for this case. Reusing session.")
        db.close()
        return existing_session.id

    # -------- Create new tracking session --------
    session = TrackingSession(
        case_id=case_id,
        target_plate=target_plate,
        status="active",
        total_cameras=len(videos),
        completed_cameras=0,
        match_found=False,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    tracking_session_id = session.id

    print("Tracking session created:", tracking_session_id)
    print("Total cameras selected:", len(videos))

    db.close()

    # -------- Controlled parallel processing --------
    processes = []
    active_processes = []

    for video_path, camera_id, start_time in videos:

        if not is_tracking_active(tracking_session_id):
            print("[STOP] Not launching remaining cameras")
            break

        # Wait if max parallel cameras running
        while len(active_processes) >= MAX_PARALLEL_CAMERAS:

            if not is_tracking_active(tracking_session_id):
                print("[STOP] Breaking scheduler loop completely")
                return tracking_session_id

            for p in active_processes:
                if not p.is_alive():
                    active_processes.remove(p)

            time.sleep(1)

        print(f"Launching process for {camera_id}")

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

        processes.append(p)
        active_processes.append(p)

    print("All camera processes started")

    # Wait for all processes to finish
    for p in processes:
        p.join()

    print("All camera processes completed")

    # Final safety check
    db: Session = SessionLocal()

    session = db.query(TrackingSession).filter(
        TrackingSession.id == tracking_session_id
    ).first()

    if session and session.completed_cameras >= session.total_cameras:
        session.status = "completed"
        db.commit()
        print("Tracking session marked as completed (final check)")

    db.close()

    return tracking_session_id


def is_tracking_active(tracking_session_id):
    db = SessionLocal()
    try:
        session = db.query(TrackingSession).filter(
            TrackingSession.id == tracking_session_id
        ).first()

        return session and session.status == "active"

    finally:
        db.close()