import os
import sys
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
from glob import glob
import subprocess
from flow.models import *
from flow.geometry import *

def zbar_scan (path):
    symbol = subprocess.check_output("./zbar.py %s" % path, shell=True)
    symbol = symbol.strip()
    assert len(symbol) > 0
    return symbol

def estimate_transform (image):
    pass

def normalize (image)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    rotate = rotate_normalize(gray)
    image = rotate(image)
    affine = calibrate(rotate(gray))

    W, H = PAPER_SIZE
    W = int(round(W * CALIB_PPI / inch))
    H = int(round(H * CALIB_PPI / inch))

    return cv2.warpAffine(image, affine, (W, H))

def process (path):
    image = cv2.imread(path, cv2.IMREAD_COLOR).astype(np.float32)
    image = normalize(image)

    hue = get_hue(image)
    classes = []
    for x, y, w, h in SCALE_BOXES:
        x = int(round(x * CALIB_PPI / inch))
        y = int(round(y * CALIB_PPI / inch))
        w = int(round(w * CALIB_PPI / inch))
        h = int(round(h * CALIB_PPI / inch))
        roi = hue[y:(y+h), x:(x+w)]
        cc = np.mean(roi)
        if abs(cc) > 20:
            classes.append(cc)
            pass

    ############################################################
    symbol = zbar_scan(path)
    if symbol is None:
        print("ERROR, %s not recognized")
        return
    batch_id, page_id = barcode_decode(symbol)

    batch = Batch.objects.get(pk=batch_id)
    page = Page.objects.get(pk=page_id)

    images = Image.objects.filter(page=page)
    image_boxes = []
    for image in images:
        x = image.page_x * CALIB_PPI / inch
        y = image.page_y * CALIB_PPI / inch
        w = image.page_w * CALIB_PPI / inch
        h = image.page_h * CALIB_PPI / inch
        image_boxes.append([y, x, (y+h), (x+w)]
    ############################################################

    for cc in classes:
        binary = (np.abs(hue - cc) < 30)
        # get masks
        # move masks to image
        labels = measure.label(binary, background=0)
        for box in measure.regionprops(labels):
            y0, x0, y1, x1 = box.bbox
            # check best images
            # find best image
            best = None
            best_area = -1
            for i, (Y0, X0, Y1, X1) in enumerate(image_boxes):
                Y0 = max(y0, Y0)
                X0 = max(x0, X0)
                Y1 = min(y1, Y1)
                X1 = min(x1, X1)
                if Y0 < Y1 and X0 < X1:
                    area = (Y1 - Y0) * (X1 - X0)
                    if area > best_area:
                        best_area = area
                        best = i
                        pass
                    pass
                pass
            if best is None:
                continue
            image = images[best]
            # somehow save info
            pass
        pass
    scan = Scan.ojbects.create(path=path, batch=batch, page=page)
    pass


class Command(BaseCommand):
    def add_arguments(self, parser):
        #parser.add_argument('--run', action='store_true', default=False, help='')
        pass

    @transaction.atomic
    def handle(self, *args, **options):
        for root, dirs, files in os.walk('scan', topdown=False):
            for f in files:
                path = os.path.join(root, f)
                if Scan.objects.filter(path=path).count() == 0:
                    process(path)
                pass
            pass
        pass

