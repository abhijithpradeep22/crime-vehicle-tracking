from sqlalchemy.orm import Session
from backend.app.models.sighting import VehicleSighting
from backend.app.workers.plate_aggregator import normalize_plate
from collections import defaultdict


def search_vehicle(
        db: Session,
        target_plate: str,
        start_time,
        end_time,
        case_id: int | None = None
):
    
    #Search for a specific vehicle in a given time window

    normalized_target = normalize_plate(target_plate)

    if not normalized_target:
        return None
    
    query = (
        db.query(VehicleSighting)
        .filter(VehicleSighting.plate_number.isnot(None))
        .filter(VehicleSighting.event_time >= start_time)
        .filter(VehicleSighting.event_time <= end_time)
    )

    if case_id is not None:
        query = query.filter(VehicleSighting.case_id == case_id)

    sightings = query.all()

    if not sightings:
        return None
    
    matched = []

    for s in sightings:
        norm = normalize_plate(s.plate_number)
        if norm == normalized_target:
            matched.append(s)
    
    if not matched:
        return None
    
    # Aggregate result for this vehicle
    event_times = [s.event_time for s in matched]
    cameras = sorted(set(s.camera_id for s in matched))

    timeline = sorted(
        [
            {
                "event_time": s.event_time,
                "camera_id": s.camera_id,
                "snapshot": s.image_path
            }
            for s in matched

        ],
        key=lambda x: x["event_time"]
    
    )

    return{
        "plate": normalized_target,
        "count": len(matched),
        "first_seen": min(event_times),
        "last_seen": max(event_times),
        "cameras": cameras,
        "timeline": timeline
    }
    
