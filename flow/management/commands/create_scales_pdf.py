import os
import sys
import simplejson as json
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from flow.geometry import create_scales_pdf
from flow.models import *
from params import *

class Command(BaseCommand):

    def handle(self, *args, **options):
        create_scales_pdf('scales.pdf')
        pass

