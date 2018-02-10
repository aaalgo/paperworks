import sys
from optparse import make_option
from reportlab.lib.units import inch
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
import subprocess as sp
import simplejson as json
from flow.models import *
from flow.pack import pack

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

        images = list(Image.objects.all())
        x0, y0, width, height = LAYOUT.imagebb
        # do packing
        items = []

        margin = LAYOUT.image_margin    # image margin
        for i, image in enumerate(images):
            w = image.width / IMAGE_PPI * inch
            h = image.height / IMAGE_PPI * inch
            image.page_w = w
            image.page_h = h
            items.append((i, w + margin * 2, h + margin * 2))
            pass
        pages = pack((width, height), items)

        C = 0
        for items in pages:
            for uid, x, y, rotate in items:
                image = images[uid]
                image.rotate = rotate
                image.page_x = x0 + x + margin
                image.page_y = y0 + y + margin
                if rotate:
                    image.page_w, image.page_h = image.page_h, image.page_w
                    right = image.page_x + image.page_h
                    bottom = image.page_y + image.page_w
                else:
                    right = image.page_x + image.page_w
                    bottom = image.page_y + image.page_h
                assert right < x0 + width + LAYOUT.space
                assert bottom < y0 + height  + LAYOUT.space
                pass
            C += len(items)
            pass
        assert C == len(images)
        print("%d images packed in %d pages." % (C, len(pages)))
        if run:
            for items in pages:
                page = Page.objects.create(done=False)
                for uid, _, _, _ in items:
                    image = images[uid]
                    image.page = page
                    image.save()
                pass
        pass

