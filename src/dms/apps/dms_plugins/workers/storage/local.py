"""
Module: Local Storage
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

import datetime
import json
import os
import shutil

from django.conf import settings

from dms_plugins.workers import PluginError

class NoRevisionError(Exception):
    def __str__(self):
        return "NoRevisionError - No such revision number"


def naturalsort(L, reverse=False):
    """
    Natural Language Sort
    """
    import re

    convert = lambda text: ('', int(text)) if text.isdigit() else (text, 0)
    alpha = lambda key: [ convert(char) for char in re.split('([0-9]+)', key) ]
    return sorted(L, key=alpha, reverse=reverse)


def filecount(directory):
    """
    Count the number of files in a directory
    """
    try:
        return len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])
    except Exception, e:
        return None

def splitdir(document):
    directory = None
    doccode = document.get_doccode()
    if doccode:
        splitdir = ''
        for d in doccode.split(document.get_stripped_filename()):
            splitdir = os.path.join(splitdir, d)
        directory = os.path.join(str(doccode.get_id()), splitdir, document.get_filename()) # TODO: doccode.get_id
    return directory

class Local(object):
    def store(self, request, document):
        root = settings.DOCUMENT_ROOT

        directory = splitdir(document)
        if not directory:
            raise PluginError("The document type is not supported.") # no doccode for document
        directory = os.path.join(root, directory)
        if not os.path.exists(directory):
            os.makedirs(directory)

        #save metadata, load revision
        document = self.save_metadata(document, directory)

        destination = open(os.path.join(directory, document.get_filename_with_revision()), 'wb+')
        document.get_uploaded_file().seek(0)
        destination.write(document.get_uploaded_file().read())
        destination.close()

    def save_metadata(self, document, directory):
        json_file = os.path.join(directory, '%s.json' % (document.get_stripped_filename(),))
        if os.path.exists(json_file):
            json_handler = open(json_file , mode='r+')
            fileinfo_db = json.load(json_handler)
            revision = fileinfo_db[-1]['revision'] + 1
        else:
            fileinfo_db = []
            revision = 1

        document.set_revision(revision)

        fileinfo = {
            'name' : document.get_filename_with_revision(),
            'revision' : document.get_revision(),
            'created_date' : str(datetime.datetime.today())
        }
        fileinfo_db.append(fileinfo)
        json_handler = open(json_file, mode='w')
        json.dump(fileinfo_db, json_handler)
        return document

    def _store(self, file_obj, filename, root=settings.DOCUMENT_ROOT):
        document, extension = os.path.splitext(filename)
        extension = extension.strip(".")
        directory = splitdir(document)

        if root:
            directory = "%s/%s" % (root, directory)
        else:
            raise Exception('Root not specified')
        
        if not os.path.exists(directory):
            os.makedirs(directory)

        # TODO: metadata should be written in separate method
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
        file_obj.seek(0)
        destination.write(file_obj.read())
        destination.close()


    @staticmethod
    def retrieve(filename, revision=None, root=settings.DOCUMENT_ROOT):
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
            raise NoRevisionError # TODO: This should NoDocumentExists exception
        fullpath = '%s/%s' % (directory, fileinfo['name'])
        file_obj = open(fullpath, 'rb')
        return file_obj


    # TODO: Extend to handle revisions
    @staticmethod
    def delete(filename, revision=None, root=settings.DOCUMENT_ROOT):
        document, extension = os.path.splitext(filename)
        extension = extension.strip(".")
        directory = splitdir(document)
        if root:
            directory = "%s/%s" % (root, directory)
            try:
                shutil.rmtree(directory)
                return None
            except:
                raise NoRevisionError # FIXME: Should be something else
        else:
            return None


    @staticmethod
    def get_meta_data(document, root=settings.DOCUMENT_ROOT):
        directory = splitdir(document)
        if root:
            directory = "%s/%s" % (root, directory)
        json_file = '%s/%s.json' % (directory, document)
        if os.path.exists(json_file):
            json_handler = open(json_file , mode='r+')
            fileinfo_db = json.load(json_handler)
            return fileinfo_db
        return None


    @staticmethod
    def get_revision_count(document, root=settings.DOCUMENT_ROOT):
        # Hacky way, but faster than reading the revs from the metadata
        directory = splitdir(document)
        if root:
            directory = "%s/%s" % (root, directory)

        file_count = filecount(directory)
        if file_count:
            return filecount(directory) - 1
        else:
            return 0


    @staticmethod
    def get_list(id_rule, root=settings.DOCUMENT_ROOT):
        """
        Return List of DocCodes in the repository for a given rule
        """
        directory = "%s/%s" % (root, id_rule)

        # Iterate through the directory hierarchy looking for metadata containing dirs.
        # This is more efficient than other methods of looking for leaf directories
        # and works for storage rules where the depth of the storage tree is not constant for all doccodes.

        # FIXME: This will be inefficient at scale and will require caching

        doccodes = []
        for root, dirs, files in os.walk(directory):
            for file in files:
                doc, extension = os.path.splitext(file)
                if extension == '.json':
                    doccodes.append(doc)
        return naturalsort(doccodes)

