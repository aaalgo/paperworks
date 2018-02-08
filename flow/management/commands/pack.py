import sys
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
import subprocess as sp
import simplejson as json
from flow.models import *
from flow.geometry import *

# test with or without rotate
#      cut along x or y
# return optimal filling method
# score == 0 means not feaisble
def divide (w0, h0, W, H):
    best = 0
    best_rotate = None
    best_along_x = None
    for rotate in [False, True]:
        if rotate:
            w, h = h0, w0
        else:
            w, h = w0, h0
        if w < W and h < H:
            # along X
            v = max(min(W-w, h), min(W, H-h))
            if v > best:
                best = v
                best_rotate = rotate
                best_along_x = True
            v = max(min(W-w, H), min(w, H-h))
            if v > best:
                best = v
                best_rotate = rotate
                best_along_x = False
                pass
            pass
        pass
    return best, best_rotate, best_along_x


def pack (page_size, images):     # item: (id, w, h)
    # return pages
    #        page: [items]
    #        item: id, x, y, rotated
    PAGE_W, PAGE_H = page_size
    pages = []
    bins = []   # [page, x, y, w, h]
    # reverse sort by size
    for uid, w, h in sorted(images, key=lambda im: -im[1] * im[2]):
        assert w <= PAGE_W
        assert h <= PAGE_H
        # try to find a bin that fits image
        best = None
        best_score = None
        best_rotate = None
        best_along_x = None     # cut along x
        for i, (_, _, _, W, H) in enumerate(bins):
            score, rotate, along_x = divide(w, h, W, H)
            if score == 0:
                continue
            if best is None or score > best_score:
                best = i
                best_score = score
                best_rotate = rotate
                best_along_x = along_x
            pass
        if best is None:
            best = len(bins)
            bins.append([len(pages), 0, 0, PAGE_W, PAGE_H])
            pages.append([])
            best_score, best_rotate, best_along_x = divide(w, h, PAGE_W, PAGE_H)
            pass
        # split
        page, x, y, W, H = bins[best]

        if best_rotate:
            w, h = h, w
            pass
        # do not rotate
        pages[page].append([uid, x, y, best_rotate])
        if best_along_x:
            bins.append([page, x+w, y, W-w, h])
            bins[best] = [page, x, y+h, W, H-h]
        else:
            bins.append([page, x, y + h, w, H-h])
            bins[best] = [page, x+w, y, W-w, H]
        pass
    return pages

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--run', action='store_true', default=False, help='')
        pass

    @transaction.atomic
    def handle(self, *args, **options):
        run = options['run']

        if run:
            BatchPage.objects.all().delete()
            Batch.objects.all().delete()
            Page.objects.all().delete()

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
            items.append((i, w + IMAGE_MARGIN * 2, h + IMAGE_MARGIN * 2))
            C += 1
            pass
        P = 0
        C = 0
        pages = pack((IMAGE_W, IMAGE_H), items)
        for items in pages:
            for uid, x, y, rotate in items:
                image = images[uid]
                image.rotate = rotate
                image.page_x = IMAGE_X0 + x + IMAGE_MARGIN
                image.page_y = IMAGE_Y0 + y + IMAGE_MARGIN
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
        if run:
            for items in pages:
                page = Page.objects.create(done=False)
                for uid, _, _, _ in items:
                    image = images[uid]
                    image.page = page
                    image.save()
                pass
        pass

