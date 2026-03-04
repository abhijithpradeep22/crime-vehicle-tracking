from datetime import timedelta
from sqlalchemy.orm import Session
from sqlalchemy import asc
import os

from backend.app.models.sighting import VehicleSighting
from backend.app.models.camera import Camera
from backend.app.models.tracking_session import TrackingSession
from backend.app.workers.plate_aggregator import is_similar_plate


def build_live_route(
    db: Session,
    case_id: int,
    visit_gap_minutes: int = 5,
):

    session = (
        db.query(TrackingSession)
        .filter(TrackingSession.case_id == case_id)
        .order_by(TrackingSession.id.desc())
        .first()
    )

    if not session:
        return []

    target_plate = session.target_plate

    sightings = (
        db.query(VehicleSighting)
        .filter(VehicleSighting.tracking_session_id == session.id)
        .order_by(asc(VehicleSighting.event_time))
        .all()
    )

    if not sightings:
        return []

    camera_map = {
        cam.camera_id: cam.location
        for cam in db.query(Camera).all()
    }

    visit_gap = timedelta(minutes=visit_gap_minutes)

    route = []
    current_stop = None

    for s in sightings:

        if not is_similar_plate(s.plate_number, target_plate, threshold=0.85):
            continue

        location = camera_map.get(s.camera_id, "Unknown")

        vehicle_image_url = (
            f"/snapshots/vehicles/{os.path.basename(s.vehicle_image_path)}"
            if s.vehicle_image_path
            else None
        )

        plate_image_url = (
            f"/snapshots/plates/{os.path.basename(s.plate_image_path)}"
            if s.plate_image_path
            else None
        )

        if current_stop is None:
            current_stop = {
                "camera_id": s.camera_id,
                "location": location,
                "first_seen": s.event_time,
                "last_seen": s.event_time,
                "total_detections": 1,
                "best_confidence": s.confidence,
                "representative_vehicle_image": vehicle_image_url,
                "representative_plate_image": plate_image_url,
            }
            continue

        time_gap = s.event_time - current_stop["last_seen"]
        same_camera = s.camera_id == current_stop["camera_id"]

        if same_camera and time_gap <= visit_gap:

            current_stop["last_seen"] = s.event_time
            current_stop["total_detections"] += 1

            # UPDATE REPRESENTATIVE IMAGE IF HIGHER CONFIDENCE
            if s.confidence and s.confidence > current_stop["best_confidence"]:
                current_stop["best_confidence"] = s.confidence
                current_stop["representative_vehicle_image"] = vehicle_image_url
                current_stop["representative_plate_image"] = plate_image_url

        else:
            route.append(current_stop)

            current_stop = {
                "camera_id": s.camera_id,
                "location": location,
                "first_seen": s.event_time,
                "last_seen": s.event_time,
                "total_detections": 1,
                "best_confidence": s.confidence,
                "representative_vehicle_image": vehicle_image_url,
                "representative_plate_image": plate_image_url,
            }

    if current_stop:
        route.append(current_stop)

    # Travel time calculation
    for i in range(len(route)):
        if i == 0:
            route[i]["travel_seconds_from_previous"] = None
            route[i]["travel_minutes_from_previous"] = None
        else:
            prev = route[i - 1]
            curr = route[i]

            travel_time = curr["first_seen"] - prev["last_seen"]
            seconds = max(int(travel_time.total_seconds()), 0)

            curr["travel_seconds_from_previous"] = seconds
            curr["travel_minutes_from_previous"] = round(seconds / 60, 2)

    # remove internal best_confidence before returning
    for stop in route:
        stop.pop("best_confidence", None)

    return route
