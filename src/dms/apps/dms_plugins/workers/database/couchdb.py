import datetime
import json
import os

from django.conf import settings

from dms_plugins.pluginpoints import BeforeRetrievalPluginPoint, BeforeRemovalPluginPoint, DatabaseStoragePluginPoint
from dms_plugins.workers import Plugin, PluginError, BreakPluginChain
from document_manager import DocumentManager


from datetime import datetime
from django.db import models

from couchdbkit.ext.django.schema import *

class CouchDocument(Document):
    id = StringProperty()
    metadata_doc_type_rule_id = StringProperty(default="")
    metadata_user_id = StringProperty(default="")
    metadata_user_name = StringProperty(default="")
    metadata_created_date = DateTimeProperty(default=datetime.utcnow)
    metadata_description = StringProperty(default="")
    tags = ListProperty(default=[])
    mdt_indexes = DictProperty(default={})
    search_keywords = ListProperty(default=[])
    revisions = DictProperty(default={})

    class Meta:
        app_label = "dmscouch"

    def populate_from_dms(self, request, document):
        self.id = document.file_name
        self.metadata_doc_type_rule_id = str(document.doccode.doccode_id)
        self.metadata_user_id = str(request.user.pk)
        if request.user.first_name:
            self.metadata_user_name = request.user.first_name + u'' + request.user.last_name
        else:
            self.metadata_user_name = request.user.username
        #self.metadata_created_date = document.metadata[document.revision]["created_date"]
        #self.metadata_description = document.db_info["description"] or "" # not implemented yet
        self.tags = document.tags
        self.mdt_indexes = {} # not implemented yet
        self.search_keywords = [] # not implemented yet
        self.revisions = document.metadata

class CouchDBMetadata(object):
    """
        Stores metadata in CouchDB DatabaseManager.
        Handles required logic for metadata <> Document(object) manipulations.
    """
#    def __init__(self):
#        self.database = DatabaseManager()

    def store(self, request, document):
        # doing nothing for no doccode documents
        if document.get_docrule().no_doccode:
            return document
        # if not exists all required metadata getting them from doccode retrieve sequence
        if not document.metadata:
            manager = DocumentManager()
            document = manager.retrieve(request, document.file_name, only_metadata=True)
        # assuming no document exists
        couchdoc=CouchDocument()
        couchdoc.populate_from_dms(request, document)
        couchdoc.save()
        print "Setoring Document into DB", document
        return document

    def update_metadata_after_removal(self, request, document):
        print "Deleting Document in DB", document

    def retrieve(self, request, document):
        print "Getting Document from DB", document
        return document


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
