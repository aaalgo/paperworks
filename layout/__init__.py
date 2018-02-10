from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.units import inch
#from params import *

class LetterSizeLandscapeLayout:
    # all orders are x, y, or width, height
    # all boxes are x, y, width, height
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

        self.contentbb = x0, y0, x1 - x0, y1 - y0
        self.imagebb = x0, y0 + self.box_height + qspace, x1 - x0, y1 - y0 - (self.box_height + qspace) * 2
        self.anchors = []
        self.samples = []

        # generate anchors
        r = self.anchor_size / 2
        for X, Y, dx, dy, dir,n in [(x0+r, y0+r, 1, 1, 0, 4),
                                  (x1-r, y0+r, -1, 1, 0, 4),
                                  (x0+r, y1-r, 1, -1, 0, 4),
                                  (x1-r, y1-r, -1, -1, 0, 5)]:
            anchors = []
            for s in range(n):
                x = X + dx * s * (1-dir) * (self.anchor_size + qspace)
                y = Y + dy * s * dir * (self.anchor_size + qspace)
                anchors.append([x, y])
                pass
            # sort by x
            anchors.sort(key=lambda a:a[0])
            self.anchors.extend(anchors)
            pass

        sample_x = x0 + 4 * (self.anchor_size + qspace) + hspace
        self.barcode_x = sample_x + 2 * (self.box_width + hspace) + hspace
        self.barcode_y = y0
        for y, n in [(y0, 2), (y1-self.box_height, 3)]:
            x = sample_x
            for _ in range(n):
                self.samples.append([x, y, self.box_width, self.box_height])
                x += self.box_width + hspace
                pass
            pass
        pass
    pass


