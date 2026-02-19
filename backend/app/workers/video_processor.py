import cv2
import os
from ultralytics import YOLO
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from backend.app.db.session import SessionLocal
from backend.app.models.camera import Camera
from backend.app.models.case import InvestigationCase
from backend.app.models.sighting import VehicleSighting
from backend.app.workers.anpr import extract_plate
from backend.app.workers.plate_aggregator import is_similar_plate


# Load models once (important for multiprocessing)
model = YOLO("yolov8n.pt")
plate_model = YOLO("backend/app/models/license_plate_detector.pt")

# YOLO class IDs: car=2, motorbike=3, bus=5, truck=7
VEHICLE_CLASSES = {2, 3, 5, 7}

last_seen_plates = {}  # {(camera_id, plate_text): datetime}
COOLDOWN_SECONDS = 5


def process_video(
    video_path: str,
    case_id: int,
    camera_id: str,
    video_start_time: datetime,
    target_plate: str = None,
    shared_state=None
):
    db: Session = SessionLocal()

    # Validate Camera
    camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not camera:
        db.close()
        raise ValueError(f"Camera {camera_id} not found")

    # Validate Case
    case = db.query(InvestigationCase).filter(InvestigationCase.id == case_id).first()
    if not case:
        db.close()
        raise ValueError(f"Case {case_id} not found")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        db.close()
        raise ValueError(f"Cannot open video: {video_path}")

    os.makedirs("data/snapshots", exist_ok=True)
    frame_count = 0
    alert_triggered = False  # Prevent multiple alerts per camera

    print(f"\nStarted processing {camera_id} at location: {camera.location}")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Process every 15th frame
        if frame_count % 15 != 0:
            continue

        results = model(frame, conf=0.35, iou=0.45, verbose=False)

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

                width = x2 - x1
                height = y2 - y1
                area = width * height

                if width < 80 or height < 80 or area < 6400:
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

                        if px2 - px1 < 20 or py2 - py1 < 10:
                            continue

                        plate_crop = vehicle_crop[py1:py2, px1:px2]
                        if plate_crop.size == 0:
                            continue

                        plate_text, plate_conf = extract_plate(plate_crop)

                        if plate_text is None or plate_conf is None:
                            continue

                        if plate_conf < 0.45:
                            continue

                        # ---- Calculate event_time EARLY ----
                        fps = cap.get(cv2.CAP_PROP_FPS)
                        if not fps or fps <= 0:
                            fps = 30  # fallback default
                        seconds_offset = frame_count / fps
                        event_time = video_start_time + timedelta(seconds=seconds_offset)

                        # -------- REAL-TIME TARGET ALERT --------
                        if target_plate and not alert_triggered:
                            if is_similar_plate(plate_text, target_plate, threshold=0.85):

                                print("\n" + "=" * 60)
                                print("🚨 TARGET VEHICLE DETECTED")
                                print(f"Plate Detected : {plate_text}")
                                print(f"Camera ID      : {camera_id}")
                                print(f"Location       : {camera.location}")
                                print(f"Event Time     : {event_time}")
                                print("=" * 60 + "\n")

                                # -------- LATEST KNOWN LOCATION UPDATE --------
                                if shared_state is not None:

                                    current_latest = shared_state.get("latest_event_time")

                                    if (
                                        current_latest is None
                                        or event_time > current_latest
                                    ):
                                        shared_state["latest_event_time"] = event_time
                                        shared_state["latest_camera"] = camera_id
                                        shared_state["latest_location"] = camera.location

                                        print("\n" + "-" * 60)
                                        print("🔵 LATEST KNOWN LOCATION UPDATED")
                                        print(f"Camera   : {camera_id}")
                                        print(f"Location : {camera.location}")
                                        print(f"Time     : {event_time}")
                                        print("-" * 60 + "\n")


                                alert_triggered = True

                        # Cooldown control
                        now = datetime.utcnow()
                        key = (camera_id, plate_text)

                        if key in last_seen_plates:
                            if (now - last_seen_plates[key]).total_seconds() < COOLDOWN_SECONDS:
                                continue

                        last_seen_plates[key] = now

                        vehicle_type = model.names[cls_id]

                        print(f"[ANPR] Plate detected: {plate_text} | Camera = {camera_id} | Frame = {frame_count}")

                        filename = f"sighting_{case_id}_{camera_id}_{frame_count}_{cls_id}.jpg"
                        image_path = os.path.join("data/snapshots", filename)
                        cv2.imwrite(image_path, plate_crop)

                        sighting = VehicleSighting(
                            case_id=case_id,
                            camera_id=camera_id,
                            image_path=image_path,
                            vehicle_type=vehicle_type,
                            confidence=float(box.conf[0]),
                            plate_number=plate_text,
                            plate_confidence=float(plate_conf),
                            event_time=event_time,
                            detected_at=now
                        )

                        db.add(sighting)

        if frame_count % 100 == 0:
            db.commit()

    db.commit()
    cap.release()
    db.close()

    print(f"Finished processing {camera_id}")
