from ultralytics import YOLO

model = YOLO("backend/app/models/license_plate_detector.pt")

print("MODEL LOADED")
print("CLASSES:", model.names)
