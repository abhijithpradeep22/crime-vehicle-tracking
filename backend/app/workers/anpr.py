import cv2
import re
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_angle_cls = True,
    lang = 'en'
)

PLATE_REGEX = r'^[A_Z]{2}\d{2}[A-Z]{1,2}\d{4}$'

def extract_plate(plate_img):
    if plate_img is None or plate_img.size == 0:
        return None, None
    
    result = ocr.ocr(plate_img)
    
    if not result or result[0] is None:
        return None, None
    
    for line in result[0]:
        text, conf = line[1]

        text = (
            text.upper()
            .replace(" ", "")
            .replace("-", "")
        )

        if  re.fullmatch(PLATE_REGEX, text) and conf > 0.6:
            return text, float(conf)
        
    return None, None