import os
import sys
import traceback
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from glob import glob
import subprocess
import imageio
import scipy
from flow.models import *
from flow.register import *
from flow.barcode import *
from flow.color import PixelClassifier, filter_color

tableau20 = [(180, 119, 31), (232, 199, 174), (14, 127, 255), (120, 187, 255),
			 (44, 160, 44), (138, 223, 152), (40, 39, 214), (150, 152, 255),
			 (189, 103, 148), (213, 176, 197), (75, 86, 140), (148, 156, 196),
			 (194, 119, 227), (210, 182, 247), (127, 127, 127), (199, 199, 199),
			 (34, 189, 188), (141, 219, 219), (207, 190, 23), (229, 218, 158)]

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
    x1 = x + w + 0.3
    y1 = y + h + 0.5
    x = int(round(x))
    y = int(round(y))
    x1 = int(round(x1))
    y1 = int(round(y1))
    return x, y, x1-x, y1-y


def overlay_channel (v, mask, c):
    for i in range(3):
        v[:, :, i][mask] *= 0.5
        v[:, :, i][mask] += c[i]*0.5
    pass

def gen_gif (path, image, mask):
    images = []
    bgr = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    images.append(bgr)
    bgrm = np.copy(bgr).astype(np.float32)
    for v in np.unique(mask):
        if v == 0:
            continue
        r, g, b= tableau20[v-1]
        overlay_channel(bgrm, mask == v, (b, g, r))
    images.append(bgrm)
    imageio.mimsave(path + '.gif', images, duration = 1)
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

@transaction.atomic
def process (path):
    print("processing", path)
    ############################################################
    batch_id, page_id = barcode_scan(path)
    batch = Batch.objects.get(pk=batch_id)
    page = Page.objects.get(pk=page_id)
    page.done = True
    page.save()
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
            filled_binary = scipy.ndimage.morphology.binary_fill_holes((labels == box.label)).astype(np.uint8)

            paste_to_mask(image_mask[best], filled_binary, image_boxes[best], best_aoi, cid+1)
            pass
        pass
    for i, image  in enumerate(images):
        bg = image_bg[i]
        mask = image_mask[i]
        if image.rotate:
            mask = cv2.flip(mask, 0)
            mask = cv2.transpose(mask)
            mask = cv2.flip(mask, 0)

        cv2.imwrite('masks/%s.png' % images[i].stem(), mask)
        gen_gif('aligned/vis-%d.gif' % images[i].id, bg, mask)
    pass


class Command(BaseCommand):
    def add_arguments(self, parser):
        #parser.add_argument('--run', action='store_true', default=False, help='')
        parser.add_argument('--remove', action='store_true', default=False, help='')
        pass

    def handle(self, *args, **options):
        Scan.objects.all().delete()
        subprocess.check_call('mkdir -p aligned masks', shell=True)
        subprocess.check_call('rm -rf aligned/* masks/*', shell=True)
        for root, dirs, files in os.walk('scan', topdown=False):
            for f in files:
                path = os.path.join(root, f)
                if Scan.objects.filter(path=path).count() == 0:
                    try:
                        process(path)
                    except:
                        traceback.print_exc()
                        print("Failed to process file %s" % path)
                        pass
                pass
            pass
        pass

