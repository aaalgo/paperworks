from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code39
from django.utils import timezone
from flow.models import *
from params import *

def create_pdf (batch):
    path = 'jobs/%04d-%s.pdf' % (batch.id, timezone.localtime(batch.timestamp).strftime('%Y%m%d%H%M%S'))
    pdf = canvas.Canvas(path, pagesize=PAPER_SIZE, bottomup=0)
    return pdf

'''
    ++ B ++




    +     +
    ++ B ++
'''
W, H = PAPER_SIZE
X0, Y0 = MARGIN
X1, Y1 = W - X0, H - Y0
GAP = ANCHOR_SIZE * 0.5
RELAX = 0.5 * GAP

def barcode_encode (batch_page):
    return '%d %d' % (batch_page.batch.id, batch_page.page.id)

ANCHORS = []
ANCHOR_LINES = []

IMAGE_X0 = X0
IMAGE_X1 = W - X0
IMAGE_Y0 = Y0 + BAR_HEIGHT + RELAX 
IMAGE_Y1 = Y1 - BAR_HEIGHT - RELAX 
IMAGE_W = IMAGE_X1 - IMAGE_X0
IMAGE_H = IMAGE_Y1 - IMAGE_Y0
SCALE_X = X0 + 3 * ANCHOR_SIZE + GAP
BAR_X = SCALE_X + 2 * (SCALE_W + ANCHOR_SIZE) + SCALE_W

def gen_anchors ():
    for X, Y, dx, dy, dir,n in [(X0+GAP, Y0+GAP, 1, 1, 0, 3),
                              (X1-GAP, Y0+GAP, -1, 1, 0, 3),
                              (X0+GAP, Y1-GAP, 1, -1, 0, 3),
                              (X1-GAP, Y1-GAP, -1, -1, 0, 3)]:
        for s in range(n):
            x = X + dx * s * (1-dir) * ANCHOR_SIZE
            y = Y + dy * s * dir * ANCHOR_SIZE
            ANCHORS.append((x, y))
            ANCHOR_LINES.append((x-GAP, y, x+GAP, y))
            ANCHOR_LINES.append((x, y-GAP, x, y+GAP))
gen_anchors()

def draw_anchors (pdf):
    pdf.setStrokeColorRGB(0,0,0)
    for x0, y0, x1, y1 in ANCHOR_LINES:
        pdf.line(x0, y0, x1, y1)
    pass

def draw_grayscale (pdf, x, y, width, height, steps):
    step = width / steps
    for i in range(steps):
        C = (1.0 - MIN_COLOR) * i/steps + MIN_COLOR
        pdf.setStrokeColorRGB(C,C,C)
        pdf.setFillColorRGB(C,C,C)
        pdf.rect(x + i * step, y, step, height, fill=1)
        pass

def draw_grayscales (pdf):
    SCALE_X = X0 + 3 * ANCHOR_SIZE + GAP
    for y, n in [(Y0, 2), (Y1-BAR_HEIGHT, 4)]:
        x = SCALE_X 
        for _ in range(n):
            draw_grayscale(pdf, x, y, SCALE_W, BAR_HEIGHT, 32)
            x += SCALE_W + ANCHOR_SIZE
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


