"""
Module: Jpeg to PNG thumbnail converter for Adlibre DMS

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
Author: Iurii Garmash (yuri@adlibre.com.au)
"""

from optparse import make_option
from wand.image import Image

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Converts from JPEG image into PNG thumbnail"""
    args = 'thumbnail_path'

    def handle(self, *args, **options):
        if len(args) == 0:
            self.stdout.write('No arguments specified\n')
            return

        if len(args) > 1:
            self.stdout.write('Please specify one path at a time\n')
            return

        self.stdout.write('Converting thumbnail\n')
        thumbnail_path = args[0]
