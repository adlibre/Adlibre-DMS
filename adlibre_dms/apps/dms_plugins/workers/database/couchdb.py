"""
Module: DMS CouchDB Plugin
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import datetime

from django.conf import settings

from dms_plugins.pluginpoints import BeforeRetrievalPluginPoint, BeforeRemovalPluginPoint, BeforeUpdatePluginPoint, DatabaseStoragePluginPoint
from dms_plugins.models import DocTags
from dms_plugins.workers import Plugin
from core.document_processor import DocumentProcessor
from dmscouch.models import CouchDocument

from couchdbkit.resource import ResourceNotFound

class CouchDBMetadata(object):
    """
        Stores metadata in CouchDB DatabaseManager.
        Handles required logic for metadata <==> Document(object) manipulations.
    """

    def store(self, user, document):
        """
        Stores CouchDB object into DB.

        (Updates or overwrites CouchDB document)
        """
        docrule = document.get_docrule()
        # doing nothing for no doccode documents
        if docrule.no_doccode:
            return document
        else:
            processor = DocumentProcessor()
            # FIXME: there might be more than one mapping
            mapping = docrule.get_docrule_plugin_mappings()
            # doing nothing for documents without mapping has DB plugins
            if not mapping.get_database_storage_plugins():
                return document
            else:
                # if not exists all required metadata getting them from doccode retrieve sequence
                if not document.metadata:
                    # HACK: Preserving db_info here... (May be Solution!!!)
                    db_info = document.get_db_info()
                    document = processor.read(user, document.file_name, options={'only_metadata':True,})

                    # HACK: saving NEW metadata ONLY if they exist in new uploaded doc (Preserving old indexes)'
                    if db_info:
                        # Storing new indexes
                        document.set_db_info(db_info)
                    else:
                        # TODO: move this code into a proper place (UPDATE method)
                        # Asking couchdb about if old metadata exists and updating them properly
                        current_revisions = document.metadata
                        try:
                            # Only if document exists in DB. Falling gracefully if not.
                            temp_doc = self.retrieve(user, document)
                            old_metadata = temp_doc.get_db_info()
                            old_index_revisions = None
                            if old_metadata['mdt_indexes']:
                                # Preserving Description, User, Created Date, indexes revisions
                                if temp_doc.index_revisions:
                                    old_index_revisions = temp_doc.index_revisions
                                old_metadata['mdt_indexes']['description'] = old_metadata['description']
                                old_metadata['mdt_indexes']['metadata_user_name'] = old_metadata['metadata_user_name']
                                old_metadata['mdt_indexes']['metadata_user_id'] = old_metadata['metadata_user_id']
                                old_cr_date = datetime.datetime.strftime(old_metadata['metadata_created_date'], settings.DATE_FORMAT)
                                old_metadata['mdt_indexes']['date'] = old_cr_date
                                document.set_db_info(old_metadata['mdt_indexes'])
                                document.set_index_revisions(old_index_revisions)
                                document.set_metadata(current_revisions)
                            else:
                                # Preserving set revisions anyway.
                                document.set_metadata(current_revisions)
                        except ResourceNotFound:
                            pass
                # updating tags to sync with Django DB
                self.sync_document_tags(document)
                # assuming no document with this _id exists. SAVING or overwriting existing
                couchdoc=CouchDocument()

                couchdoc.populate_from_dms(user, document)
                couchdoc.save(force_update=True)
                return document

    def update_document_metadata(self, user, document):
        """
        Updates document with new indexes and stores old one into another revision.
        """
        if document.new_indexes and document.file_name:
            couchdoc = CouchDocument.get(docid=document.file_name)
            couchdoc.update_indexes_revision(document)
            couchdoc.save()
            document = couchdoc.populate_into_dms(user, document)
        return document

    def update_metadata_after_removal(self, user, document):
        """
        Updates document CouchDB metadata on removal.

        (Removes CouchDB document)
        """
        if not document.get_file_obj():
            #doc is fully deleted from fs
            stripped_filename=document.get_stripped_filename()
            couchdoc = CouchDocument.get(docid=stripped_filename)
            couchdoc.delete()
        return document

    def retrieve(self, user, document):
        docrule = document.get_docrule()
        mapping = docrule.get_docrule_plugin_mappings()
        # No actions for no doccode documents
        # No actions for documents without 'mapping has DB plugins'
        if document.get_docrule().no_doccode:
            return document
        else:
            if not mapping.get_database_storage_plugins():
                return document
            else:
                doc_name = document.get_stripped_filename()
                couchdoc = CouchDocument.get(docid=doc_name)
                document = couchdoc.populate_into_dms(user, document)
                return document

    """
    Helper managers:
    """
    def sync_document_tags(self, document):
        if not document.tags:
            tags = []
            try:
                doc_model = DocTags.objects.get(name = document.get_stripped_filename())
                tags = doc_model.get_tag_list()
            except DocTags.DoesNotExist:
                pass
            document.set_tags(tags)
        return document.tags

class CouchDBMetadataRetrievalPlugin(Plugin, BeforeRetrievalPluginPoint):
    title = "CouchDB Metadata Retrieval"
    description = "Loads document metadata from CouchDB"

    plugin_type = 'database'
    worker = CouchDBMetadata()

    def work(self, user, document, **kwargs):
        return self.worker.retrieve(user, document)

class CouchDBMetadataStoragePlugin(Plugin, DatabaseStoragePluginPoint):
    title = "CouchDB Metadata Storage"
    description = "Saves document metadata CouchDB"

    plugin_type = 'database'
    worker = CouchDBMetadata()

    def work(self, user, document, **kwargs):
        return self.worker.store(user, document)

class CouchDBMetadataUpdatePlugin(Plugin, BeforeUpdatePluginPoint):
    title = "CouchDB Metadata Update Indexes"
    description = "Updates document after new indexes added with preserving old revision of document indexes"

    plugin_type = 'database'
    worker = CouchDBMetadata()

    def work(self, user, document, **kwargs):
        return self.worker.update_document_metadata(user, document)

class CouchDBMetadataRemovalPlugin(Plugin, BeforeRemovalPluginPoint):
    title = "CouchDB Metadata Removal"
    description = "Updates document metadata after removal of document (or some revisions of document)"

    plugin_type = 'database'
    worker = CouchDBMetadata()

    def work(self, user, document, **kwargs):
        return self.worker.update_metadata_after_removal(user, document)
