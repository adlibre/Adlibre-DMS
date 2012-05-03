"""
Module: MDT import management command for Adlibre DMS
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import os, json
from django.core.management.base import BaseCommand
from mdt_manager import MetaDataTemplateManager
from optparse import make_option

class Command(BaseCommand):

    def __init__(self):
        BaseCommand.__init__(self)
        self.option_list += (
            make_option(
                '--quiet', '-q',
                default=False,
                action='store_true',
                help='Hide all command output'),
            )
    help = "Imports Meta Data Template from specified JSON file\n"
    args = '<file_name1.json file_name2.json ...>'

    def handle(self, *args, **options):
        quiet = options.get('quiet', False)
        if not quiet:
            self.stdout.write('Trying to import MDT\n')
        if len(args) == 0:
            self.stdout.write('No MDT specified\n')
            return

        for mdt_file in args:
            cnt = 0
            # Checking for file
            if not os.path.exists(mdt_file):
                if not quiet:
                    self.stderr.write('Could not import %s: no such file\n' % mdt_file)
                continue

            file_obj = open(os.path.join(mdt_file))
            file_obj.seek(0)

            # Catch improper MDT payload
            try:
                mdt_data = json.load(file_obj)
            except ValueError, e:
                if not quiet:
                    self.stderr.write('MDT fail to create with bad json payload. %s\n' % e)
                continue
                pass

            # Try and validate MDT
            manager = MetaDataTemplateManager()
            if not manager.validate_mdt(mdt_data):
                if not quiet:
                    self.stderr.write('MDT %s fail to create. JSON did not validate.\n', mdt_file)
                continue

            # Store MDT
            result = manager.store(mdt_data)
            if result is False:
                if not quiet:
                    self.stderr.write('MDT %s creation error occurred on storing process.\n', mdt_file)
                continue

            if result and not quiet:
                self.stderr.write(str(result))
                self.stdout.write('\n')
            if result:
                cnt += 1
        if not quiet:
            self.stdout.write("Imported %s MDT's" % str(cnt))
            self.stdout.write('\n')
