import json
import os
from datetime import datetime

from django.conf import settings

from dms_plugins.pluginpoints import StoragePluginPoint, BeforeRetrievalPluginPoint,\
    BeforeRemovalPluginPoint, UpdatePluginPoint
from dms_plugins.workers import Plugin, PluginError, BreakPluginChain
from dms_plugins.workers.storage.local import LocalFilesystemManager


class LocalJSONMetadata(object):
    """Stores metadata in the same directory as document revisions in JSON format."""
    def __init__(self):
        self.filesystem = LocalFilesystemManager()

    def store(self, document):
        if document.get_docrule().no_doccode:
            return document
        directory = self.filesystem.get_or_create_document_directory(document)
        document = self.save_metadata(document, directory)
        return document

    def retrieve(self, document):
        directory = self.filesystem.get_or_create_document_directory(document)
        if document.get_docrule().no_doccode:
            revision = 'N/A'
            fake_metadata = self.get_fake_metadata(directory, document.get_full_filename())
            document.set_revision(revision)
            document.set_metadata({revision: fake_metadata})
        else:
            fileinfo_db, new_revision = self.load_metadata(document.get_stripped_filename(), directory)
            if not fileinfo_db:
                raise PluginError("No such document: %s" % document.get_stripped_filename(), 404)
            revision = document.get_revision()
            if not revision and new_revision > 0:
                revision = new_revision - 1
            document.set_revision(revision)
            try:
                fileinfo = fileinfo_db[str(revision)]
            except:
                raise PluginError("No such revision for this document", 404)
            document.set_metadata(fileinfo_db)
        if document.get_option('only_metadata'):
            raise BreakPluginChain()
        return document

    def update_metadata_after_removal(self, document):
        revision = document.get_revision()
        if revision:
            directory = self.filesystem.get_or_create_document_directory(document)
            fileinfo_db, new_revision = self.load_metadata(document.get_stripped_filename(), directory)
            del fileinfo_db[str(revision)]
            self.write_metadata(fileinfo_db, document, directory)
        else:
            pass # our directory with all metadata has just been deleted %)
        return document

    def update(self, document):
        """Updates document metadata after it has been updated, e.g. updated revision"""
        if 'update_file' in document.options:
            # FIXME metadata should be updated more often if we plan to store secondary keys on a disk.
            directory = self.filesystem.get_or_create_document_directory(document)
            document = self.save_metadata(document, directory)
        return document

    """Internal manager methods"""
    def load_from_file(self, json_file):
        if os.path.exists(json_file):
            revisions = []
            json_handler = open(json_file , mode='r+')
#            if settings.DEBUG:
#                print json_file
            fileinfo_db = json.load(json_handler)
            revisions_unsorted = fileinfo_db.keys()
            for rev in revisions_unsorted:
                revisions.append(int(rev))
            revisions.sort()
#            if settings.DEBUG:
#                print 'Document Revisions: '
#                print revisions
            revision = max(revisions) + 1
