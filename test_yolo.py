from backend.app.workers.video_processor import process_video

process_video(
    video_path="data/videos/IMG_1180.mp4",
    case_id=1,          
    camera_id="CAM_001" 
)

print("YOLO processing finished")
