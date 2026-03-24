import re
from collections import Counter, defaultdict
from sqlalchemy.orm import Session
from backend.app.models.sighting import VehicleSighting
from difflib import SequenceMatcher


def normalize_plate(raw: str) -> str:
    
    if not raw:
        return ""

    text = re.sub(r'[^A-Z0-9]', '', raw.upper())
    return text


def similarity_score(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()


def is_similar_plate(a: str, b: str, threshold: float = 0.80) -> bool:
    if not a or not b:
        return False
    return similarity_score(a, b) >= threshold


def resolve_plate_variants(normalized_versions: list[str]):
    """
    Preserve all variants with their counts.
    Primary plate = most frequent.
    """

    if not normalized_versions:
        return None, []

    counter = Counter(normalized_versions)

    sorted_variants = sorted(
        counter.items(),
        key=lambda x: x[1],
        reverse=True
    )

    primary_plate = sorted_variants[0][0]

    variants = [
        {"plate": plate, "count": count}
        for plate, count in sorted_variants
    ]

    return primary_plate, variants


def aggregate_case_plates(db: Session, case_id: int):

    sightings = (
        db.query(VehicleSighting)
        .filter(VehicleSighting.case_id == case_id)
        .filter(VehicleSighting.plate_number.isnot(None))
        .all()
    )

    if not sightings:
        return []

    buckets = defaultdict(list)

    for s in sightings:
        norm = normalize_plate(s.plate_number)

        # bucket by first two characters (state code)
        key = norm[:2] if len(norm) >= 2 else norm
        buckets[key].append((s, norm))

    aggregated = []

    for bucket in buckets.values():

        used = set()

        for i, (s_obj, s_norm) in enumerate(bucket):

            if s_obj.id in used:
                continue

            group_objs = []
            group_norms = []

            for other_obj, other_norm in bucket:

                if other_obj.id in used:
                    continue

                if is_similar_plate(s_norm, other_norm):
                    group_objs.append(other_obj)
                    group_norms.append(other_norm)
                    used.add(other_obj.id)

            if not group_objs:
                continue

            cameras = sorted(set(r.camera_id for r in group_objs))
            times = [r.event_time or r.detected_at for r in group_objs]

            primary_plate, variants = resolve_plate_variants(group_norms)

            aggregated.append({
                "primary_plate": primary_plate,
                "all_variants": variants,
                "count": len(group_objs),
                "first_seen": min(times),
                "last_seen": max(times),
                "cameras": cameras
            })

    aggregated.sort(key=lambda x: x["count"], reverse=True)
    return aggregated