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

def process (path):
    image = cv2.imread(path, cv2.IMREAD_COLOR).astype(np.float32)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    rotate = rotate_normalize(gray)
    image = rotate(image)
    affine = calibrate(rotate(gray))

    W, H = PAPER_SIZE
    W = int(round(W * PPI / inch))
    H = int(round(H * PPI / inch))

    image = cv2.warpAffine(image, affine, (W, H))
    cv2.imwrite('affine.png', image)


    color = enhance_color(image)
    cv2.imwrite('xxx.png', color)

    sys.exit(0)
    symbol = zbar_scan(path)
    if symbol is None:
        print("ERROR, %s not recognized")
        return
    batch_id, page_id = barcode_decode(symbol)

    batch = Batch.objects.get(pk=batch_id)
    page = Page.objects.get(pk=page_id)

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

