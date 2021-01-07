# coding=utf-8
import re
import os
import sys
import fitz
import io
import PIL
import gzip
import fitz
import cv2
import shutil
import base64
import traceback
import requests
import numpy as np
from queue import Queue
from skimage import io
from io import BytesIO
from bottle import HTTPResponse
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor


class TemporaryDirectory(object):
    def __init__(self, name='tmp'):
        self.name = name

    def __enter__(self):
        try:
            os.mkdir(self.name)
        except:
            ...
        return self.name

    def __exit__(self, exc_type, exc_value, traceback):
        shutil.rmtree(self.name)


class BatchBase(object):
    def __init__(self):
        self.queue = Queue()
        self.pool = ThreadPoolExecutor(max_workers=10)
        self.files = []

    def start(self):
        for item in self.files:
            task = self.pool.submit(self.download, item)
            self.queue.put({"object": task})
        while not self.queue.empty():
            t = self.queue.get()
            if not t["object"].done():
                self.queue.put(t)
        return 'file_name'

    def download(self, url):
        res = requests.get(url)
        with open('data/{}.mp4'.format(url), 'wb')as f:
            for content in res.iter_content(1024):
                if content:
                    f.write(content)

    def video_downloader(self, video_url, video_name):
        size = 0
        with closing(requests.get(video_url, headers={}, stream=True)) as res:
            chunk_size = 1024
            content_size = int(res.headers['content-length'])
            if res.status_code == 200:
                sys.stdout.write(' [文件大小]:%0.2f MB\n' % (content_size / chunk_size / 1024))
            with open(video_name, 'wb') as file:
                for data in res.iter_content(chunk_size=chunk_size):
                    file.write(data)
                size += len(data)
                file.flush()
                sys.stdout.write(' [下载进度]:%.2f%%' % float(size / content_size * 100) + '\r')
                sys.stdout.flush()


def make_archive(base_dir, file_name):
    import zipfile
    with zipfile.ZipFile(file_name, 'w', compression=zipfile.ZIP_DEFLATED) as zf:
        base_dir = os.path.normpath(base_dir)
        for dir_path, dir_names, filenames in os.walk(base_dir):
            for name in sorted(dir_names) + filenames:
                if name[0] == '.':
                    continue
                path = os.path.normpath(os.path.join(dir_path, name))
                zf.write(path, path[len(base_dir) + 1:])


def response(file_name):
    body = open(file_name, 'rb') or gzip.open(file_name, 'rb')
    headers = {
        'Content-Encoding': 'gzip',
        'Content-Type': 'application/zip'
    }
    return HTTPResponse(body=body, status=200, headers=headers)


def gzip_body(out, charset='utf-8'):
    with io.BytesIO() as buf:
        with gzip.GzipFile(fileobj=buf, mode='wb') as f:
            for data in out:
                f.write(data.encode(charset) if isinstance(data, str) else data)
        return buf.getvalue()


def get_exception_message():
    with io.StringIO() as fp:
        traceback.print_exc(file=fp)
        return fp.getvalue()


def get_doc(file, password=None):
    if isinstance(file, str):
        doc = fitz.open(filename=file, filetype='pdf')
    else:
        doc = fitz.open(stream=file, filetype='pdf')
    try:
        if not doc.isPDF:
            raise ValueError('not pdf file')
        if doc.needsPass and password:
            doc.authenticate(password)
        return doc
    except:
        doc.close()
        raise


def get_sections(shadow, gap, shadow_gap=10):
    if len(shadow) <= 0: return []
    satisfy = np.where(shadow > min(shadow_gap, max(2, shadow.max() / 10)))
    indexs = np.append(np.where(np.diff(satisfy) > gap)[1] + 1, values=[sys.maxsize], axis=0)
    sections = np.split(satisfy[0], indexs, axis=0)[:-1]
    return sections


