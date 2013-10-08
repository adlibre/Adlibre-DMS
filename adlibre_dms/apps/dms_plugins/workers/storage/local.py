"""
Module: Local Storage
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
"""

import datetime
import os
import shutil
import logging

from django.conf import settings

from dms_plugins.pluginpoints import StoragePluginPoint, BeforeRetrievalPluginPoint, BeforeRemovalPluginPoint,\
    UpdatePluginPoint
from dms_plugins.workers import Plugin, PluginError, BreakPluginChain

log = logging.getLogger('dms')

class NoRevisionError(Exception):
    def __str__(self):
        return "NoRevisionError - No such revision number"


def naturalsort(L, reverse=False):
    """Natural Language Sort"""
    import re

    convert = lambda text: ('', int(text)) if text.isdigit() else (text, 0)
    alpha = lambda key: [ convert(char) for char in re.split('([0-9]+)', key['name']) ]
    return sorted(L, key=alpha, reverse=reverse)


class LocalFilesystemManager(object):
    def get_document_directory(self, document):
        root = settings.DOCUMENT_ROOT
        # TODO: Refactoring for v2 (splitdir() method from Document() object used only here.)
        directory = None
        docrule = document.get_docrule()
        if docrule:
            splitdir = ''
            for d in docrule.split(document.get_stripped_filename()):
                splitdir = os.path.join(splitdir, d)
            directory = os.path.join(str(docrule.get_id()), splitdir)

        if not directory:
            raise PluginError("The document type is not supported.", 500)  # no docrule for document
        directory = os.path.join(root, directory)
        return directory

    def get_or_create_document_directory(self, document):
        directory = self.get_document_directory(document)
        if not os.path.exists(directory):
            os.makedirs(directory)
        return directory

    def move_file(self, source_path, destination_path):
        """Filesystem worker to move file from one path to another."""
        try:
            os.rename(source_path, destination_path)
        except Exception, e:
            log.error("LocalFilesystemManager. File moving Error: %s", e)
            return False
        return True

    def remove_file(self, path_with_file):
        try:
            os.remove(path_with_file)
            return True
        except Exception, e:
            log.error("LocalFilesystemManager. File removal error: %s" % e)
            return False


def file_present(file_name, directory):
    """Determine if file is present in directory"""
    return file_name in os.listdir(directory)


def filecount(directory):
    """Count the number of files in a directory"""
    try:
        return len([f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))])
    except Exception, e:
        log.error('plugins.workers.storage.local.LocalFilesystemManager().filecount error: %s' % e)
        return None


