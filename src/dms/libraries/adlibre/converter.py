"""
Module: DMS File Type Converter Library
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

import os
from subprocess import Popen, PIPE
import mimetypes
import magic

# FIXME: All of these converters write their temp file into the repository! This is a bad idea.
# FIXME: These should work with a fileobject, not filepath!

class FileConverter:
    """
    Convert file from one mimetype to another mimetype
    """

    def __init__(self, file_obj, extension):
        self.file_obj = file_obj
        self.filepath = file_obj.name
        self.filename = os.path.basename(self.filepath)
        self.document = os.path.splitext(self.filename)[0]

        self.extension_to = extension

    def convert(self):
        document, extension = os.path.splitext(self.filename)
        extension_from = extension.strip(".")

        if self.extension_to is None or self.extension_to == extension_from:
            self.file_obj.seek(0)
            content = self.file_obj.read()
            self.file_obj.close()
            mime = magic.Magic( mime = True )
            mimetype = mime.from_buffer( content )
            return [mimetype, content]
        try:
            func = getattr(self, '%s_to_%s' % (extension_from, self.extension_to))
            return func()
        except AttributeError:
            return None


    def tif_to_pdf(self):
        """
        tiff to pdf conversion, use tiff2pdf command (libtiff)
        """
        path = os.path.join(os.path.dirname(self.filepath), self.document) + '.pdf'
        p = Popen('tiff2pdf -o %s %s' % (path, self.filepath), shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        content = open(path, 'rb').read()
        p = Popen('rm -rf %s' % path, shell=True,stdout=PIPE, stderr=PIPE)
        return ['application/pdf', content]


    def pdf_to_txt(self):
        """
        pdf to txt conversion, use pdftotext command (poppler)
        """
        #path = '%s/%s.txt' % (os.path.dirname(self.filepath), self.document)
        path = os.path.join(os.path.dirname(self.filepath), self.document) + '.txt'
        p = Popen('pdftotext -enc Latin1 %s %s' % (self.filepath, path), shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        content = open(path, 'rb').read()
        p = Popen('rm -rf %s' % path, shell=True,stdout=PIPE, stderr=PIPE)
        return ['text/plain', content]


    def txt_to_pdf(self):
        """
        text to pdf conversion, use a2ps and ps2pdf command (a2ps & ghostscript)
        """
        #path = '%s/%s.pdf' % (os.path.dirname(self.filepath), self.document)
        path = os.path.join(os.path.dirname(self.filepath), self.document) + '.pdf'
        p = Popen('a2ps --quiet --portrait --columns=1 --rows=1 -L 100 --no-header --borders=off -o - %s | ps2pdf -sPAPERSIZE=a4 - %s' % (self.filepath, path), shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        content = open(path, 'rb').read()
        p = Popen('rm -rf %s' % path, shell=True,stdout=PIPE, stderr=PIPE)
        return ['application/pdf', content]


class NewFileConverter(object):
    """
    Convert file from one mimetype to another mimetype
    """

    def __init__(self, file_obj, extension):
        self.file_obj = file_obj
        self.filepath = file_obj.name
        self.filename = os.path.basename(self.filepath)
        self.document = os.path.splitext(self.filename)[0]

        self.extension_to = extension

    def convert(self):
        document, extension = os.path.splitext(self.filename)
        extension_from = extension.strip(".")

        if self.extension_to is None or self.extension_to == extension_from:
            self.file_obj.seek(0)
            content = self.file_obj.read()
            self.file_obj.close()
            mime = magic.Magic( mime = True )
            mimetype = mime.from_buffer( content )
            return [mimetype, self.file_obj]
        try:
            print "from: %s, to: %s" % (extension_from, self.extension_to)
            func = getattr(self, '%s_to_%s' % (extension_from, self.extension_to))
            return func()
        except AttributeError:
            return (None, None)

    def do_convert(self, command):
        import tempfile
        tempfile = tempfile.NamedTemporaryFile()
        p = Popen(command % {'to': tempfile.name, 'from': self.filepath}, shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        return tempfile

    def tif_to_pdf(self):
        """
        tiff to pdf conversion, use tiff2pdf command (libtiff)
        """
        file_obj = self.do_convert('tiff2pdf -o %(to)s %(from)s')
        return ['application/pdf', file_obj]


    def pdf_to_txt(self):
        """
        pdf to txt conversion, use pdftotext command (poppler)
        """
        file_obj = self.do_convert('pdftotext -enc Latin1 %(from)s %(to)s')
        return ['text/plain', file_obj]


    def txt_to_pdf(self):
        """
        text to pdf conversion, use a2ps and ps2pdf command (a2ps & ghostscript)
        """
        file_obj = self.do_convert('a2ps --quiet --portrait --columns=1 --rows=1 -L 100 --no-header --borders=off -o - %(from)s | ps2pdf -sPAPERSIZE=a4 - %(to)s')
        return ['application/pdf', file_obj]

