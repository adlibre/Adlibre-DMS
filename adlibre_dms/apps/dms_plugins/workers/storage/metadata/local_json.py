import json
import os
from datetime import datetime

from django.conf import settings

from dms_plugins.pluginpoints import StoragePluginPoint, BeforeRetrievalPluginPoint,\
    BeforeRemovalPluginPoint, UpdatePluginPoint
from dms_plugins.workers import Plugin, PluginError, BreakPluginChain
from dms_plugins.workers.storage.local import LocalFilesystemManager


class LocalJSONMetadata(object):
    """Stores file revision data in the same directory as document revisions in JSON format."""
    def __init__(self):
        self.filesystem = LocalFilesystemManager()

    def store(self, document):
        if document.get_docrule().uncategorized:
            return document
        if document.get_option('only_metadata'):
            # Doing nothing for storage of "Only code" and/or metadata (Into Indexing DB)
            return document
        directory = self.filesystem.get_or_create_document_directory(document)
        document = self.save_metadata(document, directory)
        return document

    def retrieve(self, document):
        only_metadata = document.get_option('only_metadata')
        directory = self.filesystem.get_document_directory(document)
        if document.get_docrule().uncategorized:
            revision = 'N/A'
            fake_metadata = self.get_fake_metadata(directory, document.get_full_filename())
            document.set_revision(revision)
            document.set_file_revisions_data({revision: fake_metadata})
        else:
            fileinfo_db, new_revision = self.load_metadata(document.get_code(), directory)
            if not fileinfo_db and not only_metadata:
                raise PluginError("No such document: %s" % document.get_code(), 404)
            revision = document.get_revision()
            if not revision and new_revision > 0:
                revision = new_revision - 1
            document.set_revision(revision)
            try:
                fileinfo_db[str(revision)]
            except KeyError:
                if not only_metadata and revision:
                    raise PluginError("No such revision for this document", 404)
                else:
                    pass
            document.set_file_revisions_data(fileinfo_db)
        return document

    def update_metadata_after_removal(self, document):
        # Doing nothing for mark deleted call
        mark_revision = False
        if 'mark_deleted' in document.options.iterkeys():
            return document
        revision = document.get_revision()
        if 'mark_revision_deleted' in document.options.iterkeys():
            mark_revision = document.options['mark_revision_deleted']
            revision = mark_revision
        if revision:
            directory = self.filesystem.get_or_create_document_directory(document)
            fileinfo_db, new_revision = self.load_metadata(document.get_code(), directory)
            if not mark_revision:
                del fileinfo_db[str(revision)]
            else:
                if mark_revision in fileinfo_db.iterkeys():
                    fileinfo_db[str(revision)]['deleted'] = True
                else:
                    raise PluginError('Revision not found', 404)
            self.write_metadata(fileinfo_db, document, directory)
            # Empty revisions data
            if not fileinfo_db:
                self.remove_metadata_file(directory, document)
        else:
            pass  # our directory with all file revision data has just been deleted %)
        return document

    def update(self, document):
        """Updates document file revision data after it has been updated, e.g. updated revision"""
        if 'update_file' in document.options:
            # FIXME file revision data should be updated more often if we plan to store secondary keys on a disk.
            directory = self.filesystem.get_or_create_document_directory(document)
            document = self.save_metadata(document, directory)
        if document.old_docrule:
            document = self.migrate_metadata_to_new_code(document)
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

    def convert_metadata_for_docrules(self, fileinfo_db, new_name):
        """Converts file file revision data into another docrule, changing it's file name everywhere"""
        revisions = {}
        for rev_key, revision in fileinfo_db.iteritems():
            old_file_name = revision['name']
            extension = old_file_name.split('.')[1]
            prefix = '_r%s.%s' % (rev_key, extension)
            changed_name = new_name + prefix
            revision['name'] = changed_name
            revisions[rev_key] = revision
        return revisions

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
        fileinfo_db, revision = self.load_metadata(document.get_code(), directory)
        document.set_revision(revision)

        fileinfo = {
            'name': document.get_filename_with_revision(),
            'revision': document.get_revision(),
            'created_date': self.date_to_string(datetime.today())
        }

        if document.get_current_file_revision_data():
            fileinfo.update(document.get_current_file_revision_data())

        fileinfo_db[document.get_revision()] = fileinfo

        self.write_metadata(fileinfo_db, document, directory)
        # Required for any update sequence
        document.set_file_revisions_data(fileinfo_db)
        return document

    def write_metadata(self, fileinfo_db, document, directory):
        json_file = os.path.join(directory, '%s.json' % (document.get_code(),))
        json_handler = open(json_file, mode='w')
        json.dump(fileinfo_db, json_handler, indent = 4)

    def get_fake_metadata(self, root, fil):
        current_date = datetime.strftime(datetime.now(), settings.DATETIME_FORMAT)
        created_date = datetime.strptime(current_date, settings.DATETIME_FORMAT)
        return {   'created_date': created_date,
                    'name': fil,
                    'revision': 'N/A'
                }

    def get_directories(self, docrule, filter_date = None):
        """
        Return List of directories with document files
        """
        #FIXME: seems to be rather slow for large number of docs :(
        root = settings.DOCUMENT_ROOT
        doccode_directory = os.path.join(root, docrule.get_directory_name())

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
                elif docrule.uncategorized and not dirs:  # leaf directory, no file revision data file => NoDocrule
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

    def get_metadatas(self, docrule):
        """
        Return List of directories with document files
        """
        root = settings.DOCUMENT_ROOT
        doccode_directory = os.path.join(root, docrule.get_directory_name())

        metadatas = []
        for root, dirs, files in os.walk(doccode_directory):
            for fil in files:
                doc, extension = os.path.splitext(fil)
                if extension == '.json':  # dirs with file revision data
                    metadatas.append(self.load_from_file(os.path.join(root, fil)))
        return metadatas

    def migrate_metadata_to_new_code(self, document):
        """Converts old file revision data fot use with new document Code (name) and/or for new DocTypeRule"""
        # Storing new document type file revision data here
        new_directory = self.filesystem.get_or_create_document_directory(document)
        new_name = document.get_filename()
        # Making new document OLD one for retrieving data purposes
        document.docrule = None
        document.set_filename(document.old_name_code)
        # Converting file revision data for new document name
        old_directory = self.filesystem.get_or_create_document_directory(document)
        fileinfo_db, new_revision = self.load_metadata(document.get_code(), old_directory)
        new_metadata = self.convert_metadata_for_docrules(fileinfo_db, new_name)
        # Moving document object back
        document.docrule = None
        document.set_filename(new_name)
        document.set_file_revisions_data(new_metadata)
        self.write_metadata(fileinfo_db, document, new_directory)
        self.filesystem.remove_file(os.path.join(old_directory, document.old_name_code + '.json'))
        return document

    def remove_metadata_file(self, directory, document):
        json_file = os.path.join(directory, '%s.json' % (document.get_code(),))
        self.filesystem.remove_file(json_file)

