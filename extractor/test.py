# import paddlehub as hub
import requests
import json
from .document import Document, Page
import matplotlib.pyplot as plt
import cv2
import numpy as np
import base64
import fitz

def recognize_hub(image_path):
    np_images = [cv2.imread(image_path)]
    # ocr = hub.Module(name="chinese_ocr_db_crnn_server")
    # results = ocr.recognize_text(
    #     images=np_images,  # 图片数据，ndarray.shape 为 [H, W, C]，BGR格式；
    #     use_gpu=False,  # 是否使用 GPU；若使用GPU，请先设置CUDA_VISIBLE_DEVICES环境变量
    #     output_dir='./',  # 图片的保存路径，默认设为 data_result；
    #     visualization=False,  # 是否将识别结果保存为图片文件；
    #     box_thresh=0.5,  # 检测文本框置信度的阈值；
    #     text_thresh=0.5)  # 识别中文文本置信度的阈值；
    # print(results)


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
        doc = Document.parse(pdf_path)
    return doc


import utils
def cat(data):
    return utils.file_to_base64(data)


def test():
    pdf_path = '../data_result/ddd.pdf'
    doc = parse(pdf_path)
    d = doc.json()
    import json
    json_file = '../data_result/a.json'
    with open(json_file, 'w') as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=4))
    with open(json_file, 'r') as f:
        abc = Document.load(json.loads(f.read()))
    # ad = doc.html()
    # with open('../data_result/c.html', 'w') as f:
    #     f.write(ad)
    # doc.save_to_docx('../data_result/c.docx')
    print('over')


def abcd(name):
    print(name * 10)
    print('==' * 10)
    print('over')