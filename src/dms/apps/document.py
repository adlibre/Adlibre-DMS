"""
Module: DMS core Document Object
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

import datetime
import os
import magic
import mimetypes
import time

from django.conf import settings

from dms_plugins.workers import DmsException
from doc_codes.models import DocumentTypeRuleManagerInstance

class Document(object):
    """
        Uploaded file is http://docs.djangoproject.com/en/1.3/topics/http/file-uploads/#django.core.files.uploadedfile.UploadedFile
    """
    def __init__(self):
        self.options = {}
        self.doccode = None
        self.file_name = None
        self.full_filename = None
        self.stripped_filename = None
        self.revision = None
        self.hashcode = None
        self.metadata = None
        self.fullpath = None
        self.file_obj = None
        self.current_metadata = {}
        self.mimetype = None
        self.tags = []
        self.tag_string = ''
        self.remove_tag_string = ''
        self.requested_extension = None
        self.db_info = {}

    def get_name(self):
        name = self.get_filename()
        if not name:
            name = self.get_docrule().get_name()
        name = "<Document> %s" % name
        return name

    def __unicode__(self):
        return unicode(self.get_name())

    def __str__(self):
        return self.get_name()

    def __repr__(self):
        return self.get_name()

    def get_docrule(self):
        #print "before: ", self.doccode
        if self.doccode is None and self.get_filename():
            self.doccode = DocumentTypeRuleManagerInstance.find_for_string(self.get_stripped_filename())
            if self.doccode is None:
                raise DmsException("No document type rule found for file " + self.get_full_filename(), 404)
        #print "DOCCODE: %s" % self.doccode #TODO: log.debug this
        return self.doccode

    def get_mimetype(self):
        if not self.mimetype and self.get_current_metadata():
            self.mimetype = self.get_current_metadata().get('mimetype', None)
        if not self.mimetype and self.get_file_obj():
            mime = magic.Magic( mime = True )
            self.mimetype = mime.from_buffer( self.get_file_obj().read() )
            #print "GUESSED MIMETYPE: %s" % self.mimetype
        return self.mimetype

    def set_mimetype(self, mimetype):
        self.mimetype = mimetype
        self.update_current_metadata({'mimetype': mimetype})

    def set_file_obj(self, file_obj):
        self.file_obj = file_obj

    def get_file_obj(self):
        if self.get_fullpath() and not self.file_obj:
            self.file_obj = open(self.get_fullpath(), 'rb')
            self.file_obj.seek(0)
        return self.file_obj

    def get_fullpath(self):
        return self.fullpath

    def set_fullpath(self, fullpath):
        self.fullpath = fullpath

    def set_filename(self, filename):
        self.file_name = filename
        # Need to renew docrule on document receives name
        self.doccode = self.get_docrule()

    def get_current_metadata(self):
        if not self.current_metadata and self.get_metadata() and self.get_revision():
            self.current_metadata = self.get_metadata()[str(self.get_revision())]
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
        if not self.full_filename:
            name = self.get_filename()
            if self.get_docrule().no_doccode:
                if self.get_requested_extension():
                    name = "%s.%s" % (name, self.get_requested_extension())
            elif not os.path.splitext(name)[1][1:]:
                ext = self.get_extension_by_mimetype()
                #Fixes extension format 2 dots in API output filename (Bug #588)
                try:
                    if '.' in ext:
                        dot, ext = ext.split(".",1)
                except: #FIXME: Except WHAT?
                    pass # file type conversion is in progress failing gracefully
                if ext:
                    name = "%s.%s" % (name, ext)
            self.full_filename = name
        return self.full_filename

    def set_full_filename(self, filename):
        self.full_filename = filename

    def get_extension_by_mimetype(self):
        mimetype = self.get_mimetype()
        ext = mimetypes.guess_extension(mimetype)
        return ext

    def get_extension(self):
        return os.path.splitext(self.get_full_filename())[1][1:]

    def set_requested_extension(self, extension):
        self.requested_extension = extension

    def get_requested_extension(self):
        return self.requested_extension

    def get_revision(self):
        r = self.revision
        if r: 
            try:
                r = int(r)
            except ValueError:
                pass
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

    def set_option(self, key, value):
        self.options[key] = value

    def splitdir(self):
        directory = None
        doccode = self.get_docrule()
        if doccode:
            saved_dir = self.get_option('parent_directory') or ''
            if saved_dir or doccode.no_doccode:
                doccode_dirs = doccode.split()
                doccode_dirs = map(lambda x: x.replace('{{DATE}}', datetime.datetime.now().strftime(settings.DATE_FORMAT)),
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
            tim = time.strftime(settings.DATETIME_FORMAT, time.localtime(os.stat(self.get_fullpath()).st_ctime))
        return tim

    def get_dict(self):
        d = {}
        d['metadata'] = self.get_metadata()
        d['current_metadata'] = self.get_current_metadata()
        doccode = self.get_docrule()
        d['doccode'] = {'title': doccode.get_title(), 'id': doccode.get_id()}
        d['document_name'] = self.get_filename()
        d['tags'] = self.get_tags()
        return d

    def get_tags(self):
        return self.tags

    def set_tags(self, tags):
        self.tags = tags

    def get_tag_string(self):
        return self.tag_string

    def set_tag_string(self, tag_string):
        if tag_string:
            self.tag_string = tag_string

    def get_remove_tag_string(self):
        return self.remove_tag_string

    def set_remove_tag_string(self, tag_string):
        if tag_string:
            self.remove_tag_string = tag_string

    def get_db_info(self):
        return self.db_info

    def set_db_info(self, db_info):
        self.db_info = db_info
