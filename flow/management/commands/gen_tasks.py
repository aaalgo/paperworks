import os
import sys
import simplejson as json
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.utils import timezone
#from flow.geometry import create_pdf, render_page
from flow.models import *
from flow.paper import Paper
from params import *

def gen_batches ():
    pages = Page.objects.filter(done=False)
    pages = list(pages)
    for i in range(0, len(pages), BATCH):
        yield pages[i:(i+BATCH)]

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--run', action='store_true', default=False, help='')
        pass

    def handle(self, *args, **options):
        run = options['run']
        for pages in gen_batches():
            if not run:
                continue
            batch = Batch.objects.create()

            path = 'jobs/%04d-%s.pdf' % (batch.id, timezone.localtime(batch.timestamp).strftime('%Y%m%d%H%M%S'))

            pdf = Paper(path, LAYOUT)
            for page in pages:
                batch_page = BatchPage.objects.create(batch=batch, page=page)
                pdf.render_page(batch_page, Image.objects.filter(page=page))
                pass
            pdf.save()
            pass
        pass

