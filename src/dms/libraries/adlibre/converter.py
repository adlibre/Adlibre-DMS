"""
Module: DMS File Type Converter Library
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

import os
from subprocess import Popen, PIPE
import mimetypes

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
            return [mimetypes.guess_type(self.filepath)[0], content]
        try:
            func = getattr(self, '%s_to_%s' % (extension_from, self.extension_to))
            return func()
        except AttributeError:
            return None


    def tif_to_pdf(self):
        """
        tiff to pdf conversion, use tiff2pdf command (libtiff)
        """
        path = '%s/%s.pdf' % (os.path.dirname(self.filepath), self.document)
        p = Popen('tiff2pdf -o %s %s' % (path, self.filepath), shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        content = open(path, 'rb').read()
        p = Popen('rm -rf %s' % path, shell=True,stdout=PIPE, stderr=PIPE)
        return ['application/pdf', content]


    def pdf_to_txt(self):
        """
        pdf to txt conversion, use pdftotext command (poppler)
        """
        path = '%s/%s.txt' % (os.path.dirname(self.filepath), self.document)
        p = Popen('pdftotext -enc Latin1 %s %s' % (self.filepath, path), shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        content = open(path, 'rb').read()
        p = Popen('rm -rf %s' % path, shell=True,stdout=PIPE, stderr=PIPE)
        return ['text/plain', content]


    def txt_to_pdf(self):
        """
        text to pdf conversion, use a2ps and ps2pdf  command (a2ps & ghostscript)
        """
        path = '%s/%s.pdf' % (os.path.dirname(self.filepath), self.document)
        p = Popen('a2ps --quiet --portrait --columns=1 --rows=1 -L 100 --no-header --borders=off -o - %s | ps2pdf -sPAPERSIZE=a4 - %s' % (self.filepath, path), shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        content = open(path, 'rb').read()
        p = Popen('rm -rf %s' % path, shell=True,stdout=PIPE, stderr=PIPE)
        return ['application/pdf', content]