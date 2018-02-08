import sys
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
import subprocess as sp
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
        for image in Image.objects.all():
            pages.append([image])
            w = image.width / PPI * inch
            h = image.height / PPI * inch
            #cmd += ' %f %f' % (w, h)
            item_specs.append('%d:unit:0:1:%fx%f:1' % (image.id, w, h))
            C += 1
            pass
        cmd = 'Pack/packit4me --bins %s --items %s --o result' % (bin_spec, ','.join(item_specs))
        #print("%d images placed into %d pages." % (C, len(pages)))
        print(cmd)
        sp.check_call(cmd, shell=True)
        sys.exit(0)
        run = options['run']
        C = 0
        for images in pages:
            if run:
                page = Page.objects.create(done=False)
                for image in images:
                    image.page = page
                    image.save()
                    pass
                C += 1
            pass
        print("%d pages generated." %C)
        pass

