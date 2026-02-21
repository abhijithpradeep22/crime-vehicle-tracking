from sqlalchemy.orm import Session
from datetime import timedelta

from backend.app.models.sighting import VehicleSighting
from backend.app.models.camera import Camera
from backend.app.workers.plate_aggregator import is_similar_plate



def build_vehicle_timeline(
    db: Session,
    case_id: int,
    target_plate: str,
    similarity_threshold: float = 0.70,
    visit_gap_minutes: int = 10
):

    sightings = (
        db.query(VehicleSighting)
        .filter(VehicleSighting.case_id == case_id)
        .order_by(VehicleSighting.event_time.asc())
        .all()
    )

    matched = []

    for s in sightings:
        if is_similar_plate(
            s.plate_number,
            target_plate,
            threshold=similarity_threshold
        ):
            matched.append(s)

    if not matched:
        return []

    timeline = []

    visit_gap = timedelta(minutes=visit_gap_minutes)

    # Group by camera first
    from collections import defaultdict
    camera_groups = defaultdict(list)

    for s in matched:
        camera_groups[s.camera_id].append(s)

    # Process each camera
    for cam_id, events in camera_groups.items():

        events.sort(key=lambda x: x.event_time)

        current_visit = {
            "camera_id": cam_id,
            "location": None,
            "first_seen": events[0].event_time,
            "last_seen": events[0].event_time,
            "total_detections": 1,
        }

        for i in range(1, len(events)):

            gap = events[i].event_time - events[i - 1].event_time

            if gap > visit_gap:
                timeline.append(current_visit)

                current_visit = {
                    "camera_id": cam_id,
                    "location": None,
                    "first_seen": events[i].event_time,
                    "last_seen": events[i].event_time,
                    "total_detections": 1,
                }
            else:
                current_visit["last_seen"] = events[i].event_time
                current_visit["total_detections"] += 1

        timeline.append(current_visit)

    # Fetch locations
    for entry in timeline:
        cam_obj = db.query(Camera).filter(Camera.camera_id == entry["camera_id"]).first()
        if cam_obj:
            entry["location"] = cam_obj.location

    timeline.sort(key=lambda x: x["first_seen"])

    return timeline
