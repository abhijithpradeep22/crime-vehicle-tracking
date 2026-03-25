from backend.app.db.session import SessionLocal
from backend.app.models.camera import Camera


def seed_cameras():
    db = SessionLocal()

    cameras = [
        Camera(camera_id="CAM_001", location="Kesavadasapuram", latitude=8.5303, longitude=76.9384),
        Camera(camera_id="CAM_002", location="Ulloor", latitude=8.5389, longitude=76.9276),
        Camera(camera_id="CAM_003", location="Pattom", latitude=8.5226, longitude=76.9392),
        Camera(camera_id="CAM_004", location="Murinjapalam", latitude=8.5350, longitude=76.9408),
        Camera(camera_id="CAM_005", location="Pathanamthitta", latitude=9.267292, longitude=76.794418),
        Camera(camera_id="CAM_008", location="Konni", latitude=9.231924, longitude=76.847834),
        Camera(camera_id="CAM_012", location="Vakayar", latitude=9.197236, longitude=76.850311),
        Camera(camera_id="CAM_016", location="Koodal", latitude=9.140469, longitude=76.854845),
        Camera(camera_id="CAM_020", location="Pathanapuram", latitude=9.094472, longitude=76.853053),
        Camera(camera_id="CAM_024", location="Punalur", latitude=9.020537, longitude=76.927259),
        Camera(camera_id="CAM_006", location="Kottarakkara", latitude=9.011332, longitude=76.784173),
        Camera(camera_id="CAM_007", location="Adoor", latitude=9.166957, longitude=76.718381),
        Camera(camera_id="CAM_009", location="Pandalam", latitude=9.236964, longitude=76.672434),
        Camera(camera_id="CAM_010", location="Chengannur", latitude=9.329752, longitude=76.605184),
        Camera(camera_id="CAM_011", location="Kottayam", latitude=9.603326, longitude=76.530176),
        Camera(camera_id="CAM_013", location="Anchal", latitude=8.927174, longitude=76.905946),
        Camera(camera_id="CAM_014", location="Ayoor", latitude=8.89799, longitude=76.86034),
        Camera(camera_id="CAM_015", location="Chadayamangalam", latitude=8.863303, longitude=76.87179),
        Camera(camera_id="CAM_017", location="Kilimanoor", latitude=8.76978, longitude=76.88301),
        Camera(camera_id="CAM_018", location="Venjarammoodu", latitude=8.671402, longitude=76.910845),
        Camera(camera_id="CAM_019", location="Nedumangadu", latitude=8.603396, longitude=77.005053),
    ]

    for cam in cameras:
        if not db.query(Camera).filter(Camera.camera_id == cam.camera_id).first():
            db.add(cam)

    db.commit()
    db.close()


if __name__ == "__main__":
    seed_cameras()
    print("Cameras seeded successfully.")