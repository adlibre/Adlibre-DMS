"""
Module: DMS CouchDB Plugin
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
Author: Iurii Garmash
"""

import datetime

from django.conf import settings

from dms_plugins.pluginpoints import BeforeRetrievalPluginPoint
from dms_plugins.pluginpoints import BeforeRemovalPluginPoint
from dms_plugins.pluginpoints import DatabaseUpdatePluginPoint
from dms_plugins.pluginpoints import DatabaseStoragePluginPoint
from core.models import DocTags
from dms_plugins.workers import Plugin, PluginError
from core.document_processor import DocumentProcessor
from dmscouch.models import CouchDocument

from couchdbkit.resource import ResourceNotFound


class CouchDBMetadataWorker(object):
    """Stores metadata in CouchDB DatabaseManager.

    Handles required logic for metadata <==> Document(object) manipulations.
    """

    def store(self, document):
        """Stores CouchDB object into DB.

        (Updates or overwrites CouchDB document)

        @param document: is a DMS Document() instance
        """
        # FIXME: Refactor me. We should upload new "secondary_indexes" or metatags with update() workflow,
        # not a create(), like it is now. Because this method is a mess.
        docrule = document.get_docrule()
        # doing nothing for no docrule documents
        if docrule.uncategorized:
            return document
        else:
            user = self.check_user(document)
            processor = DocumentProcessor()
            # FIXME: there might be more than one mapping
            mapping = docrule.get_docrule_plugin_mappings()
            # doing nothing for documents without mapping has DB plugins
            if not mapping.get_database_storage_plugins():
                return document
            else:
                # if not exists all required metadata getting them from docrule retrieve sequence
                if not document.file_revision_data:
                    # HACK: Preserving db_info here... (May be Solution!!!)
                    db_info = document.get_db_info()
                    document = processor.read(document.file_name, options={
                        'only_metadata': True,
                        'user': document.user
                    })

                    # saving NEW file_revision_data ONLY if they exist in new uploaded doc (Preserving old indexes)
                    if db_info:
                        # Storing new indexes
                        document.set_db_info(db_info)
                    else:
                        # TODO: move this code into a proper place (UPDATE method)
                        # Asking couchdb about if old file_revision_data exists and updating them properly
                        current_revisions = document.file_revision_data
                        try:
                            # Only if document exists in DB. Falling gracefully if not.
                            temp_doc = self.retrieve(document)
                            old_metadata = temp_doc.get_db_info()
                            old_index_revisions = None
                            if old_metadata['mdt_indexes']:
                                # Preserving Description, User, Created Date, indexes revisions
                                if temp_doc.index_revisions:
                                    old_index_revisions = temp_doc.index_revisions
                                old_metadata['mdt_indexes']['description'] = old_metadata['description']
                                old_metadata['mdt_indexes']['metadata_user_name'] = old_metadata['metadata_user_name']
                                old_metadata['mdt_indexes']['metadata_user_id'] = old_metadata['metadata_user_id']
                                old_cr_date = datetime.datetime.strftime(
                                    old_metadata['metadata_created_date'],
                                    settings.DATE_FORMAT
                                )
                                old_metadata['mdt_indexes']['date'] = old_cr_date
                                document.set_db_info(old_metadata['mdt_indexes'])
                                document.set_index_revisions(old_index_revisions)
                                document.set_file_revisions_data(current_revisions)
                            else:
                                # Preserving set revisions anyway.
                                document.set_file_revisions_data(current_revisions)
                        except ResourceNotFound:
                            pass
                # updating tags to sync with Django DB
                self.sync_document_tags(document)
                # assuming no document with this _id exists. SAVING or overwriting existing
                couchdoc = CouchDocument()

                couchdoc.populate_from_dms(user, document)
                couchdoc.save(force_update=True)
                return document

    def update_document_metadata(self, document):
        """Updates document with new indexes and stores old one into another revision.

        @param document: is a DMS Document() instance
        """
        self.check_user(document)
        if 'update_file' in document.options and document.options['update_file']:
            name = document.get_code()
            # We need to create couchdb document in case it does not exists in database.
            couchdoc = CouchDocument.get_or_create(docid=name)
            couchdoc.update_file_revisions_metadata(document)
            couchdoc.save()
        if document.old_docrule:
            couchdoc = CouchDocument.get_or_create(docid=document.file_name)
            old_couchdoc = CouchDocument.get(docid=document.old_name_code)
            couchdoc.migrate_metadata_for_docrule(document, old_couchdoc)
            couchdoc.save()
            old_couchdoc.delete()
        # We have to do it after moving document names.
        if document.new_indexes and document.file_name:
            couchdoc = CouchDocument.get(docid=document.file_name)
            couchdoc.update_indexes_revision(document)
            couchdoc.save()
            document = couchdoc.populate_into_dms(document)
        return document

    def remove(self, document):
        """Updates document CouchDB metadata on removal.

        (Removes CouchDB document or acts as prescribed in removal workflows)
        @param document: is a DMS Document() instance
        """
        # Doing nothing for mark deleted call
        code = document.get_code()
        couchdoc = CouchDocument.get(docid=code)
        if 'mark_deleted' in document.options.iterkeys():
            couchdoc['deleted'] = 'deleted'
            couchdoc.save()
            return document
        if 'mark_revision_deleted' in document.options.iterkeys():
            mark_revision = document.options['mark_revision_deleted']
            if mark_revision in couchdoc.revisions.iterkeys():
                couchdoc.revisions[mark_revision]['deleted'] = True
            else:
                raise PluginError('Object has no revision: %s' % mark_revision, 404)
            couchdoc.save()
            return document
        if 'delete_revision' in document.options.iterkeys():
            revision = document.options['delete_revision']
            del couchdoc.revisions[revision]
            couchdoc.save()
            return document
        if not document.get_file_obj():
            #doc is fully deleted from fs
            couchdoc.delete()
        return document

    def retrieve(self, document):
        """Read document CouchDB metadata.

        @param document: is a DMS Document() instance
        """
        docrule = document.get_docrule()
        mapping = docrule.get_docrule_plugin_mappings()
        # No actions for no docrule documents
        # No actions for documents without 'mapping has DB plugins'
        if document.get_docrule().uncategorized:
            return document
        else:
            if not mapping.get_database_storage_plugins():
                return document
            else:
                self.check_user(document)
                doc_name = document.get_code()
                couchdoc = CouchDocument()
                try:
                    couchdoc = CouchDocument.get(docid=doc_name)
                except Exception, e:
                    # Skip deleted errors (they are not used in DMS)
                    e_message = str(e)
                    if not e_message in ['deleted', 'missing']:
                        raise PluginError('CouchDB error: %s' % e, e)
                    pass
                document = couchdoc.populate_into_dms(document)
                return document

    ####################################################################################################################
    #############################################   Helper managers: ###################################################
    ####################################################################################################################
    def sync_document_tags(self, document):
        """Synchronise document's SQL tags between couchDB and SQL DB

        @param document: is a DMS Document() instance
        """
        if not document.tags:
            tags = []
            try:
                doc_model = DocTags.objects.get(name=document.get_code())
                tags = doc_model.get_tag_list()
            except DocTags.DoesNotExist:
                pass
            document.set_tags(tags)
        return document.tags

    def check_user(self, document):
        """Every call of this plugin should have a valid Django User() instance

        @param document: is a DMS Document() instance
        """
        user = document.user
        if not user:
            raise PluginError("Not a logged in user.", 403)
        return user


