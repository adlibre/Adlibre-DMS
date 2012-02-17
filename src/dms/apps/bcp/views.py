"""
Module: Barcode Printer Views
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

# NB FIXME: Same error? http://code.google.com/p/elaphe/issues/detail?id=9

from elaphe import barcode

from django.http import HttpResponse
from django.http import Http404, HttpResponseBadRequest

from django.conf import settings

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


def generate(request, barcode_type, code):
    """
     Returns a PDF Barcode
    """
    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'inline; filename=%s.pdf' % (code,)

    try:
        bc = barcode(barcode_type, str(code), options=dict(includetext=True), scale=4, margin=1)
    except ValueError, e:
        return HttpResponseBadRequest('Barcode Generation Failed: %s' % (e))
    buffer = StringIO()
    try:
        bc.save(buffer, 'pdf')
    except IOError, e:
        if settings.DEBUG:
            raise
        else:
            return HttpResponseBadRequest('Barcode Generation Failed: %s' % (e))

    # Get the value of the StringIO buffer and write it to the response.
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response

