"""
Module: DMS Core HTTP objects module.

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
"""

"""
Main http generation methods storage.
"""
import logging

from django.http import HttpResponse

log = logging.getLogger('core.http')

class DocumentResponse(HttpResponse):
    """
    HttpResponse() object containing DMS Document()'s file.

    Response object to fake HttpResponse() in file requests from DMS.
    Usually used in DMS returning file object to browser after search.
    uses populated Document() object to produce HttpResponse() with it populated.

    Init this object with Document() instance provided.
    e.g. (django app's view):

        def read_file_from_dms(request, filename):
            document = DocumentProcessor().read(request, filename)
            response = DocumentResponse(document)
            return response
    """
    def __init__(self, document):
        content, mimetype, filename = self.retrieve_file(document)
        super(DocumentResponse, self).__init__(content=content, mimetype=mimetype)
        self["Content-Length"] = len(content)
        self["Content-Disposition"] = 'filename=%s' % filename

    def retrieve_file(self, document):
        # Getting file vars we need from Document()

        # FIXME: Document() instance should already contain properly set up file object.
        document.get_file_obj().seek(0)
        content = document.get_file_obj().read()
        mimetype = document.get_mimetype()
        filename = document.get_full_filename()
        return content, mimetype, filename