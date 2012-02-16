"""
Module: Barcode Printer Views
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

from django.http import HttpResponse
from django.http import Http404, HttpResponseBadRequest

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
        # dynamically load the barcode type module, or raise 404
        exec('from elaphe.upc import %s as barcode' % barcode_type)
    except ImportError:
        raise Http404

    bc = barcode()

    bc_image = bc.render(str(code), options=dict(includetext=True), scale=4, margin=1)
    buffer = StringIO()
    try:
        bc_image.save(buffer, 'pdf')
    except IOError:
        return HttpResponseBadRequest('Barcode Generation Failed')

    # Get the value of the StringIO buffer and write it to the response.
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response

