import cv2
import os
import time

from ultralytics import YOLO
from sqlalchemy.orm import Session
from datetime import datetime

from backend.app.db.session import SessionLocal
from backend.app.models.camera import Camera
from backend.app.models.case import InvestigationCase
from backend.app.models.sighting import VehicleSighting
from backend.app.workers.anpr import extract_plate


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

                # Skip very low-confidence detections (OCR)
                if float(box.conf[0]) < 0.5:
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

                #Crop the detected vehicle
                vehicle_crop = frame[y1:y2, x1:x2]
                if vehicle_crop.size == 0:
                    continue

                #Compute vehicle dimensions
                h, w, _ = vehicle_crop.shape

                #Crop plate region
                plate_crop = vehicle_crop[int(h*0.55):h, int(w*0.2):int(w*0.8)]

                if plate_crop.size == 0:
                    continue

                plate_text, plate_conf = extract_plate(plate_crop)

                vehicle_type = model.names[cls_id]

                image_path = None
                if plate_text:

                    print(f"[ANPR] Plate detected: {plate_text} | Camera={camera_id} | Frame={frame_count}")
                    filename = f"sighting_{case_id}_{camera_id}_{frame_count}_{cls_id}.jpg"
                    image_path = os.path.join("data/snapshots", filename)
                    cv2.imwrite(image_path, crop)
                
                sighting = VehicleSighting(
                    case_id = case_id,
                    camera_id = camera_id,
                    image_path = image_path,
                    vehicle_type = vehicle_type,
                    confidence = float(box.conf[0]),
                    plate_number = plate_text,
                    plate_confidence = plate_conf,
                    detected_at = datetime.utcnow()
                )

                db.add(sighting)

        if frame_count % 100 == 0:
            db.commit()

    db.commit()
    cap.release()
    db.close()
    print("Processing Finished")
