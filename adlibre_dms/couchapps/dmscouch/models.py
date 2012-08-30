"""
Module: DMS CouchDB Documents manager
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

from datetime import datetime
from django.conf import settings
from couchdbkit.ext.django.schema import *
from adlibre.date_converter import str_date_to_couch

class CouchDocument(Document):
    id = StringProperty()
    metadata_doc_type_rule_id = StringProperty(default="")
    metadata_user_id = StringProperty(default="")
    metadata_user_name = StringProperty(default="")
    metadata_created_date = DateTimeProperty(default=datetime.utcnow()) # Should fix #731 Andrew check!
    metadata_description = StringProperty(default="")
    tags = ListProperty(default=[])
    mdt_indexes = DictProperty(default={})
    search_keywords = ListProperty(default=[])
    revisions = DictProperty(default={})
    index_revisions = DictProperty(default={})

    class Meta:
        app_label = "dmscouch"

    def populate_from_dms(self, request, document):
        """Populates CouchDB Document fields from DMS Document object."""
        # Setting document ID, based on filename. Using stripped (pure doccode regex readable) filename if possible.
        # TODO: to save no_docrule documents properly we need to generate metadata.
        if document.get_stripped_filename():
            self.id = document.get_stripped_filename()
            self._doc['_id']=self.id
        self.metadata_doc_type_rule_id = str(document.doccode.pk)
        # Trying to set provided user name/id
        try:
            self.metadata_user_name = document.db_info["metadata_user_name"]
            self.metadata_user_id = document.db_info["metadata_user_id"]
        except KeyError:
            # user name/id from Django user
            self.metadata_user_id = str(request.user.pk)
            if request.user.first_name:
                self.metadata_user_name = request.user.first_name + u' ' + request.user.last_name
            else:
                self.metadata_user_name = request.user.username
        self.set_doc_date(document)
        # adding description if exists
        try:
            self.metadata_description = document.db_info["description"]
        except KeyError:
            self.metadata_description = ""
            pass
        self.tags = document.tags
        # populating secondary indexes
        if document.db_info:
            try:
                db_info = document.db_info
                # trying to cleanup date and description if exist...
                try:
                    del db_info["date"]
                except: pass
                try:
                    del db_info["description"]
                except: pass
                self.mdt_indexes = db_info
                # failing gracefully due to ability to save files with API (without metadata)
            except: pass
        self.search_keywords = [] # TODO: not implemented yet
        self.revisions = document.metadata
        if document.index_revisions:
            self.index_revisions = document.index_revisions

    def populate_into_dms(self, request, document):
        """
        Updates DMS Document object with CouchDB fields data.
        """
        document.metadata = self.revisions
        document.tags = self.tags
        document.stripped_filename = self.id
        document.db_info = self.construct_db_info()
        if 'index_revisions' in self:
            document.index_revisions = self.index_revisions
        return document

    def construct_db_info(self, db_info = None):
        """Method to populate additional database info from CouchDB into DMS Document object."""
        if not db_info:
            db_info={}
        db_info["description"] = self.metadata_description
        db_info["tags"] = self.tags
        db_info["metadata_doc_type_rule_id"] = self.metadata_doc_type_rule_id
        db_info["metadata_user_id"] = self.metadata_user_id
        db_info["metadata_user_name"] = self.metadata_user_name
        db_info["metadata_created_date"] = self.metadata_created_date
        db_info["mdt_indexes"] = self.mdt_indexes
        return db_info

    def construct_index_revision_dict(self):
        """Constructs current indexes revision and export into result dict"""
        current_index_data = {
            'metadata_created_date':   self.metadata_created_date,
            'metadata_description':    self.metadata_description,
            'metadata_user_id':        self.metadata_user_id,
            'metadata_user_name':      self.metadata_user_name,
            'mdt_indexes':    self.mdt_indexes,
            }
        return current_index_data

    def set_doc_date(self, document):
        """Unifies DB storage of date object received from document."""
        # TODO: Standardize DATE parsing here!!!
        doc_date = None
        # trying to get date from db_info dict first
        try:
            doc_date = datetime.strptime(str(document.db_info["date"]), settings.DATE_FORMAT)
        except Exception:
            pass
        if doc_date:
            self.metadata_created_date = doc_date
        else:
            # Setting document current revision metadata date, except not exists using now() instead.
            try:
                revision = unicode(document.revision)
                self.metadata_created_date = datetime.strptime(document.metadata[revision][u'created_date'], "%Y-%m-%d %H:%M:%S")
            except KeyError:
                # Model stores default "utcnow" date farther
                pass

    def update_indexes_revision(self, document):
        """Updates CouchDB document with new revision of indexing data.

        Old indexing data is stored in revision. E.g.:
        Document only created:

            couchdoc.index_revisions = None

        Document updated once:

            couchdoc.index_revisions = { '1': { ... }, }

        Document updated again and farther:

            couchdoc.index_revisions = {
                '1': { ... },
                '2': { ... },
                ...
            }

        This method handles storing of indexing data changes (old one's) are stored into revisions.
        New data are populated into couchdoc thus making them current.
        """
        if document.new_indexes:
            # Creating clean self.mdt_indexes
            secondary_indexes = {}
            for secondary_index_name, secondary_index_value in document.new_indexes.iteritems():
                if not secondary_index_name in ['description', 'metadata_user_name', 'metadata_user_id',]:
                    # Converting date format to couch if secondary index is DMS date type
                    try:
                        datetime.strptime(secondary_index_value, settings.DATE_FORMAT)
                        secondary_indexes[secondary_index_name] = str_date_to_couch(secondary_index_value)
                    except ValueError:
                        secondary_indexes[secondary_index_name] = secondary_index_value
                        pass
            # Storing current index data into new revision
            if not 'index_revisions' in self:
                # Creating index_revisions initial data dictionary.
                self.index_revisions = { '1': self.construct_index_revision_dict(), }
            else:
                # Appending new document indexes revision to revisions dict
                new_revision = self.index_revisions.__len__() + 1
                self.index_revisions[new_revision] = self.construct_index_revision_dict()
            # Populating self with new provided data
            self.mdt_indexes = secondary_indexes
            self.metadata_description = document.new_indexes['description']
            self.metadata_user_id = document.new_indexes['metadata_user_id']
            self.metadata_user_name = document.new_indexes['metadata_user_name']
        return document
