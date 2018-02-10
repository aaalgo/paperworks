from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code39
from reportlab.lib.pagesizes import letter, A4, landscape
from django.utils import timezone
from sklearn.linear_model import LinearRegression
from skimage import measure
from flow.models import *
from params import *
import numpy as np
import cv2

def create_pdf (batch):
    path = 'jobs/%04d-%s.pdf' % (batch.id, timezone.localtime(batch.timestamp).strftime('%Y%m%d%H%M%S'))
    pdf = canvas.Canvas(path, pagesize=PAPER_SIZE, bottomup=0)
    return pdf

'''
    ++ B ++




    +     +
    ++ B ++
'''
def barcode_encode (batch_page):
    return '%d %d' % (batch_page.batch.id, batch_page.page.id)

def barcode_decode (symbol):
    x, y = symbol.split(' ')
    return int(x), int(y[0])

W, H = PAPER_SIZE
X0, Y0 = MARGIN
X1, Y1 = W - X0, H - Y0
GAP = ANCHOR_SIZE * 0.5
RELAX = 0.3 * GAP


ANCHORS = []
#ANCHOR_LINES = []
SCALE_BOXES = []

IMAGE_X0 = X0
IMAGE_X1 = W - X0
IMAGE_Y0 = Y0 + BAR_HEIGHT + RELAX 
IMAGE_Y1 = Y1 - BAR_HEIGHT - RELAX 
IMAGE_W = IMAGE_X1 - IMAGE_X0
IMAGE_H = IMAGE_Y1 - IMAGE_Y0
SCALE_X = X0 + 3 * (ANCHOR_SIZE + RELAX) + GAP
BAR_X = SCALE_X + 2 * (SCALE_W + ANCHOR_SIZE) + ANCHOR_SIZE

class LetterSizeLandscapeLayout:
    WIDTH



def gen_anchors ():
    for X, Y, dx, dy, dir,n in [(X0+GAP, Y0+GAP, 1, 1, 0, 3),
                              (X1-GAP, Y0+GAP, -1, 1, 0, 4),
                              (X0+GAP, Y1-GAP, 1, -1, 0, 3),
                              (X1-GAP, Y1-GAP, -1, -1, 0, 3)]:
        for s in range(n):
            x = X + dx * s * (1-dir) * (ANCHOR_SIZE + RELAX)
            y = Y + dy * s * dir * (ANCHOR_SIZE + RELAX)
            ANCHORS.append([x, y])
            #ANCHOR_LINES.append((x-GAP, y, x+GAP, y))
            #ANCHOR_LINES.append((x, y-GAP, x, y+GAP))

gen_anchors()

def draw_anchors (pdf):
    pdf.setStrokeColorRGB(0,0,0)
    pdf.setFillColorRGB(0,0,0)
    for x, y in ANCHORS:
        pdf.circle(x, y, GAP, 1, 1)
        #pdf.line(x0, y0, x1, y1)
    pass

def gen_scale_boxes ():
    SCALE_X = X0 + 3 * ANCHOR_SIZE + GAP
    for y, n in [(Y0, 2), (Y1-BAR_HEIGHT, 4)]:
        x = SCALE_X 
        for _ in range(n):
            SCALE_BOXES.append([x, y, SCALE_W, BAR_HEIGHT])
            x += SCALE_W + ANCHOR_SIZE
            pass

gen_scale_boxes()


def draw_grayscale (pdf, x, y, width, height, steps):
    step = width / steps
    for i in range(steps):
        C = (1.0 - MIN_COLOR) * i/steps + MIN_COLOR
        pdf.setStrokeColorRGB(C,C,C)
        pdf.setFillColorRGB(C,C,C)
        pdf.rect(x + i * step, y, step, height, fill=1)
        pass

def draw_grayscales (pdf):
    for x, y, w, h in SCALE_BOXES:
        draw_grayscale(pdf, x, y, w, h, 32)
        pass

