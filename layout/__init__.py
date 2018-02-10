from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.units import inch
#from params import *

class LetterSizeLandscapeLayout:
    # all orders are x, y, or width, height
    # all boxes are x0, x1, y0, y1
    def __init__ (self):
        width, height = landscape(letter)
        margin = 0.25 * inch # margin
        space = 0.5 * inch
        hspace = 0.25 * inch
        qspace = 0.125 * inch
        self.space = space
        self.hspace = hspace
        self.qspace = qspace
        self.image_margin = qspace

        self.paper_size = width, height
        self.margin = margin
        self.box_height = 0.4 * inch    # sample box or barcode
        self.box_width = 1.5 * inch
        # barcode single bar width
        self.bar_width = 0.02 * inch
        self.anchor_size = 0.4 * inch

        # x0, y0, x1, y1: content box
        x0 = margin
        y0 = margin
        x1 = width - margin
        y1 = height - margin

        self.contentbb = x0, y0, x1, y1
        self.imagebb = x0, y0 + self.box_height + qspace, x1, y1 - self.box_height - qspace
        self.anchors = []
        self.samples = []

        # generate anchors
        r = space
        for X, Y, dx, dy, dir,n in [(x0+r, y0+r, 1, 1, 0, 3),
                                  (x1-r, y0+r, -1, 1, 0, 4),
                                  (x0+r, y1-r, 1, -1, 0, 3),
                                  (x1-r, y1-r, -1, -1, 0, 3)]:
            for s in range(n):
                x = X + dx * s * (1-dir) * (self.anchor_size + qspace)
                y = Y + dy * s * dir * (self.anchor_size + qspace)
                self.anchors.append([x, y])
                pass
            pass

        sample_x = x0 + 3 * self.anchor_size + space
        self.barcode_x = sample_x + 2 * (self.box_width + hspace) + hspace
        self.barcode_y = y0
        for y, n in [(y0, 2), (y1-self.box_height, 4)]:
            x = sample_x
            for _ in range(n):
                self.samples.append([x, y, x + self.box_width, y + self.box_height])
                x += self.box_width + space
                pass
            pass
        pass
    pass


