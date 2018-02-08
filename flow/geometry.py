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
    + BBB +




    +     +
    ++   ++
'''
W, H = PAPER_SIZE
X0, Y0 = MARGIN
X1, Y1 = W - X0, H - Y0
GAP = ANCHOR_SIZE * 0.5
RELAX = 0.5 * GAP
BAR_X = X0 + GAP + RELAX
BAR_Y = Y0
SCALE_W = 2 * inch

def barcode_encode (batch_page):
    return '%d %d' % (batch_page.batch.id, batch_page.page.id)

ANCHORS = []
ANCHOR_LINES = []

IMAGE_X0 = X0
IMAGE_X1 = W - X0
IMAGE_Y0 = Y0 + 2.5 * ANCHOR_SIZE + RELAX 
IMAGE_Y1 = Y1 - 0.5 * ANCHOR_SIZE - RELAX 
IMAGE_W = IMAGE_X1 - IMAGE_X0
IMAGE_H = IMAGE_Y1 - IMAGE_Y0

def gen_anchors ():
    for X, Y, dx, dy, dir in [(X0, Y0, 1, 1, 1),
                              (X1, Y0, -1, 1, 1),
                              (X0, Y1, 1, -1, 0),
                              (X1, Y1, -1, -1, 0)]:
        for s in [0, 1, 2]:
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
    x = BAR_X
    y = BAR_Y
    for _ in range(3):
        draw_grayscale(pdf, x, y, SCALE_W, BAR_HEIGHT, 32)
        x += SCALE_W + GAP
        pass
    x = BAR_X
    y += BAR_HEIGHT + RELAX
    for _ in range(3):
        draw_grayscale(pdf, x, y, SCALE_W, BAR_HEIGHT, 32)
        x += SCALE_W + GAP
        pass
    return x, y


def render_page (pdf, batch_page):
    print(W, H, X0, Y0, X1, Y1)
    # batch-page-
    x, y = draw_grayscales(pdf)

    barcode=code39.Extended39(barcode_encode(batch_page),barWidth=BAR_WIDTH,barHeight=BAR_HEIGHT)
    pdf.setStrokeColorRGB(0,0,0)
    pdf.setFillColorRGB(0,0,0)
    barcode.drawOn(pdf, (X0+X1)/2, Y1-GAP)
    draw_anchors(pdf)

    #pdf.rect(IMAGE_X0, IMAGE_Y0, IMAGE_X1-IMAGE_X0, IMAGE_Y1-IMAGE_Y0)
    print(Y0, IMAGE_Y0, GAP, RELAX)

    #batch = batch_page.batch
    page = batch_page.page

    for image in Image.objects.filter(page=page):

        #bm = cv2.imread(image.path, cv2.IMREAD_GRAYSCALE).astype(np.float32)
        #cv2.normalize(bm, None, MIN_COLOR, 1.0, cv2.NORM_MINMAX)
        w0, h0 = image.width, image.height
        #w, h -> IMAGE_W, IMAGE_H
        #
        ratio = min(IMAGE_H/h0, IMAGE_W/w0, MAX_SCALE)
        print("XXX",ratio)

        pdf.drawImage(image.embed_path(), IMAGE_X0, IMAGE_Y0, width=w0 * ratio, height=h0* ratio)

    pass


