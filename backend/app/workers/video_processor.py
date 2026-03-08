import cv2
import os
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
COOLDOWN_SECONDS = 5

last_seen_plates = {}
last_tracking_update = {}

# ---------------- PERFORMANCE CONFIG ---------------- #

DETECTION_WIDTH = 1280
DETECTION_HEIGHT = 720

FRAME_SKIP = 20
VEHICLE_CONF = 0.45
PLATE_CONF = 0.5

MIN_VEHICLE_AREA = 15000


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

        # keep original frame for snapshots
        original_frame = frame

        # resize frame for detection (much faster)
        frame = cv2.resize(frame, (DETECTION_WIDTH, DETECTION_HEIGHT))

        # scale factors to map detection back to original frame
        scale_x = original_frame.shape[1] / DETECTION_WIDTH
        scale_y = original_frame.shape[0] / DETECTION_HEIGHT

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

        results = model(frame, conf=VEHICLE_CONF, iou=0.45, verbose=False)

        for r in results:

            for box in r.boxes:

                cls_id = int(box.cls[0])

                if cls_id not in VEHICLE_CLASSES:
                    continue

                if float(box.conf[0]) < VEHICLE_CONF:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                # scale coordinates to original frame
                x1 = int(x1 * scale_x)
                x2 = int(x2 * scale_x)
                y1 = int(y1 * scale_y)
                y2 = int(y2 * scale_y)

                if x2 <= x1 or y2 <= y1:
                    continue



                vehicle_crop = original_frame[y1:y2, x1:x2]

                if vehicle_crop.size == 0:
                    continue

                vehicle_area = (x2 - x1) * (y2 - y1)

                if vehicle_area < MIN_VEHICLE_AREA:
                    continue

                plate_results = plate_model(vehicle_crop, conf=PLATE_CONF, verbose=False)

                for pr in plate_results:

                    if pr.boxes is None:
                        continue

                    for pbox in pr.boxes:

                        if float(pbox.conf[0]) < PLATE_CONF:
                            continue

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

                        if plate_conf < PLATE_CONF or float(box.conf[0]) < VEHICLE_CONF:
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

                        context_padding = 200

                        h, w = original_frame.shape[:2]

                        cx1 = max(0, x1 - context_padding)
                        cy1 = max(0, y1 - context_padding)
                        cx2 = min(w, x2 + context_padding)
                        cy2 = min(h, y2 + context_padding)

                        frame_copy = original_frame[cy1:cy2, cx1:cx2].copy()

                        # draw box relative to cropped evidence frame
                        cv2.rectangle(
                            frame_copy,
                            (x1 - cx1, y1 - cy1),
                            (x2 - cx1, y2 - cy1),
                            (0,255,0),
                            2
                        )

                        cv2.putText(
                            frame_copy,
                            plate_text,
                            (x1 - cx1, y1 - cy1 - 10),
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

                        if tracking_session and plate_text == tracking_session.target_plate:

                            first_updated = False
                            latest_updated = False

                            # FIRST detection
                            if (
                                tracking_session.first_event_time is None
                                or event_time < tracking_session.first_event_time
                            ):
                                tracking_session.first_event_time = event_time
                                tracking_session.first_camera = camera_id
                                tracking_session.first_location = camera.location
                                first_updated = True

                            # LATEST detection (correct logic)
                            if (
                                tracking_session.latest_event_time is None
                                or event_time > tracking_session.latest_event_time
                            ):
                                tracking_session.latest_event_time = event_time
                                tracking_session.latest_camera = camera_id
                                tracking_session.latest_location = camera.location
                                latest_updated = True

                            if first_updated or latest_updated:

                                key = (camera_id, tracking_session.target_plate)

                                if key in last_tracking_update:
                                    if (now - last_tracking_update[key]).total_seconds() < 10:
                                        continue

                                last_tracking_update[key] = now

                                tracking_session.match_found = True

                                db.commit()

                            print(f"[TRACKING UPDATED] {camera_id} @ {event_time}")

        if frame_count % 100 == 0:
            db.commit()

    db.commit()

    # -------- CAMERA FINISHED -------- #

    if tracking_session_id:
        session = db.query(TrackingSession).filter(
            TrackingSession.id == tracking_session_id
        ).first()

        if session:

            session.completed_cameras += 1

            if session.completed_cameras >= session.total_cameras:
                session.status = "completed"
                print("Tracking session marked as completed")

            db.commit()

    cap.release()
    db.close()

    print(f"Finished processing {camera_id}")