class CouchDBMetadataRetrievalPlugin(Plugin, BeforeRetrievalPluginPoint):
    title = "CouchDB Metadata Retrieval"
    description = "Loads document metadata from CouchDB"

    plugin_type = 'database'
    worker = CouchDBMetadataWorker()

    def work(self, document):
        """Main plugin method

        @param document: is a DMS Document() instance"""
        return self.worker.retrieve(document)


class CouchDBMetadataStoragePlugin(Plugin, DatabaseStoragePluginPoint):
    title = "CouchDB Metadata Storage"
    description = "Saves document metadata CouchDB"

    plugin_type = 'database'
    worker = CouchDBMetadataWorker()

    def work(self, document):
        """Main plugin method

        @param document: is a DMS Document() instance"""
        return self.worker.store(document)


class CouchDBMetadataUpdatePlugin(Plugin, DatabaseUpdatePluginPoint):
    title = "CouchDB Metadata Update Indexes"
    description = "Updates document after new indexes added with preserving old revision of document indexes"

    plugin_type = 'database'
    worker = CouchDBMetadataWorker()

    def work(self, document):
        """Main plugin method

        @param document: is a DMS Document() instance"""
        return self.worker.update_document_metadata(document)


class CouchDBMetadataRemovalPlugin(Plugin, BeforeRemovalPluginPoint):
    title = "CouchDB Metadata Removal"
    description = "Updates document metadata after removal of document (or some revisions of document)"

    plugin_type = 'database'
    worker = CouchDBMetadataWorker()

    def work(self, document):
        """Main plugin method

        @param document: is a DMS Document() instance"""
        return self.worker.remove(document)
