"""
Module: Barcode Printer Views
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

from django.http import HttpResponse
from django.http import HttpResponseBadRequest
from django.core.urlresolvers import reverse
from django.shortcuts import render

from django.conf import settings

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


def print_barcode_embed_example(request, code, barcode_type, template='bcp/embed_example.html'):
    """
    This is a test page showing how you can embed a request to print a barcode
    """
    bcp_url = reverse('bcp-print', kwargs = {'barcode_type': barcode_type, 'code': code, })
    context = { 'bcp_url': bcp_url, }
    return render(request, template, context)


def print_barcode(request, code, barcode_type, template='bcp/print.html'):
    """
    This page causes the browser to request the barcode be printed
    """
    pdf_url = reverse('bcp-generate', kwargs = {'barcode_type': barcode_type, 'code': code, })
    context = { 'pdf_url': pdf_url, }
    return render(request, template, context)


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

    # TODO: Investigate embedding Javascript to force printing.
    #from reportlab.pdfbase.pdfdoc import PDFCatalog
    #PDFCatalog.__Defaults__['JavaScript'] = '<script type="text/javascript">print();</script>'
    # this.print({bUI: false, bSilent: true, bShrinkToFit: true});
    # http://livedocs.adobe.com/acrobat_sdk/9.1/Acrobat9_1_HTMLHelp/wwhelp/wwhimpl/common/html/wwhelp.htm?context=Acrobat9_HTMLHelp&file=JS_Dev_PrintProduction.75.4.html
    # http://stackoverflow.com/questions/687675/can-a-pdf-files-print-dialog-be-opened-with-javascript

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'inline; filename=%s.pdf' % (code,)

    # Config
    font_size = 10
    bar_height = 30
    font_path = os.path.join(os.path.split(__file__)[0], 'fonts', 'OCRA.ttf',)
    try:
        bc = createBarcodeDrawing(barcode_type, barHeight=bar_height, value=str(code), checksum=False,)
    except KeyError, e:
        return HttpResponseBadRequest('Barcode Generation Failed: %s' % (e))

    # Register the OCRA font
    pdfmetrics.registerFont(TTFont('OCRA', font_path))

    # Position for our text
    x = bc.width / 2
    y = - font_size  # or (bar_height + font_size) if placing on top
    # The textual barcode
    text = String(x, y, code, textAnchor='middle', fontName='OCRA', fontSize=font_size)
    bc.add(text)
    bc = bc.resized() # resize barcode drawing object to accommodate text added

    buffer = StringIO() # buffer for the output
    renderPDF.drawToFile(bc, buffer, autoSize=1) # write PDF to buffer

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
     TODO: Remove this code after we've decided it's not required
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