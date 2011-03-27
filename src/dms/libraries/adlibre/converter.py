import os
from subprocess import Popen, PIPE
import mimetypes


class FileConverter:
    """
    Convert file from one mimetype to another mimetype
    """

    def __init__(self, filepath, extension):
        self.filepath = filepath
        self.extension_to = extension


    def convert(self):
        filename = os.path.basename(self.filepath)
        document, extension = os.path.splitext(filename)
        extension_from = extension.strip(".")

        if self.extension_to is None or self.extension_to == extension_from:
            content = open(self.filepath, 'rb').read()
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

        filename = os.path.basename(self.filepath)
        document = os.path.splitext(filename)[0]
        path = '%s/%s.pdf' % (os.path.dirname(self.filepath), document)
        p = Popen('tiff2pdf %s -o %s' % (self.filepath, path), shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        content = open(path, 'rb').read()
        p = Popen('rm -rf %s' % path, shell=True,stdout=PIPE, stderr=PIPE)
        return ['application/pdf', content]


    def pdf_to_txt(self):
        """
        pdf to txt conversion, use pdftotext command (poppler)
        """

        filename = os.path.basename(self.filepath)
        document = os.path.splitext(filename)[0]
        path = '%s/%s.txt' % (os.path.dirname(self.filepath), document)
        p = Popen('pdftotext -enc Latin1 %s %s' % (self.filepath, path), shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        content = open(path, 'rb').read()
        p = Popen('rm -rf %s' % path, shell=True,stdout=PIPE, stderr=PIPE)
        return ['text/plain', content]


    def txt_to_pdf(self):
        """
        text to pdf conversion, use a2ps and ps2pdf command (a2ps & ghostscript)
        """

        filename = os.path.basename(self.filepath)
        document = os.path.splitext(filename)[0]
        path = '%s/%s.pdf' % (os.path.dirname(self.filepath), document) #output
        p = Popen('a2ps --quiet --portrait --columns=1 --rows=1 -L 100 --no-header --borders=off -o - %s | ps2pdf -sPAPERSIZE=a4 - %s' % (self.filepath, path), shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        content = open(path, 'rb').read()
        p = Popen('rm -rf %s' % path, shell=True,stdout=PIPE, stderr=PIPE)
        return ['application/pdf', content]