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
#import traceback

from django.conf import settings

from dms_plugins.pluginpoints import BeforeStoragePluginPoint, BeforeRetrievalPluginPoint, BeforeRemovalPluginPoint,\
BeforeUpdatePluginPoint
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

def file_present(file_name, directory):
    """
    Determine if file is present in directory
    """
    return file_name in os.listdir(directory)

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
        #print "STORE IN %s" % directory
        destination = open(os.path.join(directory, document.get_filename_with_revision()), 'wb+')
        fil = document.get_file_obj()
        fil.seek(0)
        destination.write(fil.read())
        destination.close()
        return document

    def retrieve(self, request, document):
        directory = self.filesystem.get_document_directory(document)
        if not document.get_docrule().no_doccode:
            fullpath = os.path.join(directory, document.get_current_metadata()['name'])
        else:
            filename = document.get_full_filename()
            fullpath = os.path.join(directory, filename)
        if not os.path.exists(fullpath):
            raise PluginError("No such document: %s" % fullpath, 404)
        document.set_fullpath(fullpath)
        #file will be read on first access lazily
        if document.get_option('only_metadata') == True:
            raise BreakPluginChain()
        return document

    def update(self, request, document):
        return document

    def document_matches_search(self, metadata_info, searchword):
        result = False
        print "%s is in %s: %s" % (searchword, metadata_info['document_name'], 
            searchword.lower() in metadata_info['document_name'].lower())
        if searchword.lower() in metadata_info['document_name'].lower():
            result = True
        return result

    def get_list(self, doccode, directories, start = 0, finish = None, order = None, searchword = None, 
                        limit_to = []):
        """
        Return List of DocCodes in the repository for a given rule
        """
        # Iterate through the directory hierarchy looking for metadata containing dirs.
        # This is more efficient than other methods of looking for leaf directories
        # and works for storage rules where the depth of the storage tree is not constant for all doccodes.

        # FIXME: This will be inefficient at scale and will require caching

        #FIXME: very un-elegant way to define available sort functions
        def sort_by_created_date(x, y):
            first = datetime.datetime.strptime(x[1]['first_metadata']['created_date'], settings.DATETIME_FORMAT)
            second = datetime.datetime.strptime(y[1]['first_metadata']['created_date'], settings.DATETIME_FORMAT)
            return cmp(first, second)
        def sort_by_name(x, y):
            first = x[1]['document_name']
            second = y[1]['document_name']
            return cmp(first, second)
        if order:
            SORT_FUNCTIONS = {
                'created_date': sort_by_created_date,
                'name': sort_by_name,
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
            doc_name = metadata_info['document_name']
            if finish and len(doccodes) >= finish :
                break
            elif searchword and not self.document_matches_search(metadata_info, searchword):
                pass
            elif limit_to and doc_name not in limit_to:
                #print "LIMIT TO = %s, DOC_NAME = %s" % (limit_to, doc_name)
                pass
            else:
                if doccode.no_doccode:
                    doccodes.append({'name': doc_name,
                        'directory': os.path.split(directory)[1]})
                else:
                    doccodes.append({'name': doc_name})
        if start:
            doccodes = doccodes[start:]
        #print "DOCCODES: %s" % doccodes
        return doccodes

    def remove(self, request, document):
        directory = self.filesystem.get_document_directory(document)
        filename = None
        if document.get_docrule().no_doccode:
            filename = document.get_full_filename()
        elif document.get_revision():
            filename = document.get_filename_with_revision()
        if filename:
            try:
                os.unlink(os.path.join(directory, filename))
            except Exception, e:
                raise PluginError(str(e), 500)

        if not filename or (document.get_docrule().no_doccode and len(os.listdir(directory)) == 0) or\
                len(os.listdir(directory)) <= 1: # delete everything or no files at all or only metadata file
            try:
                shutil.rmtree(directory)
            except Exception, e:
                raise PluginError(str(e), 500)

        # TODO: farther test if it is proper fix for Bug #399 (will it break something more)
        #if document.get_revision:
        #    document.set_revision(None) # should not perform anything in later plugins.
        """
        if document.get_revision():
            filename = document.get_filename_with_revision()
            try:
                os.unlink(os.path.join(directory, filename))
            except Exception, e:
                raise PluginError(str(e), 500)
            if len(os.listdir(directory)) <= 1: # no files at all or only metadata file
                try:
                    shutil.rmtree(directory)
                except Exception, e:
                    raise PluginError(str(e), 500)
                document.set_revision(None) # should not perform anything in later plugins.
        else:
            filename = document.get_full_filename()
            try:
                os.unlink(os.path.join(directory, filename))
                #print "No doccode file %s unlinked!" % os.path.join(directory, filename)
                #traceback.print_stack()
            except Exception, e:
                raise PluginError(str(e), 500)
            if len(os.listdir(directory)) == 0: # no files at all for no_doccode
                try:
                    shutil.rmtree(directory)
                except Exception, e:
                    raise PluginError(str(e), 500)
        """
        return document

    def get_revision_count(self, document):
        # Hacky way, but faster than reading the revs from the metadata
        directory = self.filesystem.get_document_directory(document)
        file_count = 0
        if document.get_docrule().no_doccode:
            if file_present(document.get_full_filename(), directory):
                file_count = 1
        else:
            file_count = filecount(directory)
            if file_count:
                file_count -= 1
        return file_count

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
    description = "Removes document from filesystem"

    plugin_type = 'storage'
    worker = Local()

    def work(self, request, document, **kwargs):
        return self.worker.remove(request, document)

class LocalUpdatePlugin(Plugin, BeforeUpdatePluginPoint):
    title = "Local Update"
    description = "Updates document in the filesystem"

    plugin_type = 'storage'
    worker = Local()

    def work(self, request, document, **kwargs):
        return self.worker.update(request, document)
