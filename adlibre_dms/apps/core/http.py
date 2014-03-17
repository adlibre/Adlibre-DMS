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
import traceback
import sys
from wsgiref.handlers import format_date_time
from datetime import datetime, timedelta
from time import mktime

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
    def __init__(self, document, thumbnail=False):
        if thumbnail:
            content, content_type, filename = self.retieve_thumbnail(document)
        else:
            content, content_type, filename = self.retrieve_file(document)
        super(DMSObjectResponse, self).__init__(content=content, content_type=content_type)
        if content is not None:
            self["Content-Length"] = len(content)
            if thumbnail:
                self["Content-Type"] = content_type
                # Cache thumbnails for 1 day
                now = datetime.now()
                exp = now + timedelta(days=1)
                stamp = mktime(exp.timetuple())
                expires = format_date_time(stamp)
                self['Expires'] = expires
            self["Content-Disposition"] = 'filename=%s' % filename

    def retrieve_file(self, document):
        # Getting file vars we need from Document()
        # FIXME: Document() instance should already contain properly set up file object.
        document.get_file_obj().seek(0)
        content = document.get_file_obj().read()
        content_type = document.get_mimetype()
        # Renaming returned document in case we have certain revision request
        current_revision = document.get_revision()
        file_revision_data = document.get_file_revisions_data()
        revisions_count = file_revision_data.__len__()
        if current_revision < revisions_count:
            filename = document.get_filename_with_revision()
        else:
            filename = document.get_full_filename()
        return content, content_type, filename

    def retieve_thumbnail(self, document):
        # Getting thumbnail details
        content = document.thumbnail
        content_type = 'image/png'
        filename = document.get_full_filename() + '.png'
        return content, content_type, filename

    def httpdate(self, dt):
        """Return a string representation of a date according to RFC 1123
        (HTTP/1.1).

        The supplied date must be in UTC.

        """
        weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
        month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
                 "Oct", "Nov", "Dec"][dt.month - 1]
        return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (weekday, dt.day, month,
            dt.year, dt.hour, dt.minute, dt.second)


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
        d['uncategorized'] = obj_rule.uncategorized
        self.data = d
        self.jsons = json.dumps(d, indent=4)
        super(DMSOBjectRevisionsData, self).__init__(data=self.data, jsons=self.jsons)

    def __repr__(self):
        return self.jsons

