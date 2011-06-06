import os
import magic
import mimetypes

from django.conf import settings

from base.dms import DmsException
from doc_codes import DoccodeManagerInstance

class Document(object):
    """
        Uploaded file is http://docs.djangoproject.com/en/1.3/topics/http/file-uploads/#django.core.files.uploadedfile.UploadedFile
    """
    def __init__(self):
        self.options = {}
        self.doccode = None
        self.file_name = None
        self.stripped_filename = None
        self.revision = None
        self.hashcode = None
        self.metadata = None
        self.fullpath = None
        self.file_obj = None
        self.current_metadata = {}
        self.mimetype = None

    def get_name(self):
        name = self.get_filename()
        if not name:
            name = self.get_doccode().get_name()
        name = "<Document> %s" % name
        return name

    def __unicode__(self):
        return unicode(self.get_name())

    def __str__(self):
        return self.get_name()

    def __repr__(self):
        return self.get_name()

    def get_doccode(self):
        if self.doccode is None:
            self.doccode = DoccodeManagerInstance.find_for_string(self.get_stripped_filename())
            if self.doccode is None:
                raise DmsException("No doccode found for file " + self.get_full_filename(), 404)
        #print "DOCCODE: %s" % self.doccode #TODO: log.debug this
        return self.doccode

    def get_mimetype(self):
        if not self.mimetype and self.get_current_metadata():
            self.mimetype = self.get_current_metadata().get('mimetype', None)
        if not self.mimetype and self.get_file_obj():
            
            mime = magic.Magic( mime = True )
            self.mimetype = mime.from_buffer( self.get_file_obj().read() )
        return self.mimetype

    def set_mimetype(self, mimetype):
        self.mimetype = mimetype
        self.update_current_metadata({'mimetype': mimetype})

    def set_file_obj(self, file_obj):
        self.file_obj = file_obj

    def get_file_obj(self):
        if not self.file_obj:
            self.file_obj = open(self.get_fullpath(), 'rb')
        return self.file_obj

    def get_fullpath(self):
        return self.fullpath

    def set_fullpath(self, fullpath):
        self.fullpath = fullpath

    def set_filename(self, filename):
        self.file_name = filename

    def get_current_metadata(self):
        if not self.current_metadata and self.get_metadata() and self.get_revision():
            self.current_metadata = self.get_metadata()[self.get_revision() - 1]
        return self.current_metadata

    def get_filename(self):
        try:
            name = self.file_name or self.file_obj.name
        except AttributeError:
            name = ''
        if not name and self.get_revision():
            name = self.get_current_metadata()['name']
        return name

    def get_stripped_filename(self):
        stripped_filename = os.path.splitext(self.get_filename())[0]
        return stripped_filename

    def get_full_filename(self):
        name = self.get_filename()
        if not os.path.splitext(name)[1][1:]:
            ext = self.get_extension_by_mimetype()
            if ext:
                name = "%s.%s" % (name, ext)
        return name

    def get_extension_by_mimetype(self):
        mimetype = self.get_mimetype()
        ext = mimetypes.guess_extension(mimetype)
        return ext

    def get_extension(self):
        return os.path.splitext(self.get_full_filename())[1][1:]

    def get_revision(self):
        r = self.revision
        if r: 
            r = int(r)
        return r

    def set_revision(self, revision):
        self.revision = revision

    def get_filename_with_revision(self):
        return "%s_r%s.%s" % (self.get_stripped_filename(), self.get_revision(), self.get_extension())

    def set_hashcode(self, hashcode):
        self.hashcode = hashcode

    def save_hashcode(self, hashcode):
        self.update_current_metadata({'hashcode': hashcode})

    def get_hashcode(self):
        return self.hashcode

    def get_metadata(self):
        return self.metadata

    def set_metadata(self, metadata):
        self.metadata = metadata

    def update_current_metadata(self, metadata):
        self.get_current_metadata().update(metadata)

    def get_options(self):
        return self.options

    def get_option(self, option):
        return self.options.get(option, None)

    def update_options(self, options):
        self.options.update(options)

