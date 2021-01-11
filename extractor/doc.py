# coding=utf-8
import re
import math
import fitz
import json
import numpy as np
import pandas as pd


class Serializable(object):

    @property
    def text(self) -> str:
        pass


    def cat_binary(self, binary):
        pass


class Box(Serializable):
    def __init__(self, chars: list, *args):
        super(Box, self).__init__()

    @property
    def width(self) -> float:
        return abs(self.r - self.x)

    @width.setter
    def width(self, w: float):
        self.r = self.x + w

    @property
    def height(self) -> float:
        return abs(self.b - self.y)

    @height.setter
    def height(self, h: float):
        self.b = self.y + h

    @property
    def center(self):
        return (self.x + self.r) / 2, (self.y + self.b) / 2

    @property
    def text(self) -> str:
        return ''.join([c.str for c in self.chars])

    @property
    def is_line(self):
        return isinstance(self, Table) and self.width < 8 or self.height < 8

    @property
    def rect(self) -> tuple:
        return math.floor(self.x), math.floor(self.y), math.ceil(self.r), math.ceil(self.b)

    def include_point(self, x: float, y: float):
        self.x = min(self.x, x)
        self.y = min(self.y, y)
        self.r = max(self.r, x)
        self.b = max(self.b, y)

    def include_box(self, box):
        self.include_point(box.x, box.y)
        self.include_point(box.r, box.b)
        return self

    def intersect(self, b):
        if not self.is_intersect(b):
            return Box([])
        return Box([], max(self.x, b.x), max(self.y, b.y), min(self.r, b.r), min(self.b, b.b))

    def is_intersect(self, b):
        return min(self.r, b.r) > max(self.x, b.x) and min(self.b, b.b) > max(self.y, b.y)


class BaseElement(Box):
    def __init__(self, page, lines: list, *args):
        super(BaseElement, self).__init__([c for l in lines for c in l.chars], *args)
        self.lines = lines
        self.page = page
        self.parent = None
        self.children = []
        self._blocks = []


    @property
    def global_y(self) -> float:
        return (self.page.y if self.page else 0) + self.y

    @classmethod
    def load(cls, j: Dict):
        rect = [j.x, j.y, j.r, j.b]
        text_line = TextLine([Box([Char(i, *rect) for i in j.str], *rect)], *rect)
        p = cls(None, [text_line], j.x, j.y, j.r, j.b)
        return p

    @property
    def text(self) -> str:
        if not self.chars:
            self.chars = [c for l in self.lines for c in l.chars]
        return ''.join([c.str for c in self.chars])


class Char(Box):
    def __init__(self, value: str = '', *args):
        super(Char, self).__init__(None, *args)
        self.color = 0
        self.font = None
        self.str = value

    @property
    def text(self) -> str:
        return self.str

    def __str__(self):
        return json.dumps(self.json(), ensure_ascii=False)

    def __eq__(self, other):
        return super(Char, self).__eq__(other) and self.str == other.str


class TextLine(Box):
    def __init__(self, boxs: [Box], *args):
        super(TextLine, self).__init__([c for box in boxs for c in box.chars], *args)
        self.boxs = boxs

    def json(self) -> dict:
        pass

    @classmethod
    def load(cls, j: Dict):
        return cls([Box.load(Dict(i)) for i in j.boxs], j.x, j.y, j.r, j.b)


class Table(BaseElement):
    def __init__(self, page, lines: [TextLine], *args):
        super(Table, self).__init__(page, lines, *args)
        self.rows = len(lines)
        self.cols = len(lines[0].boxs) if self.rows > 0 else 0
        self.page_number = 0
        self.grid = None
        self.binary = None
        self.boxs = []

    @property
    def cells(self) -> [Box]:
        return [cell for row in self.lines for cell in row.boxs]

    @property
    def matrix(self):
        matrix = [[cell.text for cell in line.boxs] for line in self.lines]
        res = pd.DataFrame(data=matrix)
        return res

    def add_edges(self):
        if self.grid is None:
            return
        self.grid[:3, :] = self.grid[-3:, :] = self.grid[:, :3] = self.grid[:, -3:] = 1


    @property
    def html(self) -> str:
        pass


class Line(Table):
    def __init__(self, page, _, *args):
        super(Line, self).__init__(page, [], *args)


class Title(BaseElement):
    def __init__(self, page, lines: list, *args):
        super(Title, self).__init__(page, lines, *args)
        self.level = len(re.split(r'\.', re.search(r'([\d\.]*)', self.text).group(0).strip('.')))


class Paragraph(BaseElement):
    def __init__(self, page, lines: [TextLine], *args):
        super(Paragraph, self).__init__(page, lines, *args)

class Header(BaseElement):
    def __init__(self, page, lines: [TextLine], *args):
        super(Header, self).__init__(page, lines, *args)


