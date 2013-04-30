"""
Module: DMS Core HTTP objects module.

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
Desc: Main http objects manipulation methods here.
"""

import logging
import json

from django.http import HttpResponse
from django.core.urlresolvers import reverse

log = logging.getLogger('core.http')


class DMSObjectResponse(HttpResponse):
    """
    HttpResponse() object containing DMSObject()'s file.

    Response object to fake HttpResponse() in file requests from DMS.
    Usually used in DMS returning file object to browser after search.
    uses populated DMSObject() object to produce HttpResponse() with it populated.

    Init this object with DMSObject() instance provided.
    e.g. (django app's view):

        def read_file_from_dms(request, filename):
            document = DocumentProcessor().read(request, filename)
            response = DMSObjectResponse(document)
            return response
    """
    def __init__(self, document):
        content, mimetype, filename = self.retrieve_file(document)
        super(DMSObjectResponse, self).__init__(content=content, mimetype=mimetype)
        self["Content-Length"] = len(content)
        self["Content-Disposition"] = 'filename=%s' % filename

    def retrieve_file(self, document):
        # Getting file vars we need from Document()
        # FIXME: Document() instance should already contain properly set up file object.
        document.get_file_obj().seek(0)
        content = document.get_file_obj().read()
        mimetype = document.get_mimetype()
        # Renaming returned document in case we have certain revision request
        current_revision = document.get_revision()
        file_revision_data = document.get_file_revisions_data()
        revisions_count = file_revision_data.__len__()
        if current_revision < revisions_count:
            filename = document.get_filename_with_revision()
        else:
            filename = document.get_full_filename()
        return content, mimetype, filename


class DMSOBjectRevisionsData(dict):
    """Base object for DMS Object file data dict for HTTP responses"""

    def __init__(self, dms_object):
        """Forms dict() for HTTP file revisions output of DMS"""
        d = {}
        d['metadata'] = dms_object.get_file_revisions_data()
        d['current_metadata'] = dms_object.get_current_file_revision_data()
        obj_rule = dms_object.get_docrule()
        d['doccode'] = {'title': obj_rule.get_title(), 'id': obj_rule.get_id()}
        d['document_name'] = dms_object.get_filename()
        d['tags'] = dms_object.get_tags()
        obj_mapping = obj_rule.get_docrule_plugin_mappings()
        d['document_list_url'] = reverse('ui_document_list', kwargs={'id_rule': obj_mapping.pk})
        d['no_doccode'] = obj_rule.no_doccode
        self.data = d
        self.jsons = json.dumps(d, indent=4)
        super(DMSOBjectRevisionsData, self).__init__(data=self.data, jsons=self.jsons)

    def __repr__(self):
        return self.jsons

