"""
Module: DMS Core Document manipulations handler.

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
"""


import os
import logging
import djangoplugins

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from dms_plugins import models
from dms_plugins.workers import PluginError, PluginWarning, BreakPluginChain
from dms_plugins.workers.info.tags import TagsPlugin
from dms_plugins import pluginpoints
from dms_plugins.workers import DmsException

from core.models import Document

log = logging.getLogger('core.document_manager')

# TODO: Delint this file
# TODO: AC: I think this should be refactored so that 'request' is not used here. Plugin points should be executed elsewhere.
class ConfigurationError(Exception):
    pass

class DocumentManager(object):
    """
    Document() object operations handler
    """
    def __init__(self):
        self.errors = []
        self.warnings = []

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
