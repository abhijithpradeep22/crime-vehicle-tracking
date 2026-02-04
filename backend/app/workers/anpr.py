import re
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    use_angle_cls=False,
    lang='en',
    det=True,
    rec=True,
    show_log=False
)

def extract_plate(plate_img):
    if plate_img is None or plate_img.size == 0:
        return None, None

    result = ocr.ocr(plate_img, cls=False)

    if not result:
        return None, None

    texts = []
    confs = []

    for line in result:
        if line is None:
            continue

        for word in line:
            if word is None or len(word) < 2:
                continue

            text, conf = word[1]

            if not isinstance(text, str):
                continue

            text = re.sub(r'[^A-Z0-9]', '', text.upper())

            if len(text) >= 3:
                texts.append(text)
                confs.append(conf)

    if not texts:
        return None, None

    final_text = "".join(texts)
    final_conf = sum(confs) / len(confs)

    if len(final_text) >= 6:
        return final_text, float(final_conf)

    return None, None
