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
        self.doccode = None
        self.file_name = None
        self.revision = None
        self.hashcode = None
        self.metadata = None
        self.fullpath = None

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

    def set_file_obj(self, file_obj): #TODO: check if uploaded_file and file_obj can be merged
        self.file_obj = file_obj

    def get_file_obj(self):
        if self.get_fullpath():
            self.file_obj = open(self.get_fullpath(), 'rb')
        return self.file_obj

    def get_fullpath(self):
        return self.fullpath

    def set_fullpath(self, fullpath):
        self.fullpath = fullpath

    def set_filename(self, filename):
        self.file_name = filename

    def get_filename(self):
        name = self.file_name or self.uploaded_file.name
        if not name and self.get_revision():
            name = self.get_metadata()[self.get_revision() - 1]['name']
        return name

    def get_stripped_filename(self):
        filename = ''
        if self.get_filename():
            filename = self.get_filename()
        else:
            filename = os.path.splitext(self.get_filename())[0]
        return filename

    def get_extension(self):
        return os.path.splitext(self.get_filename())[1][1:]

    def get_revision(self):
        return self.revision

    def set_revision(self, revision):
        self.revision = revision

    def get_filename_with_revision(self):
        return "%s_r%s.%s" % (self.get_stripped_filename(), self.get_revision(), self.get_extension())

    def set_hashcode(self, hashcode):
        self.hashcode = hashcode

    def get_hashcode(self):
        return self.hashcode

    def get_metadata(self):
        return self.metadata

    def set_metadata(self, metadata):
        self.metadata = metadata
