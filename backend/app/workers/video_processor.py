import cv2
import os
from collections import defaultdict
import time
from ultralytics import YOLO
from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.db.session import SessionLocal
from backend.app.models.camera import Camera
from backend.app.models.case import InvestigationCase
from backend.app.models.sighting import VehicleSighting

model = YOLO("yolov8n.pt")

# YOLO class IDs: car=2, motorbike=3, bus=5, truck=7
VEHICLE_CLASSES = {2, 3, 5, 7}


def process_video(
    video_path: str,
    case_id: int,
    camera_id: str
):
    db: Session = SessionLocal()

    #VALIDATE CAMERA
    camera = db.query(Camera).filter(Camera.camera_id == camera_id).first()
    if not camera:
        db.close()
        raise ValueError(f"Camera {camera_id} not found")

    #VALIDATE CASE
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

    last_seen_time = defaultdict(float)
    MIN_GAP_SECONDS = 5

    last_seen_position = []
    DIST_THRESHOLD = 50

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

                x1, y1, x2, y2 = map(int, box.xyxy[0])

                if x2 <= x1 or y2 <= y1:
                    continue

                MIN_WIDTH = 80
                MIN_HEIGHT = 80
                MIN_AREA = 80 * 80
                width = x2 - x1
                height = y2 - y1
                area = width * height

                if width < MIN_WIDTH or height < MIN_HEIGHT:
                    continue

                if area < MIN_AREA:
                    continue

                cx = int((x1 + x2) / 2)
                cy = int((y1 + y2) / 2)

                is_duplicate = False
                for px, py in last_seen_position:
                    if abs(cx - px) < DIST_THRESHOLD and abs(cy -py) < DIST_THRESHOLD:
                        is_duplicate = True
                        break
                if is_duplicate:
                    continue

                crop = frame[y1:y2, x1:x2]
                if crop.size == 0:
                    continue

                filename = f"sighting_{case_id}_{camera_id}_{frame_count}.jpg"
                image_path = os.path.join("data/snapshots", filename)

                cv2.imwrite(image_path, crop)

                vehicle_type = model.names[cls_id]
                key = (camera_id, vehicle_type)
                current_time = time.time()

                #skip recent detection
                if current_time - last_seen_time[key] < MIN_GAP_SECONDS:
                    continue

                last_seen_time[key] = current_time

                sighting = VehicleSighting(
                    case_id = case_id,
                    camera_id = camera_id,
                    image_path = image_path,
                    vehicle_type = vehicle_type,
                    confidence = float(box.conf[0]),
                    detected_at = datetime.utcnow()
                )

                db.add(sighting)

        # optional safety commit
        if frame_count % 100 == 0:
            db.commit()

    db.commit()
    cap.release()
    db.close()
    print("Processing Finished")
