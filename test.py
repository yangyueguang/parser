# import paddlehub as hub
import requests
import json
from extractor.document import Document, Page
import cv2
import base64
import fitz


def request_hub(image_path):
    def cv2_to_base64(image):
        data = cv2.imencode('.jpg', image)[1]
        return base64.b64encode(data.tostring()).decode('utf8')
    data = {'images': [cv2_to_base64(cv2.imread(image_path))]}
    headers = {"Content-type": "application/json"}
    url = "http://127.0.0.1:8866/predict/chinese_ocr_db_crnn_mobile"
    r = requests.post(url=url, headers=headers, data=json.dumps(data))
    # 打印预测结果
    print(r.json()["results"])


def parse(pdf_path, page=None):
    if page is not None:
        document = fitz.open(pdf_path)
        doc = Page.parse(document, document[page])
    else:
        doc = Document(pdf_path)
        doc.parse()
    return doc


def test():
    pdf_path = '/Users/super/Downloads/abc.pdf'
    doc = parse(pdf_path)
    d = doc.json()