def render_page (pdf, batch_page):
    print(W, H, X0, Y0, X1, Y1)
    # batch-page-
    draw_grayscales(pdf)

    barcode=code39.Extended39(barcode_encode(batch_page),barWidth=BAR_WIDTH,barHeight=BAR_HEIGHT)
    pdf.setStrokeColorRGB(0,0,0)
    pdf.setFillColorRGB(0,0,0)
    barcode.drawOn(pdf, BAR_X, Y0)
    draw_anchors(pdf)

    #pdf.rect(IMAGE_X0, IMAGE_Y0, IMAGE_X1-IMAGE_X0, IMAGE_Y1-IMAGE_Y0)
    print(Y0, IMAGE_Y0, GAP, RELAX)

    #batch = batch_page.batch
    page = batch_page.page

    for image in Image.objects.filter(page=page):

        #bm = cv2.imread(image.path, cv2.IMREAD_GRAYSCALE).astype(np.float32)
        #cv2.normalize(bm, None, MIN_COLOR, 1.0, cv2.NORM_MINMAX)
        #w0, h0 = image.width, image.height
        #w, h -> IMAGE_W, IMAGE_H
        #
        #ratio = min(IMAGE_H/h0, IMAGE_W/w0, MAX_SCALE)
        ratio = 1.0 / PPI * inch

        pdf.drawImage(image.embed_path(image.rotate), image.page_x, image.page_y, width=image.page_w, height=image.page_h)

    pass


def create_scales_pdf (path):
    W, H = min(PAPER_SIZE), max(PAPER_SIZE)
    pdf = canvas.Canvas(path, pagesize=(W, H), bottomup=0)

    y = Y0 + ANCHOR_SIZE
    for _ in range(8):
        x = X0 + ANCHOR_SIZE
        for _ in range(2):
            draw_grayscale(pdf, x, y, SCALE_W * 2, BAR_HEIGHT, 32)
            x += SCALE_W * 2 + ANCHOR_SIZE
            pass
        y += BAR_HEIGHT + ANCHOR_SIZE
        pass
    pdf.showPage()
    pdf.save()
    pass


def detect_circles (image, off):
    image = cv2.GaussianBlur(image, (9, 9), 0)
    image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX)
    binary = image < 50
    labels = measure.label(binary, background=0)

    centers = []
    x0, y0 = off
    for box in measure.regionprops(labels):
        if box.area < 2000:
            continue
        #print("\t", box.area, box.centroid)
        y, x = box.centroid
        centers.append([x0+x, y0+y])
    return centers

def detect_anchors (image):
    H, W = image.shape[:2]
    h = H//4
    w = W//4
    blocks = [(0, 0),
              (W-w, 0),
              (0, H-h),
              (W-w, H-h)]
    anchors = []
    for i, (x, y) in enumerate(blocks):
        aoi = image[y:(y+h), x:(x+w)]
        anchors.append(detect_circles(aoi, (x, y)))
        pass
    return anchors

def rotate_clockwise (image):
    image = cv2.transpose(image)
    return cv2.flip(image, 1)

def rotate_counterclockwise (image):
    image = cv2.transpose(image)
    return cv2.flip(image, 0)

def rotate_normalize (image):
    anchors = detect_anchors(image)
    if len(anchors[0]) == 4:
        return rotate_clockwise
    elif len(anchors[3]) == 4:
        return rotate_counterclockwise
    pass

def calibrate (image):
    anchors = detect_anchors(image)
    assert len(anchors[1]) == 4
    X = np.array(sum(anchors, []), dtype=np.float32)
    y1 = np.array([x * CALIB_PPI/inch for x , _ in ANCHORS], dtype=np.float32)
    y2 = np.array([y * CALIB_PPI/inch for _ , y in ANCHORS], dtype=np.float32)
    reg_x = LinearRegression()
    reg_y = LinearRegression()
    reg_x.fit(X, y1)
    reg_y.fit(X, y2)
    #print(reg_x.coef_, reg_x.intercept_)
    #print(reg_y.coef_, reg_y.intercept_)
    affine = np.zeros((2,3), dtype=np.float32)
    affine[0, :2] = reg_x.coef_
    affine[0, 2] = reg_x.intercept_
    affine[1, :2] = reg_y.coef_
    affine[1, 2] = reg_y.intercept_
    return affine



