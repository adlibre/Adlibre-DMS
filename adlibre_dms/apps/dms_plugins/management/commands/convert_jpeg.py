"""
Module: Jpeg to PNG thumbnail converter for Adlibre DMS

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
Author: Iurii Garmash (yuri@adlibre.com.au)
"""

from optparse import make_option
from PIL import Image

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Converts from JPEG image into PNG thumbnail"""
    args = 'thumbnail_path'

    def __init__(self):
        BaseCommand.__init__(self)
        self.option_list += (
            make_option(
                '--quiet', '-q',
                default=False,
                action='store_true',
                help='Hide all command output'),
        )

    def handle(self, *args, **options):
        quiet = options.get('quiet', False)
        if len(args) == 0:
            if not quiet:
                self.stdout.write('No arguments specified\n')
            return

        if len(args) > 1:
            if not quiet:
                self.stdout.write('Please specify one path at a time\n')
            return
        if not quiet:
            self.stdout.write('Converting thumbnail\n')

        thumbnail_path = args[0]
        im = Image.open(thumbnail_path)
        try:
            img = im.resize(64, 64, Image.ANTIALIAS)
        except:
            if not quiet:
                self.stderr.write('PIL error resizing.\n')
            raise
        img.save(thumbnail_path + '.png', 'PNG')
        if not quiet:
            self.stdout.write('Done!\n')