class LocalJSONMetadataRetrievalPlugin(Plugin, BeforeRetrievalPluginPoint):
    title = "Filesystem Metadata Retrieval"
    description = "Loads document file revision data as local file"

    plugin_type = 'metadata'
    worker = LocalJSONMetadata()

    def work(self, document, **kwargs):
        return self.worker.retrieve(document)


class LocalJSONMetadataStoragePlugin(Plugin, StoragePluginPoint):
    title = "Filesystem Metadata Storage"
    description = "Saves document file revision data as local file"

    plugin_type = 'metadata'
    worker = LocalJSONMetadata()

    def work(self, document, **kwargs):
        return self.worker.store(document)


class LocalJSONMetadataRemovalPlugin(Plugin, BeforeRemovalPluginPoint):
    title = "Filesystem Metadata Removal"
    description = "Updates document file revision data after removal of document (actualy some revisions of document)"

    plugin_type = 'metadata'
    worker = LocalJSONMetadata()

    def work(self, document, **kwargs):
        return self.worker.update_metadata_after_removal(document)


class LocalJSONMetadataUpdatePlugin(Plugin, UpdatePluginPoint):
    title = "Filesystem Metadata Update"
    description = "Updates document file revision data after modification of document revisions."

    plugin_type = 'metadata'
    worker = LocalJSONMetadata()

    def work(self, document, **kwargs):
        return self.worker.update(document)