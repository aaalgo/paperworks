import sys
from optparse import make_option
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django.contrib.auth.models import User
from annotate.models import *

class Command(BaseCommand):
    def add_arguments(self, parser):
        #parser.add_argument('--run', action='store_true', default=False, help='')
        pass

    @transaction.atomic
    def handle(self, *args, **options):
        pass

