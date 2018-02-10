import os
import sys
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
from glob import glob
import subprocess
from skimage import morphology
import imageio
from flow.models import *
from flow.geometry import *

def zbar_scan (path):
    symbol = subprocess.check_output("./zbar.py %s" % path, shell=True)
    symbol = symbol.decode('ascii').strip()
    assert len(symbol) > 0
    return symbol

def estimate_transform (image):
    pass

def normalize (image):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    rotate = rotate_normalize(gray)
    image = rotate(image)
    affine = calibrate(rotate(gray))

    W, H = PAPER_SIZE
    W = int(round(W * CALIB_PPI / inch))
    H = int(round(H * CALIB_PPI / inch))

    return cv2.warpAffine(image, affine, (W, H))

def gen_gif (path, image, mask):
    images = []
    bgr = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    images.append(bgr)
    bgrm = np.copy(bgr).astype(np.float32)
    print("YYY", np.sum(mask), np.max(mask))
    bgrm[:, :, 1] += mask * 255
    bgrm = np.clip(bgrm, 0, 255).astype(np.uint8)
    images.append(bgrm)
    imageio.mimsave(path + '.gif', images, duration = 0.5)
    subprocess.check_call('gifsicle -O3 < %s.gif > %s; rm %s.gif' % (path, path, path), shell=True)
    pass

def map_to_image (L, X0, X1, x0, x1):
    # L is image size
    # X0:X1 image in page
    # x0:x1 roi in page
    
    x0 = int(round(1.0 *(x0 - X0) * L / (X1 - X0)))
    x1 = int(round(1.0 * (x1 - X0) * L / (X1 - X0)))
    return x0, x1

def paste_to_mask (mask, binary, image_box, aoi):
    print(image_box, '=>', aoi)
    H, W = mask.shape
    Y0,X0,Y1,X1 = [int(round(v)) for v in image_box]
    y0,x0,y1,x1 = [int(round(v)) for v in aoi]
    aoi = binary[y0:y1, x0:x1]

    x0, x1 = map_to_image(W, X0, X1, x0, x1)
    y0, y1 = map_to_image(H, Y0, Y1, y0, y1)
    print(W, H, x0,x1,y0,y1)
    aoi = cv2.resize(aoi, (x1-x0, y1-y0))

    mask_aoi = mask[y0:y1, x0:x1]
    mask_aoi[aoi > 0] = 1
    pass

def process (path):
    ############################################################
    symbol = zbar_scan(path)
    if symbol is None:
        print("ERROR, %s not recognized")
        return
    batch_id, page_id = barcode_decode(symbol)
    batch = Batch.objects.get(pk=batch_id)
    page = Page.objects.get(pk=page_id)
    scan = Scan.objects.create(path=path, batch=batch, page=page)
    ############################################################

    image = cv2.imread(path, cv2.IMREAD_COLOR).astype(np.float32)
    image = normalize(image)

    cv2.imwrite('aligned/%d.png' % scan.id, image)
    cv2.imwrite('aligned/%d-color.png' % scan.id, enhance_color(image))
    #sys.exit(0)

    hue = get_hue(image)
    classes = []
    for x, y, w, h in SCALE_BOXES:
        x = int(round(x * CALIB_PPI / inch))
        y = int(round(y * CALIB_PPI / inch))
        w = int(round(w * CALIB_PPI / inch))
        h = int(round(h * CALIB_PPI / inch))
        roi = hue[y:(y+h), x:(x+w)]
        nc = np.sum(roi > 0)
        cc = np.sum(roi) / nc
        roi = np.copy(roi)
        roi[np.abs(roi - cc) > 50] = 0
        nc = np.sum(roi > 0)
        cc = np.sum(roi) / nc
        if nc > LEGEND_TH:
            print("COLOR DETECTED:", cc, nc)
            classes.append(cc)
            pass
    classes.sort()
    for i in range(1, len(classes)):
        assert classes[i] - classes[i-1] > 2 * CLASS_GAP

    images = Image.objects.filter(page=page)
    image_boxes = []
    image_bg = []
    image_mask = []
    for imager in images:
        x = imager.page_x * CALIB_PPI / inch
        y = imager.page_y * CALIB_PPI / inch
        w = imager.page_w * CALIB_PPI / inch
        h = imager.page_h * CALIB_PPI / inch
        image_boxes.append([y, x, (y+h), (x+w)])

        bg = cv2.imread(imager.path, cv2.IMREAD_COLOR)
        H, W = bg.shape[:2]
        mask = np.zeros((H, W), dtype=np.uint8)
        if imager.rotate:
            mask = cv2.transpose(mask)
        image_bg.append(bg)
        image_mask.append(mask)
        
    ############################################################

    kernel = np.ones((1,1), dtype=np.uint8)
    for cid, cc in enumerate(classes):
        binary = (np.abs(hue - cc) < 50)
        binary = morphology.remove_small_objects(binary, 32)
        

        cv2.imwrite('aligned/%d-%d.png' % (scan.id, cid), binary.astype(np.uint8)*255)
        # get masks
        # move masks to image
        labels = measure.label(binary, background=0)
        binary = binary.astype(np.uint8)
        for box in measure.regionprops(labels):
            y0, x0, y1, x1 = box.bbox
            cc = np.sum(binary[y0:y1, x0:x1])
            if cc < 20:
                continue
            # check best images
            # find best image
            best = None
            best_area = -1
            best_aoi = None
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
                        best_aoi = [Y0, X0, Y1, X1]
                        pass
                    pass
                pass
            if best is None:
                continue
            #image = images[best]
            mask = image_mask[best]
            paste_to_mask(mask, binary, image_boxes[best], best_aoi)
            # somehow save info
            pass
        pass
    for i, image  in enumerate(images):
        bg = image_bg[i]
        mask = image_mask[i]
        if image.rotate:
            mask = cv2.transpose(mask)
        mask = cv2.flip(mask, 0)
        gen_gif('aligned/vis-%d.gif' % images[i].id, bg, mask)


    pass


class Command(BaseCommand):
    def add_arguments(self, parser):
        #parser.add_argument('--run', action='store_true', default=False, help='')
        pass

    @transaction.atomic
    def handle(self, *args, **options):
        Scan.objects.all().delete()
        subprocess.check_call('rm aligned/*', shell=True)
        for root, dirs, files in os.walk('scan', topdown=False):
            for f in files:
                path = os.path.join(root, f)
                if Scan.objects.filter(path=path).count() == 0:
                    process(path)
                pass
            pass
        pass

