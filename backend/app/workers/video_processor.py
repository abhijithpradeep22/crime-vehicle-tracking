import cv2
import os
from sqlalchemy import or_
from sqlalchemy import text
from ultralytics import YOLO
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from backend.app.db.session import SessionLocal
from backend.app.models.camera import Camera
from backend.app.models.case import InvestigationCase
from backend.app.models.sighting import VehicleSighting
from backend.app.models.tracking_session import TrackingSession
from backend.app.workers.anpr import extract_plate
from backend.app.workers.plate_aggregator import is_similar_plate


# ---------------- MODEL LOADING ---------------- #

model = YOLO("yolov8n.pt")
plate_model = YOLO("backend/app/models/license_plate_detector.pt")


# ---------------- CONFIG ---------------- #

VEHICLE_CLASSES = {2, 3, 5, 7}
FRAME_SKIP = 3
COOLDOWN_SECONDS = 5

last_seen_plates = {}
last_tracking_update = {}


# ---------------- MAIN PROCESS FUNCTION ---------------- #

def process_video(
    video_path: str,
    case_id: int,
    camera_id: str,
    video_start_time: datetime,
    target_plate: str = None,
    tracking_session_id: int = None,
):

    db: Session = SessionLocal()

    camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not camera:
        db.close()
        raise ValueError(f"Camera {camera_id} not found")

    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        db.close()
        raise ValueError(f"Case {case_id} not found")

    tracking_session = None
    if tracking_session_id:
        tracking_session = db.query(TrackingSession).filter(
            TrackingSession.id == tracking_session_id
        ).first()

    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        db.close()
        raise ValueError(f"Cannot open video: {video_path}")

    os.makedirs("data/snapshots/vehicles", exist_ok=True)
    os.makedirs("data/snapshots/plates", exist_ok=True)

    frame_count = 0
    stop_check_counter = 0

    print(f"\nStarted processing {camera_id} at location: {camera.location}")

    while True:

        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1
        stop_check_counter += 1

        # ---- CHECK IF USER STOPPED TRACKING ----
        if tracking_session_id and stop_check_counter % 30 == 0:
            session = db.query(TrackingSession).filter(
                TrackingSession.id == tracking_session_id
            ).first()

            if session and session.status == "stopped":
                print(f"[STOP] Tracking stopped by user for case {case_id}")
                cap.release()
                db.commit()
                db.close()
                return

        if frame_count % FRAME_SKIP != 0:
            continue

        results = model(frame, conf=0.45, iou=0.45, verbose=False)

        for r in results:

            for box in r.boxes:

                cls_id = int(box.cls[0])

                if cls_id not in VEHICLE_CLASSES:
                    continue

                if float(box.conf[0]) < 0.5:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                if x2 <= x1 or y2 <= y1:
                    continue

                vehicle_crop = frame[y1:y2, x1:x2]

                if vehicle_crop.size == 0:
                    continue

                plate_results = plate_model(vehicle_crop, conf=0.4, verbose=False)

                for pr in plate_results:

                    if pr.boxes is None:
                        continue

                    for pbox in pr.boxes:

                        px1, py1, px2, py2 = map(int, pbox.xyxy[0])

                        vh, vw = vehicle_crop.shape[:2]

                        px1 = max(0, px1)
                        py1 = max(0, py1)
                        px2 = min(vw, px2)
                        py2 = min(vh, py2)

                        plate_crop = vehicle_crop[py1:py2, px1:px2]

                        if plate_crop.size == 0:
                            continue

                        plate_text, plate_conf = extract_plate(plate_crop)

                        if plate_text is None or plate_conf is None:
                            continue

                        plate_text = plate_text.upper().replace(" ", "")
                        if len(plate_text) < 6 or len(plate_text) > 10:
                            continue

                        if plate_conf < 0.5 or float(box.conf[0]) < 0.6:
                            continue

                        fps = cap.get(cv2.CAP_PROP_FPS)

                        if not fps or fps <= 0:
                            fps = 30

                        seconds_offset = frame_count / fps
                        event_time = video_start_time + timedelta(seconds=seconds_offset)

                        now = datetime.utcnow()

                        key = (camera_id, plate_text)

                        if key in last_seen_plates:
                            if (now - last_seen_plates[key]).total_seconds() < COOLDOWN_SECONDS:
                                continue

                        last_seen_plates[key] = now

                        vehicle_type = model.names[cls_id]

                        frame_copy = frame.copy()

                        cv2.rectangle(frame_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)

                        cv2.putText(
                            frame_copy,
                            plate_text,
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (0, 255, 0),
                            2,
                        )

                        vehicle_filename = f"vehicle_{case_id}_{camera_id}_{frame_count}.jpg"
                        vehicle_image_path = os.path.join(
                            "data/snapshots/vehicles",
                            vehicle_filename,
                        )

                        cv2.imwrite(vehicle_image_path, frame_copy)

                        plate_filename = f"plate_{case_id}_{camera_id}_{frame_count}.jpg"
                        plate_image_path = os.path.join(
                            "data/snapshots/plates",
                            plate_filename,
                        )

                        cv2.imwrite(plate_image_path, plate_crop)

                        print(
                            f"[ANPR] Plate detected: {plate_text} | "
                            f"Camera: {camera_id} | "
                            f"Frame: {frame_count}"
                        )

                        sighting = VehicleSighting(
                            case_id=case_id,
                            tracking_session_id=tracking_session_id,
                            camera_id=camera_id,
                            vehicle_image_path=vehicle_image_path,
                            plate_image_path=plate_image_path,
                            vehicle_type=vehicle_type,
                            confidence=float(box.conf[0]),
                            plate_number=plate_text,
                            plate_confidence=float(plate_conf),
                            event_time=event_time,
                            detected_at=now,
                        )

                        db.add(sighting)

                        # ---------- TRACKING UPDATE ----------

                        if tracking_session and is_similar_plate(
                            plate_text,
                            tracking_session.target_plate,
                            threshold=0.9
                        ):

                            session_check = db.query(TrackingSession).filter(
                                TrackingSession.id == tracking_session_id
                            ).first()

                            first_updated = False

                            # FIRST detection
                            if (
                                session_check.first_event_time is None
                                or event_time < session_check.first_event_time
                            ):
                                session_check.first_event_time = event_time
                                session_check.first_camera = camera_id
                                session_check.first_location = camera.location
                                session_check.match_found = True
                                first_updated = True

                            # ATOMIC LATEST UPDATE
                            key = (camera_id, tracking_session_id)

                            if key in last_tracking_update:
                                if (now - last_tracking_update[key]).total_seconds() < 10:
                                    continue

                            update_count = 0

                            for _ in range(3):
                                try:

                                    update_count = db.query(TrackingSession).filter(
                                        TrackingSession.id == tracking_session_id,
                                        or_(
                                            TrackingSession.latest_event_time == None,
                                            TrackingSession.latest_event_time < event_time
                                        )
                                    ).update({
                                        "latest_event_time": event_time,
                                        "latest_camera": camera_id,
                                        "latest_location": camera.location,
                                        "match_found": True
                                    })

                                    db.commit()

                                    if update_count > 0:
                                        last_tracking_update[key] = now

                                    break

                                except Exception:
                                    db.rollback()

                            print(f"[TRACKING UPDATED] {camera_id} @ {event_time}")

        if frame_count % 100 == 0:
            for _ in range(3):
                try:
                    db.commit()
                    break
                except Exception:
                    db.rollback()

    for _ in range(3):
        try:
            db.commit()
            break
        except Exception:
            db.rollback()

    # -------- CAMERA FINISHED -------- #

    db.execute(
        text(
            """
            UPDATE tracking_sessions
            SET completed_cameras = completed_cameras + 1
            WHERE id = :session_id
            """
        ),
        {"session_id": tracking_session_id}
    )

    db.commit()

    session = db.query(TrackingSession).filter(
        TrackingSession.id == tracking_session_id
    ).first()

    if session.completed_cameras >= session.total_cameras:
        session.status = "completed"
        db.commit()
        print("Tracking session marked as completed")

    cap.release()
    db.close()

    print(f"Finished processing {camera_id}")