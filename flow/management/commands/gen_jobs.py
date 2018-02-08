import os
import sys
import simplejson as json
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from flow.geometry import create_pdf, render_page
from flow.models import *
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

            pdf = create_pdf(batch)
            for page in pages:
                batch_page = BatchPage.objects.create(batch=batch, page=page)
                render_page(pdf, batch_page)
                pdf.showPage()
                pass
            pdf.save()
            pass
        pass

