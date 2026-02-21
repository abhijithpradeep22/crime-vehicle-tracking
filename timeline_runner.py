from backend.app.db.session import SessionLocal
from backend.app.workers.timeline_service import build_vehicle_timeline


CASE_ID = 1
TARGET_PLATE = "KL45R7008"


def main():

    db = SessionLocal()

    try:
        timeline = build_vehicle_timeline(
            db=db,
            case_id=CASE_ID,
            target_plate=TARGET_PLATE
        )

        print("\n===== VEHICLE MOVEMENT TIMELINE =====\n")

        if not timeline:
            print("No sightings found.")
            return

        for idx, entry in enumerate(timeline, start=1):

            print(f"Stop #{idx}")
            print(f"Camera ID        : {entry['camera_id']}")
            print(f"Location         : {entry['location']}")
            print(f"First Seen       : {entry['first_seen']}")
            print(f"Last Seen        : {entry['last_seen']}")
            print(f"Total Detections : {entry['total_detections']}")
            print("-" * 50)

    finally:
        db.close()


if __name__ == "__main__":
    main()
