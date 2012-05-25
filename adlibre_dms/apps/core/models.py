"""
Module: DMS Core system handlers.

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
"""


import datetime
import os
import magic
import mimetypes
import time
import logging
import djangoplugins

from django.conf import settings
from dms_plugins.workers import DmsException
from doc_codes.models import DocumentTypeRuleManagerInstance
from django.core.files.uploadedfile import UploadedFile
from dms_plugins import models
from dms_plugins.workers import PluginError, PluginWarning, BreakPluginChain
from dms_plugins.workers.info.tags import TagsPlugin
from dms_plugins import pluginpoints


log = logging.getLogger('dms.document')
class Document(object):
    """
    DMS core Document Object

    Basic internal building block.
    Represents an instance of unique NAME.
    All other DMS processing use it as a main building block.
    However main interaction method of this document is DocumentManager()

    """
    def __init__(self):
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

    def splitdir(self):
        directory = None
        doccode = self.get_docrule()
        if doccode:
        #            saved_dir = self.get_option('parent_directory') or ''
        #            if saved_dir or doccode.no_doccode:
        #                doccode_dirs = doccode.split()
        #                doccode_dirs = map(lambda x: x.replace('{{DATE}}', datetime.datetime.now().strftime(settings.DATE_FORMAT)),
        #                                    doccode_dirs)
        #                if saved_dir:
        #                    doccode_dirs[-1] = saved_dir
        #                args = [str(doccode.get_id())] + doccode_dirs
        #                directory = os.path.join(*args)
        #            else:
            splitdir = ''
            for d in doccode.split(self.get_stripped_filename()):
                splitdir = os.path.join(splitdir, d)
            directory = os.path.join(str(doccode.get_id()), splitdir)
        return directory

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


log = logging.getLogger('dms.document_manager')
# TODO: Delint this file
# TODO: AC: I think this should be refactored so that 'request' is not used here. Plugin points should be executed elsewhere.
class ConfigurationError(Exception):
    pass

