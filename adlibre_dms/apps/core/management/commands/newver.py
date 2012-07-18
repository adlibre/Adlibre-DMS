"""
Module: Version incremental script for Adlibre DMS

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash (yuri@adlibre.com.au)

Description:

 - used to increment internal version in DMS to render for user.
 - updates file 'version.txt' that should be in settings.PROJECT_PATH
 - increments version with pattern $+.$.$

usage:
    $ python manage.py newver
    Current version is: 11.1.9
    New version: 11.2.0
    $

"""

import os

from django.core.management.base import BaseCommand
from optparse import make_option

CUR_PATH = os.path.abspath(os.path.split(__file__)[0])

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
    help = "Increments DMS internal version number"

    def handle(self, *args, **options):
        quiet = options.get('quiet', False)
        ver_file = self.getverfile()
        version = self.getver(ver_file)
        if not quiet:
            self.stdout.write('Current version is: ' + version + '\n')

        new_ver = self.incremetver(version)
        if not quiet:
            self.stdout.write('New version: %s \n' % new_ver)

        self.storever(ver_file, new_ver)

    def getverfile(self):
        # Getting file and retrieveing version file
        version_path = os.path.join(CUR_PATH, '..', '..', '..', '..')
        version_file = os.path.join(version_path, 'version.txt')
        ver_file = open(version_file, 'r+')
        return ver_file

    def getver(self, ver_file):
        # Extracting version file content
        version = ver_file.read()
        return version

    def incremetver(self, ver):
        # Parsing and incrementing version
        ver_list = ver.split('.')
        lastnum = int(ver_list[2])
        midnum = int(ver_list[1])
        main = int(ver_list[0])
        # Incrementing version by one taking dots into account
        if lastnum == 9:
            if midnum == 9:
                main += 1
                midnum = 0
                lastnum = 0
            else:
                midnum += 1
                lastnum = 0
        else:
            lastnum +=1
        # Completing version string
        version = '%s.%s.%s' % (main, midnum, lastnum)
        return version

    def storever(self, verfile, new_ver):
        verfile.seek(0)
        verfile.write(new_ver)
        return verfile