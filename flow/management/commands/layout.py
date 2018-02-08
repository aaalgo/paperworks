import sys
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
from flow.models import *

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--run', action='store_true', default=False, help='')
        pass

    @transaction.atomic
    def handle(self, *args, **options):
        pages = []
        C = 0
        for image in Image.objects.all():
            pages.append([image])
            C += 1
            pass
        print("%d images placed into %d pages." % (C, len(pages)))
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

