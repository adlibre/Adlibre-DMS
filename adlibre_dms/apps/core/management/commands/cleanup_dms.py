"""
Module: Cleanup Adlibre DMS from tests data without running all the tests

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash (yuri@adlibre.com.au)

Description:

 - used to clean up all the tests data from working DMS copy

usage:
    $ python manage.py cleanup_dms
    $ ...

"""

import os
import shutil
import subprocess
from optparse import make_option
from django.core.management.base import BaseCommand
from django.conf import settings

from couchdbkit import Server


class Command(BaseCommand):

    def __init__(self):
        BaseCommand.__init__(self)
        self.option_list += (
            make_option(
                '--quiet', '-q',
                default=False,
                action='store_true',
                help='Hide all command output.'),
        )
        self.option_list += (
            make_option(
                '--prod-indexes', '-p',
                default=False,
                action='store_true',
                help='Delete all production databases indexes in CouchDB. e.g. "dmscouch" and "mdtcouch" databases.'),
        )

    help = "Cleanup DMS from all tests data."

    def handle(self, *args, **options):
        quiet = options.get('quiet', False)
        prod_indexes = options.get('prod-indexes', False)
        docs_root = os.path.normpath(settings.DOCUMENT_ROOT)
        if not quiet:
            self.stdout.write('Cleaning UP stored files in DOCUMENT_ROOT: %s \n' % docs_root)
        shutil.rmtree(docs_root)
        os.makedirs(docs_root)
        if not quiet:
            self.stdout.write('done\n')

        if not quiet:
            self.stdout.write('Deleting CouchDB debug mode databases.\n')

        databases = settings.COUCHDB_DATABASES
        server = Server()
        try:
            for database in databases:
                dbname = database[0] + '_test'
                if not quiet:
                    self.stdout.write('Deleting DB: %s\n' % dbname)
                server.delete_db(dbname)
            if not quiet:
                self.stdout.write('done\n')
        except Exception, e:
            if not quiet:
                self.stdout.write('Failed to delete debug databases in CouchDB: %s ' % e)
            pass

        if prod_indexes:
            if not quiet:
                self.stdout.write('Deleting CouchDB production databases.\n')
            for database in databases:
                dbname = database[0] + '_test'
                if not quiet:
                    self.stdout.write('Deleting DB: %s\n' % dbname)
                server.delete_db(dbname)
            if not quiet:
                self.stdout.write('done\n')

        db_file = os.path.normpath(settings.DATABASES['default']['NAME'])
        if not quiet:
            self.stdout.write('Recreating SQL DB: %s.\n' % db_file)
        os.remove(db_file)
        # Using django-admin.py to populate and create main config DB
        subprocess.call(['django-admin.py', 'syncdb', '--noinput', '--all', ])
        if not quiet:
            self.stdout.write('Done DB.\n')

        for app in ['core', 'dms_plugins']:
            if not quiet:
                self.stdout.write('Applying schema migrations for South app: %s.\n' % app)

            subprocess.call(['python', 'manage.py', 'migrate', app, '--fake', ])
            if not quiet:
                self.stdout.write('Done migrating app: %s\n' % app)

        if not quiet:
            self.stdout.write('Finished!\n')