class DocumentManager(object):
    def __init__(self):
        self.errors = []
        self.warnings = []

    def get_plugin_mappings(self):
        return models.DoccodePluginMapping.objects.all()

    def get_plugin_mapping_by_kwargs(self, **kwargs):
        try:
            mapping = models.DoccodePluginMapping.objects.get(**kwargs)
        except models.DoccodePluginMapping.DoesNotExist:
            raise DmsException('Rule not found', 404)
        return mapping

    def get_plugin_mapping(self, document):
        doccode = document.get_docrule()
        log.info('get_plugin_mapping for: %s.' % doccode)
        mapping = models.DoccodePluginMapping.objects.filter(
            doccode = str(doccode.doccode_id),
            active=True)
        if mapping.count():
            mapping = mapping[0]
        else:
            raise DmsException('Rule not found', 404)
        return mapping

    def get_plugins_from_mapping(self, mapping, pluginpoint, plugin_type):
        plugins = []
        plugin_objects = getattr(mapping, 'get_' + pluginpoint.settings_field_name)()
        plugins = map(lambda plugin_obj: plugin_obj.get_plugin(), plugin_objects)
        if plugin_type:
            plugins = filter(lambda plugin: hasattr(plugin, 'plugin_type') and plugin.plugin_type == plugin_type, plugins)
        return plugins

    def get_plugins(self, pluginpoint, document, plugin_type=None):
        mapping = self.get_plugin_mapping(document)
        if mapping:
            plugins = self.get_plugins_from_mapping(mapping, pluginpoint, plugin_type)
        else:
            plugins = []
        return plugins

    def process_pluginpoint(self, pluginpoint, request, document=None):
        plugins = self.get_plugins(pluginpoint, document)
        log.debug('process_pluginpoint: %s with %s plugins.' % (pluginpoint, plugins))
        for plugin in plugins:
            try:
                log.debug('process_pluginpoint begin processing: %s.' % plugin)
                document = plugin.work(request, document)
                log.debug('process_pluginpoint begin processed: %s.' % plugin)
            except PluginError, e: # if some plugin throws an exception, stop processing and store the error message
                self.errors.append(e)
                if settings.DEBUG:
                    log.error('process_pluginpoint: %s.' % e) # e.parameter, e.code
                break
            except PluginWarning, e:
                self.warnings.append(str(e))
            except BreakPluginChain:
                break
        return document

    def store(self, request, uploaded_file, index_info=None, barcode=None):
        """
        Process all storage plugins
        uploaded file is http://docs.djangoproject.com/en/1.3/topics/http/file-uploads/#django.core.files.uploadedfile.UploadedFile
        or file object
        """
        log.debug('Storing Document %s, index_info: %s, barcode: %s' % (uploaded_file, index_info, barcode))
        # Check if file already exists
        if not self.file_exists(request, uploaded_file.name):
            doc = Document()
            doc.set_file_obj(uploaded_file)
            if barcode is not None:
                doc.set_filename(barcode)
                log.debug('Allocated Barcode %s.' % barcode)
            else:
                doc.set_filename(os.path.basename(uploaded_file.name))
            if hasattr(uploaded_file, 'content_type'):
                doc.set_mimetype(uploaded_file.content_type)
            if index_info:
                doc.set_db_info(index_info)
                # FIXME: if uploaded_file is not None, then some plugins should not run because we don't have a file
            doc = self.process_pluginpoint(pluginpoints.BeforeStoragePluginPoint, request, document=doc)
            # Process storage plugins
            self.process_pluginpoint(pluginpoints.StoragePluginPoint, request, document=doc)
            # Process DatabaseStorage plugins
            doc = self.process_pluginpoint(pluginpoints.DatabaseStoragePluginPoint, request, document=doc)
            #mapping = self.get_plugin_mapping(doc)
            #for plugin in mapping.get_database_storage_plugins(): print 'Mapping has plugin: ', plugin
        else:
            doc = self.update(request, uploaded_file.name)
        return doc

    def rename(self, request, document_name, new_name, extension):
        doc = self.retrieve(request, document_name, extension=extension)
        if new_name and new_name != doc.get_filename():
            name = new_name
            ufile = UploadedFile(doc.get_file_obj(), name, content_type=doc.get_mimetype())
            new_doc = self.store(request, ufile)
            if not self.errors:
                self.remove(request, doc.get_filename(), extension=extension)
            #            else:
            #                if settings.DEBUG:
            #                    print "ERRORS: %s" % self.errors
            return new_doc

    def update(self, request, document_name, tag_string=None, remove_tag_string=None, extension=None):
        """
        Process update plugins.

        This is needed to update document properties like tags without re-storing document itself.
        """
        doc = Document()
        doc.set_filename(document_name)
        #doc = self.retrieve(request, document_name)
        if extension:
            doc.set_requested_extension(extension)
        doc.set_tag_string(tag_string)
        doc.set_remove_tag_string(remove_tag_string)
        return self.process_pluginpoint(pluginpoints.BeforeUpdatePluginPoint, request, document=doc)

    def retrieve(self, request, document_name, hashcode=None, revision=None, only_metadata=False, extension=None):
        doc = Document()
        doc.set_filename(document_name)
        doc.set_hashcode(hashcode)
        doc.set_revision(revision)
        options = {'only_metadata': only_metadata,}
        if extension:
            doc.set_requested_extension(extension)
        doc.update_options(options)
        doc = self.process_pluginpoint(pluginpoints.BeforeRetrievalPluginPoint, request, document=doc)
        return doc

    def remove(self, request, document_name, revision=None, extension=None):
        doc = Document()
        doc.set_filename(document_name)
        if extension:
            doc.set_requested_extension(extension)
        if revision:
            doc.set_revision(revision)
        return self.process_pluginpoint(pluginpoints.BeforeRemovalPluginPoint, request, document=doc)

    def get_plugins_by_type(self, doccode_plugin_mapping, plugin_type, pluginpoint=pluginpoints.BeforeStoragePluginPoint):
        plugins = self.get_plugins_from_mapping(doccode_plugin_mapping, pluginpoint, plugin_type=plugin_type)
        return plugins

    def get_storage(self, doccode_plugin_mapping, pluginpoint=pluginpoints.StoragePluginPoint):
        #Plugin point does not matter here as mapping must have a storage plugin both at storage and retrieval stages
        storage = self.get_plugins_by_type(doccode_plugin_mapping, 'storage', pluginpoint)
        #Document MUST have a storage plugin
        if not storage:
            raise ConfigurationError("No storage plugin for %s" % doccode_plugin_mapping)
            #Should we validate more than one storage plugin?
        return storage[0]

    def get_metadata(self, doccode_plugin_mapping, pluginpoint=pluginpoints.StoragePluginPoint):
        metadata = None
        metadatas = self.get_plugins_by_type(doccode_plugin_mapping, 'metadata', pluginpoint)
        if metadatas: metadata = metadatas[0]
        return metadata

    def get_file_list(self, doccode_plugin_mapping, start=0, finish=None, order=None, searchword=None,
                      tags=[], filter_date=None):
        storage = self.get_storage(doccode_plugin_mapping)
        metadata = self.get_metadata(doccode_plugin_mapping)
        doccode = doccode_plugin_mapping.get_docrule()
        doc_models = TagsPlugin().get_doc_models(doccode=doccode_plugin_mapping.get_docrule(), tags=tags)
        doc_names = map(lambda x: x.name, doc_models)
        if metadata:
            document_directories = metadata.worker.get_directories(doccode, filter_date=filter_date)
        else:
            document_directories = []
        return storage.worker.get_list(doccode, document_directories, start, finish, order, searchword,
            limit_to=doc_names)

    def get_file(self, request, document_name, hashcode, extension, revision=None):
        document = self.retrieve(request, document_name, hashcode=hashcode, revision=revision, extension=extension,)
        mimetype, filename, content = (None, None, None)
        if not self.errors:
            document.get_file_obj().seek(0)
            content = document.get_file_obj().read()
            mimetype = document.get_mimetype()

            if revision:
                filename = document.get_filename_with_revision()
            else:
                filename = document.get_full_filename()
        return mimetype, filename, content

    def delete_file(self, request, document_name, revision=None, extension=None):
        document = self.remove(request, document_name, revision=revision, extension=extension)
        return document

    def get_revision_count(self, document_name, doccode_plugin_mapping):
        storage = self.get_storage(doccode_plugin_mapping)
        doc = Document()
        doc.set_filename(document_name)
        return storage.worker.get_revision_count(doc)

    def get_plugin_list(self):
        all_plugins = djangoplugins.models.Plugin.objects.all().order_by('point__name', 'index')
        return all_plugins

    def get_all_tags(self, doccode=None):
        return TagsPlugin().get_all_tags(doccode = doccode)

    def file_exists(self, request, filename):
        """
        Main condition of file present in DMS is here
        """
        exists = False
        # TODO: implement this to really check if we need ot update document
        #        file_obj = self.retrieve(request, filename, only_metadata=True)
        #        if file_obj.metadata:
        #            exists = True
        return exists
