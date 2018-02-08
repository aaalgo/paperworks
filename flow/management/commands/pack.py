import sys
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
import subprocess as sp
import simplejson as json
from flow.models import *
from flow.geometry import *

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--run', action='store_true', default=False, help='')
        pass

    @transaction.atomic
    def handle(self, *args, **options):
        pages = []
        C = 0
        #cmd = "RectangleBinPack/BinPackTest";
        bin_spec = '0:unit:-1:%fx%f:1' % (IMAGE_W, IMAGE_H)
        #cmd += " %f %f" % (IMAGE_W, IMAGE_H)
        item_specs = []
        images = list(Image.objects.all())
        for i, image in enumerate(images):
            pages.append([image])
            w = image.width / PPI * inch
            h = image.height / PPI * inch
            image.page_w = w
            image.page_h = h
            #cmd += ' %f %f' % (w, h)
            item_specs.append('%d:unit:0:1:%fx%f:1' % (i, w, h))
            C += 1
            pass
        cmd = 'Pack/packit4me --bins %s --items %s --o result' % (bin_spec, ','.join(item_specs))
        #print("%d images placed into %d pages." % (C, len(pages)))
        #print(cmd)
        sp.check_call(cmd, shell=True)
        with open('result', 'r') as f:
            result = json.load(f)
        #print(result)
        print("Total items: %d" % C)

        # do not run, just show statistics
        missing = set(range(len(images)))
        P = 0
        C = 0
        for packed in result['packed']:
            items = packed['items']
            for item in items:
                uid = int(item['user_id'])
                image = images[uid]
                x = item['W']
                y = item['H']
                rotate = (item['rotation'].lower() == 'yes')
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
                missing.remove(uid)
                pass
            P += 1
            C += len(items)
            pass
        print("%d items packed." % C)
        print("%d pages used." % P)
        print("%d items unpacked." % len(missing))
        if options['run']:
            for packed in result['packed']:
                items = packed['items']
                page = Page.objects.create(done=False)
                for item in items:
                    uid = int(item['user_id'])
                    image = images[uid]
                    image.page = page
                    image.save()
                pass
        pass