class Local(object):
    def __init__(self):
        self.filesystem = LocalFilesystemManager()

    def store(self, document):
        if not document.get_option('only_metadata'):
            self.store_new_file(document)
        return document

    def retrieve(self, document):
        if document.get_option('only_metadata'):
            return document
        directory = self.filesystem.get_document_directory(document)
        if not document.get_docrule().no_doccode:
            fullpath = os.path.join(directory, document.get_current_file_revision_data()['name'])
        else:
            filename = document.get_full_filename()
            fullpath = os.path.join(directory, filename)
        if not os.path.exists(fullpath):
            raise PluginError("No such document: %s" % fullpath, 404)
        document.set_fullpath(fullpath)

        if 'revision_count' in document.options:
            if document.options['revision_count']:
                revision = self.get_revision_count(document)
                print 'GOT Document revision: %s' % revision
                document.revision = revision
        return document

    def update(self, document):
        if 'update_file' in document.options.iterkeys() and document.options['update_file'] is not None:
            self.store_new_file(document)
        if document.old_docrule:
            # Renaming and moving files to new location files
            new_directory = self.filesystem.get_or_create_document_directory(document)
            new_name = document.get_filename()
            file_revision_data = document.get_file_revisions_data()
            # Making new document OLD one for retrieving data purposes
            document.docrule = None
            document.set_filename(document.old_name_code)
            old_directory = self.filesystem.get_or_create_document_directory(document)
            old_code = document.old_name_code
            # Returning document back to normal
            document.docrule = None
            document.set_filename(new_name)
            for key, value in file_revision_data.iteritems():
                new_file_revision = value['name']
                new_path = os.path.join(new_directory, new_file_revision)
                old_rev_name = self.convert_metadata_for_revision(new_file_revision, old_code, key)
                old_path = os.path.join(old_directory, old_rev_name)
                status = self.filesystem.move_file(old_path, new_path)
                if not status:
                    raise PluginError("File moving problem. File %s does not exists" % old_rev_name, 500)
        return document

    def document_matches_search(self, metadata_info, searchword):
        result = False
        print "%s is in %s: %s" % (searchword, metadata_info['document_name'], 
            searchword.lower() in metadata_info['document_name'].lower())
        if searchword.lower() in metadata_info['document_name'].lower():
            result = True
        return result

    def convert_metadata_for_revision(self, old_file_name, new_name, rev_key):
        """Converts file metadata into another docrule, changing it's file name everywhere"""
        extension = old_file_name.split('.')[1]
        prefix = '_r%s.%s' % (rev_key, extension)
        changed_name = new_name + prefix
        return changed_name

    def get_list(self, docrule, directories, start = 0, finish = None, order = None, searchword = None,
                        limit_to = []):
        """
        Return List of DocCodes in the repository for a given rule
        """
        # Iterate through the directory hierarchy looking for file revision data containing dirs.
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
            if finish and len(doccodes) >= finish:
                break
            elif searchword and not self.document_matches_search(metadata_info, searchword):
                pass
            elif limit_to and doc_name not in limit_to:
                #print "LIMIT TO = %s, DOC_NAME = %s" % (limit_to, doc_name)
                pass
            else:
                if docrule.no_doccode:
                    doccodes.append({
                        'name': doc_name,
                        'directory': os.path.split(directory)[1]
                    })
                else:
                    doccodes.append({'name': doc_name})
        if start:
            doccodes = doccodes[start:]
        return doccodes

    def remove(self, document):
        # TODO: FIXME: Refactor this method so it's safer!
        # Doing nothing for mark deleted call
        opts = [o for o in document.options.iterkeys()]
        if ('mark_deleted' in opts) or ('mark_revision_deleted' in opts):
            return document
        directory = self.filesystem.get_document_directory(document)
        filename = None
        if document.get_revision():
            filename = document.get_filename_with_revision()
        if filename:
            #print "Deleting Filename: ", filename
            #print "In directory: ", directory
            try:
                os.unlink(os.path.join(directory, filename))
            except Exception, e:
                raise PluginError(str(e), 500)

        #check if only '.json' file left in the directory for e.g.
        if not filename:
            try:
                shutil.rmtree(directory)
            except Exception, e:
                log.error('LocalFileStorage delete exception %s' % e)
                pass
                # Do not rise anything because we are now supporting delete for code with 0 file revisions
                #raise PluginError(str(e), 500)
        return document

    def get_revision_count(self, document):
        """Hacky way, but faster than reading the revs from the file revision data"""
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

    def store_new_file(self, document):
        directory = self.filesystem.get_or_create_document_directory(document)
        #print "STORE IN %s" % directory
        destination = open(os.path.join(directory, document.get_filename_with_revision()), 'wb+')
        fil = document.get_file_obj()
        fil.seek(0)
        destination.write(fil.read())
        destination.close()


class LocalStoragePlugin(Plugin, StoragePluginPoint):
    title = "Local Storage"
    description = "Saves document as local file"

    plugin_type = 'storage'
    worker = Local()

    def work(self, document, **kwargs):
        return self.worker.store(document)


class LocalRetrievalPlugin(Plugin, BeforeRetrievalPluginPoint):
    title = "Local Retrieval"
    description = "Loads document as local file"

    plugin_type = 'storage'
    worker = Local()

    def work(self, document, **kwargs):
        return self.worker.retrieve(document)


class LocalRemovalPlugin(Plugin, BeforeRemovalPluginPoint):
    title = "Local Removal"
    description = "Removes document from filesystem"

    plugin_type = 'storage'
    worker = Local()

    def work(self, document, **kwargs):
        return self.worker.remove(document)


class LocalUpdatePlugin(Plugin, UpdatePluginPoint):
    title = "Local Update"
    description = "Updates document in the filesystem"

    plugin_type = 'storage'
    worker = Local()

    def work(self, document, **kwargs):
        return self.worker.update(document)
