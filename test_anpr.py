import cv2
from backend.app.workers.anpr import extract_plate

img = cv2.imread("data/videos/test_plate.jpg")
plate, conf = extract_plate(img)

print("Plate: ", plate)
print("Confidence: ", conf)