#            if settings.DEBUG:
#                print 'Latest File Revision: ', str(revision - 1)
        else:
            fileinfo_db = {}
            revision = 1
        return fileinfo_db, revision

    def load_metadata(self, document_name, directory):
        json_file = os.path.join(directory, '%s.json' % (document_name,))
        file = self.load_from_file(json_file)
        return file

    def date_to_string(self, date):
        return date.strftime(settings.DATETIME_FORMAT)

    def string_to_date(self, string):
        try:
            date = datetime.strptime(string, settings.DATETIME_FORMAT)
        except ValueError:
            date = datetime.strptime(string[:10], settings.DATE_FORMAT)
        except:
            raise
        return date

    def save_metadata(self, document, directory):
        fileinfo_db, revision = self.load_metadata(document.get_stripped_filename(), directory)
        document.set_revision(revision)

        fileinfo = {
            'name' : document.get_filename_with_revision(),
            'revision' : document.get_revision(),
            'created_date' : self.date_to_string(datetime.today())
        }

        if document.get_current_metadata():
            fileinfo.update(document.get_current_metadata())

        fileinfo_db[document.get_revision()] = fileinfo

        self.write_metadata(fileinfo_db, document, directory)
        # Required for any update sequence
        document.set_metadata(fileinfo_db)
        return document

    def write_metadata(self, fileinfo_db, document, directory):
        json_file = os.path.join(directory, '%s.json' % (document.get_stripped_filename(),))
        json_handler = open(json_file, mode='w')
        json.dump(fileinfo_db, json_handler, indent = 4)

    def get_fake_metadata(self, root, fil):
        current_date = datetime.strftime(datetime.now(), settings.DATETIME_FORMAT)
        created_date = datetime.strptime(current_date, settings.DATETIME_FORMAT)
        return {   'created_date': created_date,
                    'name': fil,
                    'revision': 'N/A'
                }

    def get_directories(self, doccode, filter_date = None):
        """
        Return List of directories with document files
        """
        #FIXME: seems to be rather slow for large number of docs :(
        root = settings.DOCUMENT_ROOT
        doccode_directory = os.path.join(root, doccode.get_directory_name())

        directories = []
        for root, dirs, files in os.walk(doccode_directory):
            for fil in files:
                doc, extension = os.path.splitext(fil)
                metadatas = None
                first_metadata = None
                if extension == '.json':
                        metadatas = self.load_from_file(os.path.join(root, fil))[0]
                        keys = metadatas.keys()
                        keys.sort()
                        first_metadata = metadatas[keys[0]]
                elif doccode.no_doccode and not dirs:  # leaf directory, no metadata file => NoDoccode
                    first_metadata = self.get_fake_metadata(root, fil)
                    metadatas = [first_metadata]
                    doc = fil
                if filter_date and first_metadata and first_metadata and \
                        self.string_to_date(first_metadata['created_date']).date() != self.string_to_date(filter_date).date():
                            continue
                if metadatas and first_metadata:
                    directories.append( (root, {
                                                    'document_name': doc, 
                                                    'metadatas': metadatas,
                                                    'first_metadata': first_metadata,
                                                    }) )
        return directories

    def get_metadatas(self, doccode):
        """
        Return List of directories with document files
        """
        root = settings.DOCUMENT_ROOT
        doccode_directory = os.path.join(root, doccode.get_directory_name())

        metadatas = []
        for root, dirs, files in os.walk(doccode_directory):
            for fil in files:
                doc, extension = os.path.splitext(fil)
                if extension == '.json': #dirs with metadata
                    metadatas.append(self.load_from_file(os.path.join(root, fil)))
        return metadatas


class LocalJSONMetadataRetrievalPlugin(Plugin, BeforeRetrievalPluginPoint):
    title = "Filesystem Metadata Retrieval"
    description = "Loads document metadata as local file"

    plugin_type = 'metadata'
    worker = LocalJSONMetadata()

    def work(self, document, **kwargs):
        return self.worker.retrieve(document)


class LocalJSONMetadataStoragePlugin(Plugin, StoragePluginPoint):
    title = "Filesystem Metadata Storage"
    description = "Saves document metadata as local file"

    plugin_type = 'metadata'
    worker = LocalJSONMetadata()

    def work(self, document, **kwargs):
        return self.worker.store(document)


class LocalJSONMetadataRemovalPlugin(Plugin, BeforeRemovalPluginPoint):
    title = "Filesystem Metadata Removal"
    description = "Updates document metadata after removal of document (actualy some revisions of document)"

    plugin_type = 'metadata'
    worker = LocalJSONMetadata()

    def work(self, document, **kwargs):
        return self.worker.update_metadata_after_removal(document)


class LocalJSONMetadataUpdatePlugin(Plugin, UpdatePluginPoint):
    title = "Filesystem Metadata Update"
    description = "Updates document metadata after update. e.g. Update of document revision."

    plugin_type = 'metadata'
    worker = LocalJSONMetadata()

    def work(self, document, **kwargs):
        return self.worker.update(document)