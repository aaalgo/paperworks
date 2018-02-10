from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code39
from django.utils import timezone
from sklearn.linear_model import LinearRegression
from skimage import measure
from flow.models import *
from flow.barcode import *
from params import *
import numpy as np
import cv2

class Paper:
    def __init__ (self, path, layout=LAYOUT):
        self.path = 'jobs/%04d-%s.pdf' % (batch.id, timezone.localtime(batch.timestamp).strftime('%Y%m%d%H%M%S'))
        self.canvas = canvas.Canvas(self.path, pagesize=layout.paper_size, bottomup=0)
        self.layout = layout
        pass

    def render_fixtures (self):
        pdf = self.canvas

        # anchors
        pdf.setStrokeColorRGB(0,0,0)
        pdf.setFillColorRGB(0,0,0)
        for x, y in self.layout.anchors:
            pdf.circle(x, y, GAP, 1, 1)

        # sample boxes
        steps = 32
        for x, y, w, h in self.samples:
            step = w / steps
            for i in range(steps):
                C = (1.0 - MIN_COLOR) * i/steps + MIN_COLOR
                pdf.setStrokeColorRGB(C,C,C)
                pdf.setFillColorRGB(C,C,C)
                pdf.rect(x + i * step, y, step, h, fill=1)
                pass
        pass

    def render_page (self, batch_page, images):

        self.render_fixtures()
        # barcode
        barcode=code39.Extended39(barcode_encode(batch_page),
                                  barWidth=self.layout.bar_width,
                                  barHeight=self.layout.box_height)
        pdf = self.canvas
        pdf.setStrokeColorRGB(0,0,0)
        pdf.setFillColorRGB(0,0,0)
        barcode.drawOn(pdf, self.layout.barcode_x, self.layout.barcode_y)

        for image in images:
            ratio = 1.0 / PPI * inch
            pdf.drawImage(image.embed_path(image.rotate), image.page_x, image.page_y, width=image.page_w, height=image.page_h)
            pass
        pdf.showPage()
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


