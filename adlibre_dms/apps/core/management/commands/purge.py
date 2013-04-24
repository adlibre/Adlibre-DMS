"""
Module: PURGE (Expunge) marked deleted files and revisions for DMS

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
Author: Iurii Garmash (yuri@adlibre.com.au)

Description:

 - uses special CouchDB views to destroy marked deleted revisions and/or codes

usage:
    $ python manage.py purge
    Deleted code: ADL-0001
    Deleted revision: 2 for code: ADL-0002
    $

"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from optparse import make_option

#from core.document_processor import DocumentProcessor
from dmscouch.models import CouchDocument
import core


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
    help = """Clean up (Really delete) all the "marked delete" documents"""

    def handle(self, *args, **options):
        quiet = options.get('quiet', False)
        codes = self.get_codes()
        if not quiet:
            if codes:
                self.stdout.write('Will now delete codes: %s \n' % codes)
            else:
                self.stdout.write('No Object codes to delete. \n')
        revisions = self.get_revisions()
        if not quiet:
            if codes:
                self.stdout.write("Will now delete additional doc's revisions in docs: %s \n"
                                  % [d[0] for d in revisions])
            else:
                self.stdout.write('No additional revision files to delete. \n')
        if codes or revisions:
            processor = core.document_processor.DocumentProcessor()
            user = User.objects.filter(is_superuser=True)[0]
            for code in codes:
                processor.delete(code, {'user': user})
                if not processor.errors:
                    if not quiet:
                        self.stdout.write('Permanently deleted object with code: %s' % code)
                else:
                    if not quiet:
                        self.stdout.write(processor.errors)
                    raise(Exception, processor.errors)
            for rev in revisions:
                processor.delete(rev[0], {'user': user, 'delete_revision': rev[1]})

    def get_codes(self):
        deleted_codes = CouchDocument.view('dmscouch/deleted')
        codes = [doc.get_id for doc in deleted_codes]
        return codes

    def get_revisions(self):
        """ Returns list of doc's deleted revisions in list of tuples (code, revision)
        e.g.: [('ADL-0001', '1'), ('BBB-0001', '3'), ... ] """
        deleted_revisions = CouchDocument.view('dmscouch/deleted_files_revisions')
        results = [(doc.get_id, doc['deleted_revision']) for doc in deleted_revisions]
        return results
