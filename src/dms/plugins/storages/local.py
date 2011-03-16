import os
import datetime

from django.conf import settings

from fileshare.models import Rule
from fileshare.utils import StorageProvider
import json


class NoRevisionError(Exception):
    def __str__(self):
        return "NoRevisionError - No such revision number"

def splitdir(document):
    rule = Rule.objects.match(document)
    doccode = rule.get_doccode()
    splitdir = ''
    for d in doccode.split(document):
        splitdir = "%s/%s" % (splitdir, d)
    return "%s/%s/%s" % (rule.id, splitdir, document)


class Local(StorageProvider):
    name = "Local Storage"
    description = "Local storage plugin"


    @staticmethod
    def store(f, root=settings.DOCUMENT_ROOT):
        filename = f.name
        document, extension = os.path.splitext(filename)
        extension = extension.strip(".")
        directory = splitdir(document)
        if root:
            directory = "%s/%s" % (root, directory)
        if not os.path.exists(directory):
            os.makedirs(directory)

        json_file = '%s/%s.json' % (directory, document)
        if os.path.exists(json_file):
            json_handler = open(json_file , mode='r+')
            fileinfo_db = json.load(json_handler)
            revision = fileinfo_db[-1]['revision'] + 1
        else:
            fileinfo_db = []
            revision = 1

        fileinfo = {
            'name' : "%s_r%s.%s" % (document, revision, extension),
            'revision' : revision,
            'created_date' : str(datetime.datetime.today())
        }
        fileinfo_db.append(fileinfo)
        json_handler = open(json_file, mode='w')
        json.dump(fileinfo_db, json_handler)

        destination = open('%s/%s' % (directory, fileinfo['name']), 'wb+')
        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()


    @staticmethod
    def get(filename, revision=None, root=settings.DOCUMENT_ROOT):
        document, extension = os.path.splitext(filename)
        extension = extension.strip(".")
        directory = splitdir(document)
        if root:
            directory = "%s/%s" % (root, directory)

        json_file = '%s/%s.json' % (directory, document)
        if os.path.exists(json_file):
            json_handler = open(json_file , mode='r+')
            fileinfo_db = json.load(json_handler)
            if revision:
                try:
                    fileinfo = fileinfo_db[int(revision)-1]
                except:
                    raise NoRevisionError
            else:
                fileinfo = fileinfo_db[-1]
        else:
            raise NoRevisionError # TODO: This should be a different exception
        fullpath = '%s/%s' % (directory, fileinfo['name'])
        return fullpath


    @staticmethod
    def revision(document, root=settings.DOCUMENT_ROOT):
        directory = splitdir(document)
        if root:
            directory = "%s/%s" % (root, directory)
        json_file = '%s/%s.json' % (directory, document)
        if os.path.exists(json_file):
            json_handler = open(json_file , mode='r+')
            fileinfo_db = json.load(json_handler)
            return fileinfo_db
        return None


    # FIXME: I really don't like the chain of dependency. This is called from piston handlers.py
    # which requires knowledge of the rule, and then the storage needs to know
    # which rule is invoked as well... its a bit of a mess.

    @staticmethod
    def get_list(id_rule, root=settings.DOCUMENT_ROOT):

        import os
        import glob

        # root of our storage tree for the given id_rule
        if root:
            directory = "%s/%s" % (root, id_rule)

        rule = Rule.objects.get(id=id_rule)

        for i in range(rule.get_doccode().splits + 1):
            directory = "%s/%s" % (directory, '*')

        files = []
        for file in glob.glob(directory):
            files.append(os.path.basename(file))
        return files
