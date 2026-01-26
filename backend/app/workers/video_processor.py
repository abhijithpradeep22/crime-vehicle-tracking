import cv2
import os
from ultralytics import YOLO
from sqlalchemy.orm import Session
from backend.app.db.session import SessionLocal

from backend.app.models.camera import Camera
from backend.app.models.case import InvestigationCase
from backend.app.models.sighting import VehicleSighting

from datetime import datetime

model = YOLO("yolov8n.pt")

VEHICLE_CLASSES = {2,3,5,7} # car,bike,bus,truck

def process_video(
        video_path: str,
        case_id: int,
        camera_id:int
):
    db: Session = SessionLocal()
    cap = cv2.VideoCapture(video_path)
    frame_count = 0

    os.makedirs("data/snapshots", exist_ok = True)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        #run yolo every 10 frames

        if frame_count % 10 != 0:
            continue

        results = model(frame, conf = 0.4, verbose = False)

        for r in results:
            for r in results:
                for box in r.boxes:
                    cls_id = int(box.cls[0])

                    if cls_id not in VEHICLE_CLASSES:
                        continue

                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    crop = frame[y1:y2, x1:x2]

                    filename = f"sighting_{case_id}_{camera_id}_{frame_count}.jpg"
                    image_path = os.path.join("data/snapshots", filename)

                    cv2.imwrite(image_path, crop)

                    sighting = VehicleSighting(
                        case_id = case_id,
                        camera_id = camera_id,
                        image_path = image_path,
                        vehicle_type = model.names[cls_id],
                        confidence = str(float(box.conf[0])),
                        detected_at = datetime.utcnow()
                    )

                    db.add(sighting)
                    db.commit()

                cap.release()
                db.close()