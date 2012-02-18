"""
Module: DMS CocuhDB Plugin
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
"""

from dms_plugins.pluginpoints import BeforeRetrievalPluginPoint, BeforeRemovalPluginPoint, DatabaseStoragePluginPoint
from dms_plugins.models import Document as DocTags #needs refactoring of name
from dms_plugins.workers import Plugin, PluginError, BreakPluginChain
from document_manager import DocumentManager
from dmscouch.couchdocs_manager import CouchDocument


class CouchDBMetadata(object):
    """
        Stores metadata in CouchDB DatabaseManager.
        Handles required logic for metadata <==> Document(object) manipulations.
    """

    def store(self, request, document):
        # doing nothing for no doccode documents
        if document.get_docrule().no_doccode:
            return document
        # if not exists all required metadata getting them from doccode retrieve sequence
        if not document.metadata:
            manager = DocumentManager()
            document = manager.retrieve(request, document.file_name, only_metadata=True)
        # updating tags to sync with Django DB
        self.sync_document_tags(document)
        # assuming no document with this _id exists. SAVING
        couchdoc=CouchDocument()
        couchdoc.populate_from_dms(request, document)
        couchdoc.save(force_update=True)
        #print "Storing Document into DB", document
        return document

    def update_metadata_after_removal(self, request, document):
        """
        Updates document CouchDB metadata on removal. (Removes CocuhDB document)
        """
        if not document:
            #doc is fully deleted
            if request.method == 'DELETE':
                #precaution to only delete on delete not on 'PUT'
                doc_name = request.GET["filename"]
                couchdoc = CouchDocument.get(docid=doc_name)
                couchdoc.delete()
        #print "Deleted Document in DB", document

    def retrieve(self, request, document):
        # doing nothing for no doccode documents
        if document.get_docrule().no_doccode:
            return document
        doc_name = document.get_stripped_filename()
        couchdoc = CouchDocument.get(docid=doc_name)
        document = couchdoc.populate_into_dms(request, document)
        #print "Populating Document from DB", document
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
    title = "CocuhDB Metadata Retrieval"
    description = "Loads document metadata from CouchDB"

    plugin_type = 'database'
    worker = CouchDBMetadata()

    def work(self, request, document, **kwargs):
        return self.worker.retrieve(request, document)

class CouchDBMetadataStoragePlugin(Plugin, DatabaseStoragePluginPoint):
    title = "CouchDB Metadata Storage"
    description = "Saves document metadata CouchDB"

    plugin_type = 'database'
    worker = CouchDBMetadata()

    def work(self, request, document, **kwargs):
        return self.worker.store(request, document)

class CouchDBMetadataRemovalPlugin(Plugin, BeforeRemovalPluginPoint):
    title = "CouchDB Metadata Removal"
    description = "Updates document metadata after removal of document (or some revisions of document)"

    plugin_type = 'database'
    worker = CouchDBMetadata()

    def work(self, request, document, **kwargs):
        return self.worker.update_metadata_after_removal(request, document)
