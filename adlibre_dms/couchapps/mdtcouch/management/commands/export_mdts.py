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
    help = "Exports Meta Data Templates from DMS into json file\n"
    args = 'No args possible'

    def handle(self, *args, **options):
        quiet = options.get('quiet', False)
        if not quiet:
            self.stdout.write("Export of DMS MDT's command called.\n")

        # Try and Fetch all mdts
        manager = MetaDataTemplateManager()
        mdts = manager.get_all_mdts()
        # Validating all OK
        if not mdts:
            if not quiet:
                self.stderr.write('DMS has no MDT-s.')
            return

        for mdt_link in mdts.itervalues():

            filename = mdt_link['mdt_id']
            mdt_instance = manager.get_mdts_by_name([filename, ])
            filename += '.json'
            file_obj = open(os.path.join(filename), 'w+')
            file_obj.seek(0)
            mdt_obj = mdt_instance['1']
            try:
                del mdt_obj["doc_type"]
            except KeyError:
                pass
            mdt_jsoned = json.dumps(mdt_obj, sort_keys=True, indent=4)
            file_obj.write(mdt_jsoned)
            if not quiet:
                self.stderr.write('Exported to file: %s\n'% filename)

        if not quiet:
            self.stdout.write("Exporting %s MDT's" % str(len(mdts)))
            self.stdout.write('\n')
