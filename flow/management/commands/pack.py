import sys
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
import subprocess as sp
import simplejson as json
from flow.models import *
from flow.geometry import *

def pack (page_size, images):     # item: (id, w, h)
    # return pages
    #        page: [items]
    #        item: id, x, y, rotated
    PAGE_W, PAGE_H = page_size
    pages = []
    bins = []   # [page, x, y, w, h, size]
    # reverse sort by size
    for uid, w, h in sorted(images, key=lambda im: -im[1] * im[2]):
        assert w <= PAGE_W
        assert h <= PAGE_H
        # try to find a bin that fits image
        best = None
        best_size = None
        for i, (_, _, _, W, H, size) in enumerate(bins):
            if (w < W and h < H) or (w < H and h < W):
                if best is None or size < best_size:
                    best = i
                    best_size = size
                    pass
                pass
            pass
        if best is None:
            best = len(bins)
            bins.append([len(pages), 0, 0, PAGE_W, PAGE_H, PAGE_W * PAGE_H])
            pages.append([])
            pass
        # split
        page, x, y, W, H, S = bins[best]

        rotate =False
        if w < W and h < H:
            pass
        else:
            rotate = True
            w, h = h, w
            pass
        # do not rotate
        pages[page].append([uid, x, y, rotate])
        bins.append([page, x, y + h, w, H-h, w * (H-h)])
        bins[best] = [page, x+w, y, W-w, H, (W-w)*H]
        pass
    return pages

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--run', action='store_true', default=False, help='')
        pass

    @transaction.atomic
    def handle(self, *args, **options):
        pages = []
        C = 0
        images = list(Image.objects.all())
        items = []
        for i, image in enumerate(images):
            pages.append([image])
            w = image.width / PPI * inch
            h = image.height / PPI * inch
            image.page_w = w
            image.page_h = h
            items.append((i, w, h))
            C += 1
            pass
        P = 0
        C = 0
        pages = pack((IMAGE_W, IMAGE_H), items)
        for items in pages:
            for uid, x, y, rotate in items:
                image = images[uid]
                image.rotate = rotate
                image.page_x = IMAGE_X0 + x
                image.page_y = IMAGE_Y0 + y
                if rotate:
                    image.page_w, image.page_h = image.page_h, image.page_w
                    right = image.page_x + image.page_h
                    bottom = image.page_y + image.page_w
                else:
                    right = image.page_x + image.page_w
                    bottom = image.page_y + image.page_h
                print('x0:', image.page_x, 'y0:', image.page_y, 'x1:', right, 'y1', bottom, rotate)
                print(IMAGE_X1, IMAGE_Y1)
                #assert right < IMAGE_X1 * 1.01
                #assert bottom < IMAGE_Y1 * 1.01
                pass
            P += 1
            C += len(items)
            pass
        print("%d items packed." % C)
        print("%d pages used." % P)
        if options['run']:
            for items in pages:
                page = Page.objects.create(done=False)
                for uid, _, _, _ in items:
                    image = images[uid]
                    image.page = page
                    image.save()
                pass
        pass

