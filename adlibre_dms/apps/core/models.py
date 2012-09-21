"""
Module: DMS Core system object.

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
"""


import os
import magic
import mimetypes
import time
import logging


from django.conf import settings
from core.errors import DmsException
from doc_codes.models import DocumentTypeRuleManagerInstance

log = logging.getLogger('core.document')

class Document(object):
    """
    DMS core Document Object

    Basic internal building block.
    Represents an instance of unique NAME.
    All other DMS processing use it as a main building block.
    However main interaction method of this document is DocumentManager()

    """
    def __init__(self):
        """List of options DMS document object may have during lifetime"""
        self.options = {}
        self.doccode = None
        self.file_name = None # Refactor out, document_manager should have this, not document
        self.full_filename = None # Refactor out, document_manager should have this, not document
        self.stripped_filename = None # Refactor out, document_manager should have this, not document
        self.revision = None
        self.hashcode = None
        self.metadata = None
        self.fullpath = None # Refactor out, document_manager should have this, not document
        self.file_obj = None # Refactor out, document_manager should have this, not document
        self.current_metadata = {}
        self.mimetype = None
        self.tags = []
        self.tag_string = ''
        self.remove_tag_string = ''
        self.requested_extension = None
        self.db_info = {}
        self.new_indexes = {}
        self.index_revisions = {}

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
        log.debug('get_docrule for %s.' % self.doccode)
        # TODO: add checking doccode from Couch_DB or similar (when self.db_info data present). It usually contains it.
        # we can economise 1-2 SQL Db calls this way.
        # Better to implemnt through proxy for e.g.: self.get_docrule_from_db_info()
        if self.doccode is None and self.get_filename():
            self.doccode = DocumentTypeRuleManagerInstance.find_for_string(self.get_stripped_filename())
            if self.doccode is None:
                log.error('get_docrule. doccode is None!')
                raise DmsException("No document type rule found for file " + self.get_full_filename(), 404)
        log.debug('get_docrule finished for %s.' % self.doccode)
        return self.doccode

    def get_mimetype(self):
        if not self.mimetype and self.get_current_metadata():
            self.mimetype = self.get_current_metadata().get('mimetype', None)
        if not self.mimetype and self.get_file_obj():
            mime = magic.Magic( mime = True )
            self.mimetype = mime.from_buffer( self.get_file_obj().read() )
            log.debug('get_mimetype guessed mimetype: %s.' % self.mimetype)
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
                # Fixes extension format 2 dots in API output filename (Bug #588)
                try:
                    if '.' in ext:
                        dot, ext = ext.split(".",1)
                except Exception, e: #FIXME: Except WHAT?
                    log.error('get_full_filename Exception %s' % e)
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
                raise # or r = None, I'm not sure which is more correct behaviour
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

    def get_creation_time(self):
        metadata = self.get_current_metadata()
        if metadata:
            creation_time = metadata.get('creation_time', None)
        else:
            creation_time = time.strftime(settings.DATETIME_FORMAT, time.localtime(os.stat(self.get_fullpath()).st_ctime))
        return creation_time

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

    def update_db_info(self, new_indexes):
        self.new_indexes = new_indexes

    def set_index_revisions(self, revisions_dict):
        """Forces document to have specified index revisions"""
        if revisions_dict:
            self.index_revisions = revisions_dict