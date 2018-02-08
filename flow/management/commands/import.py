import sys
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
import cv2
from flow.models import *

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--run', action='store_true', default=False, help='')
        pass

    @transaction.atomic
    def handle(self, *args, **options):
        #hours = options['hours'] + 24 * options['days']
        #check_and_import(hours, not options['run'], options['check'])
        run = options['run']
        C = 0
        for line in sys.stdin:
            path = line.strip()
            image = cv2.imread(path)
            H, W = image.shape[:2]
            if run:
                x = Image.objects.create(path = path, width=W, height=H)
                x.gen_embed()
                C += 1
                pass
            print(path)
            pass
        print("%d images imported." %C)
        pass

