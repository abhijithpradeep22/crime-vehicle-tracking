from datetime import datetime
from multiprocessing import Process, Manager

from backend.app.workers.video_processor import process_video


TARGET_PLATE = "KL45R7008"

VIDEOS = [
    ("data/videos/IMG_1178.mp4", "CAM_001", datetime(2026, 2, 4, 8, 30, 0)),
    ("data/videos/IMG_1179.mp4", "CAM_002", datetime(2026, 2, 4, 10, 15, 0)),
    ("data/videos/IMG_1180.mp4", "CAM_003", datetime(2026, 2, 4, 13, 45, 0)),
    ("data/videos/IMG_1182.mp4", "CAM_004", datetime(2026, 2, 4, 17, 10, 0)),
]

CASE_ID = 1


def main():

    print("\n===== LIVE TARGET TRACKING MODE =====")
    print(f"Tracking Target Plate: {TARGET_PLATE}")
    print("======================================\n")

    manager = Manager()
    shared_state = manager.dict()

    # Initialize shared latest known location
    shared_state["latest_event_time"] = None
    shared_state["latest_camera"] = None
    shared_state["latest_location"] = None

    processes = []

    for video_path, camera_id, start_time in VIDEOS:

        p = Process(
            target=process_video,
            args=(
                video_path,
                CASE_ID,
                camera_id,
                start_time,
                TARGET_PLATE,
                shared_state,
            ),
        )

        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    print("\n===== TRACKING COMPLETED =====")

    if shared_state["latest_event_time"]:
        print("\n===== FINAL LATEST KNOWN LOCATION =====")
        print(f"Camera   : {shared_state['latest_camera']}")
        print(f"Location : {shared_state['latest_location']}")
        print(f"Time     : {shared_state['latest_event_time']}")
        print("=======================================\n")


if __name__ == "__main__":
    main()
