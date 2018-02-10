import os
import sys
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
from glob import glob
import subprocess
import imageio
from flow.models import *
from flow.register import *
from flow.barcode import *
from flow.color import PixelClassifier, filter_color

def overlap (box1, box2):
    x0, y0, w, h = box1
    x1, y1 = x0 + w, y0 + h

    X0, Y0, W, H = box2
    X1, Y1 = X0 + W, Y0 + H

    ox0 = max(x0, X0)
    oy0 = max(y0, Y0)
    ox1 = min(x1, X1)
    oy1 = min(y1, Y1)

    return [ox0, oy0, ox1-ox0, oy1-oy0]

def round_box (box):
    x, y, w, h = box
    x1 = x + w + 0.5
    y1 = y + h + 0.5
    x = int(round(x))
    y = int(round(y))
    x1 = int(round(x1))
    y1 = int(round(y1))
    return x, y, x1-x, y1-y



def gen_gif (path, image, mask):
    images = []
    bgr = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    images.append(bgr)
    bgrm = np.copy(bgr).astype(np.float32)
    bgrm[:, :, 1] += np.clip(mask, 0, 1) * 255
    bgrm = np.clip(bgrm, 0, 255).astype(np.uint8)
    images.append(bgrm)
    imageio.mimsave(path + '.gif', images, duration = 0.5)
    subprocess.check_call('gifsicle --colors 256 -O3 < %s.gif > %s; rm %s.gif' % (path, path, path), shell=True)
    pass

def map_to_mask (L, X0, W, x0, w):
    # X0, W image in page
    # x0, w roi in page
    x1 = x0 + w
    x0 = int(round(1.0 * (x0 - X0) * L / W))
    x1 = int(round(1.0 * (x1 - X0) * L / W))
    return x0, x1

def paste_to_mask (mask, binary, image_box, aoi, cid):
    #print(image_box, '=>', aoi)
    height, width = mask.shape
    X0,Y0,W,H = image_box
    x0,y0,w,h = aoi
    assert w > 0 and h > 0

    #print(aoi, 'in', image_box)
    aoi = binary[y0:(y0+h), x0:(x0+w)]

    x0, x1 = map_to_mask(width, X0, W, x0, w)
    y0, y1 = map_to_mask(height, Y0, H, y0, h)
    if x0 >= x1 or y0 >= y1:
        return
    y0, x0, y1, x1 = expand((y0, x0, y1, x1), mask.shape, 0)
    aoi = cv2.resize(aoi, (x1-x0, y1-y0))

    mask_aoi = mask[y0:y1, x0:x1]
    mask_aoi[aoi > 0] = cid
    #cv2.rectangle(mask, (x0, y0), (x1, y1), 1, 1)
    pass

def process (path):
    ############################################################
    batch_id, page_id = barcode_scan(path)
    batch = Batch.objects.get(pk=batch_id)
    page = Page.objects.get(pk=page_id)
    scan = Scan.objects.create(path=path, batch=batch, page=page)
    ############################################################

    image = cv2.imread(path, cv2.IMREAD_COLOR) #.astype(np.float32)
    image = cv2.GaussianBlur(image, (9, 9), 3)
    image = normalize(image, LAYOUT)

    cv2.imwrite('aligned/%d-color.png' % scan.id, filter_color(image))

    pc = PixelClassifier()

    samples = []
    for x, y, w, h in boxes2paper(LAYOUT.samples):
        x = int(round(x))
        y = int(round(y))
        x1 = int(round(x+w))
        y1 = int(round(y+h))
        samples.append(image[y:y1, x:x1])
        pass
    pc.fit(samples)

    images = Image.objects.filter(page=page)
    image_boxes = []
    image_bg = []
    image_mask = []
    for r in images:
        image_boxes.append([r.page_x, r.page_y, r.page_w, r.page_h])

        bg = cv2.imread(r.path, cv2.IMREAD_COLOR)
        H, W = bg.shape[:2]
        mask = np.zeros((H, W), dtype=np.uint8)
        if r.rotate:
            mask = cv2.transpose(mask)
        image_bg.append(bg)
        image_mask.append(mask)
        pass
    image_boxes = [round_box(box) for box in boxes2paper(image_boxes)]

    for cid, binary in enumerate(pc.predict(image)):
        binary = binary.astype(np.uint8)
        cv2.imwrite('aligned/%d-%d.png' % (scan.id, cid), binary * 255)
        # get masks
        # move masks to image
        labels = measure.label(binary, background=0)
        for box in measure.regionprops(labels):
            # check best images
            # find best image
            best = None
            best_area = -1
            best_aoi = None
            for i, ibox in enumerate(image_boxes):
                y0, x0, y1, x1 = box.bbox
                bbox = [x0, y0, x1-x0, y1-y0]
                aoi = overlap(bbox, ibox)
                _, _, w, h = aoi
                area = w * h
                if w > 0 and h > 0:
                    if area > best_area:
                        best_area = area
                        best = i
                        best_aoi = aoi
                        pass
                    pass
                pass
            if best is None:
                continue
            paste_to_mask(image_mask[best], binary, image_boxes[best], best_aoi, cid+1)
            pass
        pass
    for i, image  in enumerate(images):
        bg = image_bg[i]
        mask = image_mask[i]
        if image.rotate:
            mask = cv2.transpose(mask)
        cv2.imwrite(image.path + '.png', mask)
        gen_gif('aligned/vis-%d.gif' % images[i].id, bg, mask)
    pass


class Command(BaseCommand):
    def add_arguments(self, parser):
        #parser.add_argument('--run', action='store_true', default=False, help='')
        pass

    @transaction.atomic
    def handle(self, *args, **options):
        Scan.objects.all().delete()
        subprocess.check_call('rm -f aligned/*', shell=True)
        for root, dirs, files in os.walk('scan', topdown=False):
            for f in files:
                path = os.path.join(root, f)
                if Scan.objects.filter(path=path).count() == 0:
                    process(path)
                pass
            pass
        pass

