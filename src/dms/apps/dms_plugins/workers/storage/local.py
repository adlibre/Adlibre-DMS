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

from dms_plugins.pluginpoints import BeforeStoragePluginPoint, BeforeRetrievalPluginPoint, BeforeRemovalPluginPoint
from dms_plugins.workers import Plugin, PluginError, BreakPluginChain

class NoRevisionError(Exception):
    def __str__(self):
        return "NoRevisionError - No such revision number"


def naturalsort(L, reverse=False):
    """
    Natural Language Sort
    """
    import re

    convert = lambda text: ('', int(text)) if text.isdigit() else (text, 0)
    alpha = lambda key: [ convert(char) for char in re.split('([0-9]+)', key['name']) ]
    return sorted(L, key=alpha, reverse=reverse)


class LocalFilesystemManager(object):
    def get_document_directory(self, document):
        root = settings.DOCUMENT_ROOT
        directory = document.splitdir()
        if not directory:
            raise PluginError("The document type is not supported.", 500) # no doccode for document
        directory = os.path.join(root, directory)
        return directory

    def get_or_create_document_directory(self, document):
        directory = self.get_document_directory(document)
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory

def filecount(directory):
    """
    Count the number of files in a directory
    """
    try:
        return len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])
    except Exception, e:
        return None

class Local(object):
    def __init__(self):
        self.filesystem = LocalFilesystemManager()

    def store(self, request, document):
        directory = self.filesystem.get_or_create_document_directory(document)
        destination = open(os.path.join(directory, document.get_filename_with_revision()), 'wb+')
        fil = document.get_file_obj()
        fil.seek(0)
        destination.write(fil.read())
        destination.close()
        return document

    def retrieve(self, request, document):
        directory = self.filesystem.get_document_directory(document)
        if document.get_current_metadata():
            fullpath = os.path.join(directory, document.get_current_metadata()['name'])
        else:
            fullpath = os.path.join(directory, document.get_filename())
        if not os.path.exists(fullpath):
            raise PluginError("No such document", 404)
        document.set_fullpath(fullpath)
        #file will be read on first access lazily
        if document.get_option('only_metadata') == True:
            raise BreakPluginChain()
        return document

    
        

    def get_list(self, doccode, directories, start = 0, finish = None, order = "created_date"):
        """
        Return List of DocCodes in the repository for a given rule
        """
        # Iterate through the directory hierarchy looking for metadata containing dirs.
        # This is more efficient than other methods of looking for leaf directories
        # and works for storage rules where the depth of the storage tree is not constant for all doccodes.

        # FIXME: This will be inefficient at scale and will require caching
        def sort_by_created_date(x, y):
            first = datetime.datetime.strptime(x[1]['metadatas'][0]['created_date'], settings.DATE_FORMAT)
            second = datetime.datetime.strptime(y[1]['metadatas'][0]['created_date'], settings.DATE_FORMAT)
            if first < second:
                return -1
            elif first > second:
                return 1
            return 0
        SORT_FUNCTIONS = {
            'created_date': sort_by_created_date,
        }
        try:
            directories.sort(SORT_FUNCTIONS[order])
        except KeyError:
            if settings.DEBUG:
                raise
            else:
                pass
        doccodes = []
        for directory, metadata_info in directories:
            if finish and len(doccodes) >= finish :
                break
            if not doccode.uses_repository:
                doccodes.append({'name': metadata_info['document_name'],
                    'directory': os.path.split(directory)[1]})
            else:
                doccodes.append({'name': metadata_info['document_name']})
        if start:
            doccodes = doccodes[start:]
        return naturalsort(doccodes)

    def remove(self, request, document):
        directory = self.filesystem.get_document_directory(document)
        try:
            shutil.rmtree(directory)
            return None
        except Exception, e:
            raise PluginError(str(e), 500)

    def get_revision_count(self, document):
        # Hacky way, but faster than reading the revs from the metadata
        directory = self.filesystem.get_document_directory(document)

        file_count = filecount(directory)
        if file_count:
            return filecount(directory) - 1
        else:
            return 0

class LocalStoragePlugin(Plugin, BeforeStoragePluginPoint):
    title = "Local Storage"
    description = "Saves document as local file"

    plugin_type = 'storage'
    worker = Local()

    def work(self, request, document, **kwargs):
        return self.worker.store(request, document)

class LocalRetrievalPlugin(Plugin, BeforeRetrievalPluginPoint):
    title = "Local Retrieval"
    description = "Loads document as local file"

    plugin_type = 'storage'
    worker = Local()

    def work(self, request, document, **kwargs):
        return self.worker.retrieve(request, document)

class LocalRemovalPlugin(Plugin, BeforeRemovalPluginPoint):
    title = "Local Removal"
    description = "Removes document from filestytem"

    plugin_type = 'storage'
    worker = Local()

    def work(self, request, document, **kwargs):
        return self.worker.remove(request, document)
