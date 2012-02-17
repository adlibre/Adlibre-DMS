from django.db import models
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
        # setting document current revision metadata date, except not exist's using now() instead.
        try:
            revision = unicode(document.revision)
            self.metadata_created_date = document.metadata[revision][u'created_date']
        except: pass
        try:
            self.metadata_description = document.db_info["description"] or "" # not implemented yet
        except: pass
        self.tags = document.tags
        self.mdt_indexes = {} # not implemented yet
        self.search_keywords = [] # not implemented yet
        self.revisions = document.metadata

