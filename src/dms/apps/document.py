import datetime
import os
import magic
import mimetypes
import time

from django.conf import settings

from dms_plugins.workers import DmsException
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
        self.file_obj.seek(0)
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
        revision = self.get_revision()
        if revision:
            name = "%s_r%s.%s" % (self.get_stripped_filename(), self.get_revision(), self.get_extension())
        else:
            name = self.get_full_filename()
        return name

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

    def splitdir(self):
        directory = None
        doccode = self.get_doccode()
        if doccode:
            saved_dir = self.get_option('parent_directory') or ''
            if saved_dir or not doccode.uses_repository:
                doccode_dirs = doccode.split()
                doccode_dirs = map(lambda x: x.replace('{{DATE}}', datetime.datetime.now().strftime('%Y-%m-%d')),
                                    doccode_dirs)
                if saved_dir:
                    doccode_dirs[-1] = saved_dir
                args = [str(doccode.get_id())] + doccode_dirs
                directory = os.path.join(*args)
            else:
                splitdir = ''
                for d in doccode.split(self.get_stripped_filename()):
                    splitdir = os.path.join(splitdir, d)
                directory = os.path.join(str(doccode.get_id()), splitdir)
        return directory

    def get_creation_time(self):
        metadata = self.get_current_metadata()
        if metadata:
            tim = metadata.get('creation_time', None)
        else:
            tim = time.strftime("%d/%m/%Y %H:%M:%S",time.localtime(os.stat(self.get_fullpath()).st_ctime))
        return tim

    def get_dict(self):
        d = {}
        d['current_metadata'] = self.get_current_metadata()
        doccode = self.get_doccode()
        d['doccode'] = {'title': doccode.get_title(), 'id': doccode.get_id()}
        d['document_name'] = self.get_filename()
        return d