def get_middles(shadow, gap, shadow_gap=10):
    sections = get_sections(shadow, gap, shadow_gap)
    middles = [(sections[ind][-1] + sections[ind + 1][0]) // 2 for ind in range(len(sections) - 1)]
    return middles


def find_x_middles(binary: np.ndarray, col_gap=3):
    x_shadow = binary.sum(axis=0)
    return get_middles(x_shadow, col_gap)


def find_y_bottoms(binary: np.ndarray, row_gap=3):
    y_shadow = binary.sum(axis=1)
    sections = get_sections(y_shadow, row_gap, 10)
    middles = [sections[ind + 1][0] for ind in range(len(sections) - 1)]
    return middles


def find_y_middles(binary: np.ndarray, row_gap=3):
    y_shadow = binary.sum(axis=1)
    return get_middles(y_shadow, row_gap)


def find_middles(binary: np.ndarray, col_gap=3, row_gap=3):
    return find_y_middles(binary, row_gap), find_x_middles(binary, col_gap)


# 模版匹配从大图里找到这个小图对应的位置
def find_img(imgPath, litle_img):
    target = cv2.imread(imgPath)
    th, tw = litle_img.shape[:2]
    res = cv2.matchTemplate(target, litle_img, cv2.TM_CCOEFF)
    res_sorted = sorted(res.max(axis=1), reverse=True)
    res_dif = [0] * 150
    for i in range(150):
        res_dif[i] = (res_sorted[i] - res_sorted[i + 1]) * 100. / res_sorted[i + 1]
    max_lastIdx = res_dif.index(sorted(res_dif, reverse=True)[0])
    idx = np.argwhere(res >= res_sorted[max_lastIdx])
    idx_set = set(np.unique(idx[:, 0]))
    for i in range(len(idx)):
        if idx[i, 0] in idx_set:
            idx_set.remove(idx[i, 0])
            tl = (idx[i, 1], idx[i, 0])
            br = (tl[0] + tw, tl[1] + th)
            cv2.rectangle(target, tl, br, (0, 0, 0), 1)
    cv2.imwrite(imgPath, target)


def layout_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    for page in doc:
        img = page.newShape()
        disp = fitz.Rect(page.CropBoxPosition, page.CropBoxPosition)
        img.drawRect(page.rect + disp)
        img.finish(color=None, fill=None)
        blks = page.getTextBlocks()
        for b in blks:
            img.drawRect(fitz.Rect(b[:4]) + disp)
            color = (1, 0 if b[-1] == 1 else 1, 0)
            img.finish(width=2, color=color)
        draws = page.getDrawings()
        for j in draws:
            r = j['rect'].irect
            cv2.rectangle(img, r[:2], r[2:], (255, 0, 0), 2)
        image_list = page.getImageList()
        for ig in image_list:
            image_box = page.getImageBbox(ig[-2])
            cv2.rectangle(img, image_box.irect[:2], image_box.irect[2:4], (255, 0, 0), 2)
        img.commit()
    doc.save("layout.pdf", garbage=4, deflate=True, clean=True)


def file_to_base64(file_data: bytes):
    return base64.b64encode(file_data).decode('utf-8')


def base64_to_data(content: bytes):
    return base64.b64decode(content)


class PDF_OCR(object):
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.pic_path = []
        self.imgs = []

    def pdf2img(self, out_path):
        doc = fitz.open(self.pdf_path)
        for idx, page in enumerate(doc):
            image_matrix = fitz.Matrix(fitz.Identity).preScale(4, 4)
            pix = page.getPixmap(alpha=False, matrix=image_matrix)
            pic_path = os.path.join(out_path, f"{str(idx + 1)}.png")
            pix.writePNG(pic_path)
            self.pic_path.append(pic_path)
            print(pic_path)

    def merge_picture_to_pdf(self, imglist: list, out: str):
        doc = fitz.open()
        for i, f in enumerate(imglist):
            img = fitz.open(f)
            rect = img[0].rect
            pdfbytes = img.convertToPDF()
            img.close()
            tmp = fitz.open("tmp", pdfbytes)
            page = doc.newPage(width=rect.width, height=rect.height)
            page.showPDFpage(rect, tmp, 0)
        doc.save(out)

    def get_img(self, page: fitz.Page, out: str):
        pm = page.getPixmap(matrix=fitz.Matrix(3, 3).preRotate(0), alpha=False)
        getpngdata = pm.getImageData(output="png")
        image_array = np.frombuffer(getpngdata, dtype=np.uint8)
        img_cv = cv2.imdecode(image_array, cv2.IMREAD_ANYCOLOR)
        cv2.imwrite(out, img_cv)

    def pixmap2array(self, page):
        links = page.getLinks()
        for link in page.links():
            ...
        for annot in page.annots():
            ...
        for field in page.widgets():
            ...
        clip = fitz.Rect(0, 0, 1, 1)  # the area we want
        mat = fitz.Matrix(3, 3).preRotate(0)
        pix = page.getPixmap(matrix=mat, clip=clip)

        pix = page.getPixmap()
        cspace = pix.colorspace
        if cspace is None:
            mode = "L"
        elif cspace.n == 1:
            mode = "L" if pix.alpha == 0 else "LA"
        elif cspace.n == 3:
            mode = "RGB" if pix.alpha == 0 else "RGBA"
        else:
            mode = "CMYK"
        img = Image.frombytes(mode, (pix.width, pix.height), pix.samples)
        img = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2BGR)
        return img

    def draw_shape(self, x0, y0, x1, y1, width, height):
        outpdf = fitz.open()
        outpage = outpdf.newPage(width=width, height=height)
        shape = outpage.newShape()
        shape.drawLine((x0, y0), (x1, y1))
        shape.drawRect(x0, y0, x1, y1)
        shape.finish()
        shape.commit()
        outpdf.save("ab.pdf")

    def get_catelogs(self, doc):
        toc = doc.getToC()
        return toc

    def extract_image(self, doc):
        for page_index in range(len(doc)):
            page = doc[page_index]
            image_list = page.getImageList()
            if image_list:
                print(f"[+] Found a total of {len(image_list)} images in page {page_index}")
            else:
                print("[!] No images found on page", page_index)
            for image_index, img in enumerate(image_list, start=1):
                xref, _, width, height = img[:4]
                base_image = doc.extractImage(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                image = PIL.Image.open(BytesIO(image_bytes))
                image.save(open(f"result{page_index + 1}_{image_index}.{image_ext}", "wb"))

    def synthesis(self, out: str):
        doc = fitz.open()
        for i in self.imgs:
            pdfbytes = i.convertToPDF()
            imgpdf = fitz.open("temp", pdfbytes)
            doc.insertPDF(imgpdf)
        doc.save(out)
        doc.close()

    def merge_pdfs(self, files: list, out: str):
        doc = fitz.open(files[0])
        for f in files[1:]:
            doc.insertPDF(docsrc=fitz.open(f))
        doc.save(out)

    def deal_page_objects(self, doc: fitz.Document):
        toc = doc.PDFCatalog()
        for page in doc:
            cont = b""
            for xref in page._getContents():
                part = doc.xrefStream(xref)
                print(part)
                cont += part