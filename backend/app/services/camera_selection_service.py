from math import radians, sin, cos, sqrt, atan2
from backend.app.db.session import SessionLocal
from backend.app.models.camera import Camera

AUTO_SELECTION_RADIUS_KM = 3


def get_distance(lat1, lon1, lat2, lon2):
    R = 6371

    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)

    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return R * c


def auto_select_cameras(incident_lat, incident_lon):
    db = SessionLocal()

    try:
        cameras = db.query(Camera).all()

        selected = []

        for cam in cameras:
            dist = get_distance(
                incident_lat,
                incident_lon,
                cam.latitude,
                cam.longitude
            )

            if dist <= AUTO_SELECTION_RADIUS_KM:
                selected.append(cam.camera_id)

        selected.sort()

        return selected

    finally:
        db.close()