class Footer(BaseElement):
    def __init__(self, page, lines: [TextLine], *args):
        super(Footer, self).__init__(page, lines, *args)


class Catelog(BaseElement):
    def __init__(self, page, lines: [TextLine], *args):
        super(Catelog, self).__init__(page, lines, *args)


class Graph(BaseElement):
    def __init__(self, page, lines: [TextLine], *args):
        super(Graph, self).__init__(page, lines, *args)
        self.img_id = None

    def save(self, file_name: str):
        pass

    def show(self):
        pass




class Page(Box):
    def __init__(self, doc: fitz.Document, meta_list: list, index: int, *args):
        super(Page, self).__init__([c for l in meta_list for c in l.chars], *args)
        self.meta_list = meta_list
        self.doc = doc
        self.index = index
        self.rotate = 0
        self.scale = 1
        self.own = self.doc[self.index]
        self.is_ocr = False
        self.grid = None  # 网格线二进制
        self.binary = None  # 实体二进制



    @classmethod
    def parse(cls, doc: fitz.Document, page: fitz.Page, index=0, global_y=0):
        pass



    def show(self):
        pass

    def save(self, file_name: str):
        self.getPixmap().writePNG(file_name)

    @property
    def text(self) -> str:
        return '\n'.join([m.text for m in self.meta_list])


    def drawRect(self, rect, color=None, fill=None):
        pass

    def getText(self, option="text", clip=None, flags=None):
        return self.own.getText(option, clip, flags)

    def getTextPage(self, clip=None, flags=0):
        return self.own.getTextPage(clip, flags)

    def getPixmap(self, matrix=fitz.Matrix(3, 3).preRotate(0), clip=None):
        return self.own.getPixmap(matrix, clip=clip)

    def annots(self, types=None):
        return self.own.annots(types)

    def widgets(self, types=None):
        return self.own.widgets(types)

    def links(self, kinds=None):
        return self.own.links(kinds)

    def getLinks(self):
        return self.own.getLinks()

    def updateLink(self, lnk):
        return self.own.updateLink(lnk)

    def insertLink(self, lnk, mark=True):
        self.own.insertLink(lnk, mark)

    def insertText(self, point, text, fontsize=11, color=None, fill=None):
        return self.own.insertText(point, text, fontsize, color=color, fill=fill)

    def insertTextbox(self, rect, buffer, fontsize=11, color=None, fill=None):
        return self.own.insertTextbox(rect, buffer, fontsize=fontsize, color=color, fill=fill)

    def insertImage(self, rect, filename=None, pixmap=None, stream=None):
        return self.own.insertImage(rect, filename, pixmap, stream)

    def newShape(self):
        return fitz.utils.Shape(self.own)

    def searchFor(self, text, quads=False, clip=None):
        return self.own.searchFor(text, quads=quads, clip=clip)

    def writeText(self, rect=None, writers=None, color=None):
        return self.own.writeText(rect, writers, color=color)


class Document(fitz.Document):
    def __init__(self, file, password: str = None, **kwargs):

    @classmethod
    def load_from_images(cls, imgs: list):
        pass

    def parse(self):
        'pass every page'

    def save_layout(self, layout_path: str):
        pass

    def json(self) -> dict:
        serialized_document = {
            'metadata': self.metadata,
            'pages': [page.json() for page in self.pages]
        }
        return serialized_document

    @property
    def text(self):
        return '\f'.join([p.text for p in self.pages])

    @classmethod
    def load(cls, json_dict):
        page_list = [Page.load(Dict(j)) for j in json_dict['pages']]
        document = cls(None)
        document.pages = page_list
        document.metadata = json_dict['metadata']
        return document

    def save(self, filename, garbage=0, deflate=0, clean=0):
        super(Document, self).save(filename, garbage=garbage, deflate=deflate, clean=clean)

    def getToC(self):
        return super(Document, self).getToC()

    def setToC(self, toc):
        super(Document, self).setToC(toc)

    def PDFCatalog(self):
        return super(Document, self).PDFCatalog()

    def newPage(self, pno=-1, width=595, height=842):
        return super(Document, self).newPage(pno, width, height)

    def insertPDF(self, doc: fitz.Document, from_page=-1):
        super(Document, self).insertPDF(doc, from_page)

    def remove_hidden(self):
        pass

    # 写入word文本文档
    def save_to_docx(self, name):
       pass

    def html(self) -> str:
        pass


class ImageLayout(Serializable):
    def __init__(self, img_path, img=None, page=None):
        pass

    def find_graph(self, gray: np.ndarray) -> list:
        pass

    # 布局分析
    def layout_parse(self):
        pass

    def fill_boxs(self, boxs: list):
        pass