"""
Module: DMS CocuhDB Documents manager
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

from datetime import datetime
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
        """
        Populates CocuhDB Document fields from DMS Document object.
        """
        # setting document ID, based on filename. Using stripped (pure doccode regex readable) filename if possible.
        # TODO: to save no_docrule documents properly we need to generate metadata.
        if document.get_stripped_filename():
            self.id = document.get_stripped_filename()
            self._doc['_id']=self.id
        self.metadata_doc_type_rule_id = str(document.doccode.doccode_id)
        # user name/id from Django user
        self.metadata_user_id = str(request.user.pk)
        if request.user.first_name:
            self.metadata_user_name = request.user.first_name + u'' + request.user.last_name
        else:
            self.metadata_user_name = request.user.username
        self.set_doc_date(document)
        # adding description if exists
        try:
            self.metadata_description = document.db_info["description"]
        except:
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

    def populate_into_dms(self, request, document):
        """
        Updates DMS Document object with CouchDB fields data.
        """
        document.metadata = self.revisions
        document.tags = self.tags
        document.stripped_filename = self.id
        document.db_info = self.construct_db_info()
        return document

    def construct_db_info(self, db_info = None):
        """
        Method to populate additional database info from CouchDB into DMS Document object.
        """
        if not db_info:
            db_info={}
        db_info["description"] = self.metadata_description
        db_info["tags"] = self.tags
        db_info["metadata_doc_type_rule_id"] = self.metadata_doc_type_rule_id
        # TODO: not implemented and needed for exposure till implementation of Permissions/Ldap plugin.
        #db_info["metadata_user_id"] = self.metadata_user_id
        db_info["metadata_user_name"] = self.metadata_user_name
        db_info["metadata_created_date"] = self.metadata_created_date
        db_info["mdt_indexes"] = self.mdt_indexes
        return db_info

    def set_doc_date(self, document):
        """
        Unifies DB storage of date object received from document.
        """
        # TODO: Standartize DATE parsign here!!!
        doc_date = None
        # trying to get date from db_info dict first
        try:
            doc_date = datetime.strptime(str(document.db_info["date"]), "%Y-%m-%d")
        except Exception:
            pass
        if doc_date:
            self.metadata_created_date = doc_date
        else:
            # setting document current revision metadata date, except not exist's using now() instead.
            try:
                revision = unicode(document.revision)
                self.metadata_created_date = document.metadata[revision][u'created_date']
            except Exception:
                # if not provided model stores default "utcnow" date
                pass
