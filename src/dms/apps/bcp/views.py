"""
Module: Barcode Printer Views
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

from django.http import HttpResponse
from django.http import HttpResponseBadRequest

from django.conf import settings

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


def generate(request, code, barcode_type='Standard39',):
    """
     Returns a PDF Barcode using ReportLab
    """

    import os

    from reportlab.graphics.shapes import String
    from reportlab.graphics import renderPDF
    from reportlab.graphics.barcode import createBarcodeDrawing
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'inline; filename=%s.pdf' % (code,)

    # Config
    font_size=8
    font = os.path.join(os.path.split(__file__)[0], 'fonts', 'OCRA.ttf',)
    try:
        bc = createBarcodeDrawing(barcode_type, value=code, checksum=False,)
    except KeyError, e:
        return HttpResponseBadRequest('Barcode Generation Failed: %s' % (e))

    # register the OCRA font
    pdfmetrics.registerFont(TTFont('OCRA', font))

    # position for our text
    x = bc.width/2
    y = bc.height-(font_size*1.2) # Hack: 1.2 is a fudge factor alignment
    # the textual barcode
    text = String(x,-y, code, textAnchor='middle', fontName='OCRA', fontSize=font_size)
    bc.add(text)
    bc = bc.resized() # resize barcode drawing object to accommodate text added
    buffer = StringIO() # buffer for the output
    renderPDF.drawToFile(bc,buffer,autoSize=1) # write PDF to buffer

    # Get the value of the StringIO buffer and write it to the response.
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)

    return response


def generate_elephe(request, code, barcode_type='code39',):
    """
     Returns a PDF Barcode.
     NB, Barcode generation with Elephe is somewhat unreliable. This code is kept here incase it is required in future
     otherwise we'll use the report lab method above
    """
    # NB FIXME: Same error? http://code.google.com/p/elaphe/issues/detail?id=9

    from elaphe import barcode

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