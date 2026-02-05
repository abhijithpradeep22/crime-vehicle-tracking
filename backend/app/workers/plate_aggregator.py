import re
from collections import Counter, defaultdict
from sqlalchemy.orm import Session
from backend.app.models.sighting import VehicleSighting

DIGIT_MAP = {
    'O': '0',
    'Q': '0',
    'I': '1',
    'L': '1',
    'Z': '2',
    'S': '5',
    'B': '8'
}

LETTER_MAP = {
    '0': 'O',
    '1': 'I',
    '2': 'Z',
    '5': 'S',
    '8': 'B'
}

def normalize_plate(raw: str) -> str:
    #Normalize OCR plate string in a format-aware way

    if not raw:
        return ""
    
    text = re.sub(r'[^A-Z0-9]', '', raw.upper())

    chars = list(text)
    normalized = []

    #Letter - Digit, Digit - Letter conversions
    for i, ch in enumerate(chars):
        if i < 2:  #state code
            normalized.append(LETTER_MAP.get(ch, ch))
        elif 2 <= i < 4:  #RTO code (digits)
            normalized.append(DIGIT_MAP.get(ch, ch))
        elif 4 <= i < 6:  #series
            normalized.append(LETTER_MAP.get(ch, ch))
        else:  #last numbers
            normalized.append(DIGIT_MAP.get(ch, ch))

    return "".join(normalized)

#Aggregation

def aggregate_case_plates(db: Session, case_id: int):

    sightings = (
        db.query(VehicleSighting)
        .filter(VehicleSighting.case_id == case_id)
        .filter(VehicleSighting.plate_number.isnot(None))
        .all()
    )

    if not sightings:
        return []
    
    plate_groups = defaultdict(list)

    for s in sightings:
        norm = normalize_plate(s.plate_number)
        if len(norm) >= 6:
            plate_groups[norm].append(s)

    aggregated = []

    for plate, records in plate_groups.items():
        cameras = []
        timestamps = []

        for r in records:
            cameras.append(r.camera_id)
            timestamps.append(r.detected_at)

        aggregated.append({
            "final_plate": plate,
            "count": len(records),
            "first_seen": min(timestamps),
            "last_seen": max(timestamps),
            "cameras": sorted(set(cameras))
        })

    aggregated.sort(key = lambda x: x["count"], reverse=True)
    #Most accurately detected plates
    aggregated = [a for a in aggregated if a["count"] >= 3]

    return aggregated


