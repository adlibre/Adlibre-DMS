import os
from subprocess import Popen, PIPE
import mimetypes

class FileConverter:

    def __init__(self, filepath):
        self.filepath = filepath


    def to_pdf(self):
        filename = os.path.basename(self.filepath)
        document = os.path.splitext(filename)[0]
        path = '%s/%s.pdf' % (os.path.dirname(self.filepath), document)
        p = Popen('tiff2pdf %s -o %s' % (self.filepath, path), shell=True, stdout=PIPE, stderr=PIPE)
        stdout, stderr = p.communicate()
        content = open(path, 'rb').read()
        p = Popen('rm -rf %s' % path, shell=True,stdout=PIPE, stderr=PIPE)
        return ['application/pdf', content]

