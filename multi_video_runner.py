from datetime import datetime

from backend.app.workers.video_processor import process_video
from backend.app.db.session import SessionLocal
from backend.app.workers.plate_aggregator import aggregate_case_plates


VIDEOS = [
    ("data/videos/IMG_1178.mp4", "CAM_001", datetime(2026, 2, 4, 8, 30, 0)),
    ("data/videos/IMG_1179.mp4", "CAM_002", datetime(2026, 2, 4, 10, 15, 0)),
    ("data/videos/IMG_1180.mp4", "CAM_003", datetime(2026, 2, 4, 13, 45, 0)),
    ("data/videos/IMG_1182.mp4", "CAM_004", datetime(2026, 2, 4, 17, 10, 0)),
]

CASE_ID = 1


def main():

    print("\n===== MULTI-CAMERA PROCESSING STARTED =====\n")

    
    for video_path, camera_id, start_time in VIDEOS:

        print(f"\nProcessing {video_path} as {camera_id}")
        print(f"Video start time: {start_time}")

        process_video(
            video_path=video_path,
            case_id=CASE_ID,
            camera_id=camera_id,
            video_start_time=start_time
        )

    print("\nAll videos processed.\n")

    # Run aggregation
    db = SessionLocal()
    try:
        print("===== AGGREGATING RESULTS =====\n")
        results = aggregate_case_plates(db, case_id=CASE_ID)

        print(f"Total clusters found: {len(results)}\n")

        for idx, r in enumerate(results, start=1):
            print(f"Cluster #{idx}")
            print(f"  Primary Plate : {r['primary_plate']}")
            print(f"  Variants      : {r['all_variants']}")
            print(f"  Count         : {r['count']}")
            print(f"  First Seen    : {r['first_seen']}")
            print(f"  Last Seen     : {r['last_seen']}")
            print(f"  Cameras       : {r['cameras']}")
            print("-" * 50)

    finally:
        db.close()
        print("\nDatabase connection closed.")


if __name__ == "__main__":
    main()
