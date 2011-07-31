import datetime
import json
import os

from django.conf import settings

from dms_plugins.pluginpoints import BeforeStoragePluginPoint, BeforeRetrievalPluginPoint, BeforeRemovalPluginPoint
from dms_plugins.workers import Plugin, PluginError, BreakPluginChain
from dms_plugins.workers.storage.local import LocalFilesystemManager

class LocalJSONMetadata(object):
    """
        Stores metadata in the same directory as document revisions in JSON format.
    """
    def __init__(self):
        self.filesystem = LocalFilesystemManager()

    def store(self, request, document):
        directory = self.filesystem.get_or_create_document_directory(document)
        document = self.save_metadata(document, directory)
        return document

    def retrieve(self, request, document):
        directory = self.filesystem.get_or_create_document_directory(document)
        fileinfo_db, new_revision = self.load_metadata(document.get_stripped_filename(), directory)
        if not fileinfo_db:
            raise PluginError("No such document", 404)
        revision = document.get_revision()
        if not revision and new_revision > 0:
            revision = new_revision - 1
        document.set_revision(revision)
        try:
            fileinfo = fileinfo_db[int(revision)-1]
        except:
            raise PluginError("No such revision for this document", 404)
        document.set_metadata(fileinfo_db)
        if document.get_option('only_metadata') == True:
            raise BreakPluginChain()
        return document

    def load_from_file(self, json_file):
        if os.path.exists(json_file):
            json_handler = open(json_file , mode='r+')
            fileinfo_db = json.load(json_handler)
            revision = fileinfo_db[-1]['revision'] + 1
        else:
            fileinfo_db = []
            revision = 1
        return fileinfo_db, revision

    def load_metadata(self, document_name, directory):
        json_file = os.path.join(directory, '%s.json' % (document_name,))
        return self.load_from_file(json_file)

    def date_to_string(self, date):
        return date.strftime(settings.DATETIME_FORMAT)

    def string_to_date(self, string):
        try:
            date = datetime.datetime.strptime(string, settings.DATETIME_FORMAT)
        except ValueError:
            date = datetime.datetime.strptime(string[:10], settings.DATE_FORMAT)
        except:
            raise
        return date

    def save_metadata(self, document, directory):
        fileinfo_db, revision = self.load_metadata(document.get_stripped_filename(), directory)
        document.set_revision(revision)

        fileinfo = {
            'name' : document.get_filename_with_revision(),
            'revision' : document.get_revision(),
            'created_date' : self.date_to_string(datetime.datetime.today())
        }

        if document.get_current_metadata():
            fileinfo.update(document.get_current_metadata())

        fileinfo_db.append(fileinfo)

        self.write_metadata(fileinfo_db, document, directory)

        return document

    def write_metadata(self, fileinfo_db, document, directory):
        json_file = os.path.join(directory, '%s.json' % (document.get_stripped_filename(),))
        json_handler = open(json_file, mode='w')
        json.dump(fileinfo_db, json_handler, indent = 4)

    def get_directories(self, doccode, filter_date = None):
        """
        Return List of directories with document files
        """
        #FIXME: seems to be rather slow for large number of docs :(
        root = settings.DOCUMENT_ROOT
        doccode_directory = os.path.join(root, str(doccode.get_id()))

        directories = []
        for root, dirs, files in os.walk(doccode_directory):
            for fil in files:
                doc, extension = os.path.splitext(fil)
                if extension == '.json' or (not doccode.uses_repository and not dirs): #dirs with metadata or leaf dirs
                        metadatas = self.load_from_file(os.path.join(root, fil))[0]
                        if filter_date and metadatas[0] and metadatas[0] and \
                        self.string_to_date(metadatas[0]['created_date']).date() != self.string_to_date(filter_date).date():
                            continue
                            #print "%s != %s" % (self.string_to_date(metadatas[0]['created_date']).date(), self.string_to_date(filter_date).date())
                        #print "%s appended" % doc
                        directories.append( (root, {
                                                    'document_name': doc, 
                                                    'metadatas': metadatas
                                                    }) )
        return directories

    def get_metadatas(self, doccode):
        """
        Return List of directories with document files
        """
        root = settings.DOCUMENT_ROOT
        doccode_directory = os.path.join(root, str(doccode.get_id()))

        metadatas = []
        for root, dirs, files in os.walk(doccode_directory):
            for fil in files:
                doc, extension = os.path.splitext(fil)
                if extension == '.json': #dirs with metadata
                    metadatas.append(self.load_from_file(os.path.join(root, fil)))
        return metadatas

    def update_metadata_after_removal(self, request, document):
        revision = document.get_revision()
        if revision:
            directory = self.filesystem.get_or_create_document_directory(document)
            fileinfo_db, new_revision = self.load_metadata(document.get_stripped_filename(), directory)
            for metadata in fileinfo_db:
                if int(metadata['revision']) == int(revision):
                    del(metadata)
                    break
            self.write_metadata(fileinfo_db, document, directory)
        else:
            pass # our directory with all metadata has just been deleted %)

class LocalJSONMetadataRetrievalPlugin(Plugin, BeforeRetrievalPluginPoint):
    title = "Local Metadata Retrieval"
    description = "Loads document metadata as local file"

    plugin_type = 'metadata'
    worker = LocalJSONMetadata()

    def work(self, request, document, **kwargs):
        return self.worker.retrieve(request, document)

class LocalJSONMetadataStoragePlugin(Plugin, BeforeStoragePluginPoint):
    title = "Local Metadata Storage"
    description = "Saves document metadata as local file"

    plugin_type = 'metadata'
    worker = LocalJSONMetadata()

    def work(self, request, document, **kwargs):
        return self.worker.store(request, document)

class LocalJSONMetadataRemovalPlugin(Plugin, BeforeRemovalPluginPoint):
    title = "Local Metadata Removal"
    description = "Updates document metadata after removal of document (actualy some revisions of document)"

    plugin_type = 'metadata'
    worker = LocalJSONMetadata()

    def work(self, request, document, **kwargs):
        return self.worker.update_metadata_after_removal(request, document)
