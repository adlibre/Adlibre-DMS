import os

from django.conf import settings

from base.dms import DmsException
from doc_codes import DoccodeManagerInstance

class Document(object):
    """
        Uploaded file is http://docs.djangoproject.com/en/1.3/topics/http/file-uploads/#django.core.files.uploadedfile.UploadedFile
    """
    def __init__(self):
        self.uploaded_file = None
        self.id = None
        self.doccode = None
        self.file_name = None
        self.revision = None

    def get_doccode(self):
        if self.doccode is None:
            self.doccode = DoccodeManagerInstance.find_for_string(self.get_stripped_filename())
            if self.doccode is None:
                raise DmsException("No doccode found for file " + self.get_filename(), 404)
        #print "DOCCODE: %s" % self.doccode #TODO: log.debug this
        return self.doccode

    def set_uploaded_file(self, uploaded_file):
        self.uploaded_file = uploaded_file

    def get_uploaded_file(self):
        return self.uploaded_file

    def set_id(self, doc_id):
        self.id = doc_id

    def get_id(self):
        return self.id

    def get_filename(self):
        name = self.file_name or self.uploaded_file.name
        return name

    def get_stripped_filename(self):
        return os.path.splitext(self.get_filename())[0]

    def get_extension(self):
        return os.path.splitext(self.get_filename())[1][1:]

    def get_revision(self):
        return self.revision

    def set_revision(self, revision):
        self.revision = revision

    def get_filename_with_revision(self):
        return "%s_r%s.%s" % (self.get_stripped_filename(), self.get_revision(), self.get_extension())

