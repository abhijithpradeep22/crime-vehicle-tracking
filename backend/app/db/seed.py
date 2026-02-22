from backend.app.db.session import SessionLocal
from backend.app.models.camera import Camera

def seed_cameras():
    db = SessionLocal()

    cameras = [
        Camera(camera_id="CAM_001", location="Main Road Junction", latitude=10.7867, longitude=76.6548),
        Camera(camera_id="CAM_002", location="Highway Entry", latitude=10.8000, longitude=76.6600),
        Camera(camera_id="CAM_003", location="City Signal", latitude=10.8100, longitude=76.6700),
        Camera(camera_id="CAM_004", location="Toll Plaza", latitude=10.8200, longitude=76.6800),
    ]

    for cam in cameras:
        if not db.query(Camera).filter(Camera.camera_id == cam.camera_id).first():
            db.add(cam)

    db.commit()
    db.close()

if __name__ == "__main__":
    seed_cameras()
    print("Cameras seeded successfully.")
