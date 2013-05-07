"""
Module: Document import management script for Adlibre DMS

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
"""

import os
import traceback

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

from core.document_processor import DocumentProcessor


class Command(BaseCommand):
    args = '<directory_name directory_name ...>'
    help = 'Imports the documents from specified directory'

    def handle(self, *args, **options):

        silent = 'silent' in options.keys() and options['silent']
        if len(args) == 0:
            self.stdout.write('No arguments specified\n')
            return

        for directory in args:
            if not os.path.exists(directory):
                self.stderr.write('Could not import %s: no such directory\n' % directory)
                continue
            cnt = 0
            admin = User.objects.filter(is_superuser=True)[0]
            for root, dirs, files in os.walk(directory):
                if '.svn' in dirs:
                    dirs.remove('.svn')  # don't visit svn directories
                for filename in files:
                    if not silent:
                        self.stdout.write('Importing file: "%s"\n' % filename)
                    file_obj = open(os.path.join(root, filename))
                    file_obj.seek(0)
                    processor = DocumentProcessor()
                    try:
                        processor.create(file_obj, {'user': admin})
                    except Exception:
                        self.stderr.write(traceback.format_exc() + "\n")
                    else:
                        if processor.errors:
                            self.stderr.write('\nImport error: %s\n' % processor.errors)
                        else:
                            cnt += 1
                    file_obj.close()
            if not silent:
                if cnt:
                    self.stdout.write('Successfully imported %s documents from directory "%s"\n' % (cnt, directory))
                else:
                    self.stdout.write('No documents were imported\n')
