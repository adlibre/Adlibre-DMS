"""
Module: DMS Core CRUD logic handler.

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
"""

import os
import logging

from django.core.files.uploadedfile import UploadedFile

from dms_plugins import pluginpoints
from dms_plugins.operator import PluginsOperator

from core.models import Document
from core.errors import DmsException

log = logging.getLogger('core.document_processor')

# TODO: AC: I think this should be refactored so that 'request' is not used here.
class DocumentProcessor(object):
    """Main DMS CRUD logic operations handler.

    TODO: refactor methods to accept only 1 additional variable 'options'
    so instead of adding local vars:

        Manager().create(request, uploaded_file, index_info, barcode)

    it should list all the options required there. e.g. in this case:

        options = {
                'barcode' = 'ADL-0001' ,
                'index_info' = {
                           # ...
                    },
            }
        class Manager()

            def create(request, uploaded_file, options=None)
                # Context init
                barcode = None
                index_info = None
                # ...
                if options:
                    if 'barcode' in options:
                        barcode = options['barcode']
                    # ...

    Manager should have similar behaviour at all the CRUD methods.
    """
    def __init__(self):
        self.errors = []
        self.warnings = []

    def create(self, request, uploaded_file, index_info=None, barcode=None):
        """
        Creates a new Document() object.

        Responsible for adding new Document() objects into DMS.

        uploaded file is http://docs.djangoproject.com/en/1.3/topics/http/file-uploads/#django.core.files.uploadedfile.UploadedFile
        or file object
        """
        log.debug('CREATE Document %s, index_info: %s, barcode: %s' % (uploaded_file, index_info, barcode))
        operator = PluginsOperator()
        doc = Document()
        doc.set_file_obj(uploaded_file)

        # Setting new file name and type.
        if barcode is not None:
            doc.set_filename(barcode)
            log.debug('Allocated Barcode %s.' % barcode)
        else:
            # Appending error to processor in case we have recieved a "No docrule" file.
            try:
                doc.set_filename(os.path.basename(uploaded_file.name))
            except DmsException, e:
                self.errors.append(unicode(e.parameter))
                return None
                pass
        if hasattr(uploaded_file, 'content_type'):
            doc.set_mimetype(uploaded_file.content_type)
        if index_info:
            doc.set_db_info(index_info)
        # Processing plugins
        # FIXME: if uploaded_file is not None, then some plugins should not run because we don't have a file
        doc = operator.process_pluginpoint(pluginpoints.BeforeStoragePluginPoint, request, document=doc)
        operator.process_pluginpoint(pluginpoints.StoragePluginPoint, request, document=doc)
        doc = operator.process_pluginpoint(pluginpoints.DatabaseStoragePluginPoint, request, document=doc)
        self.check_errors_in_operator(operator)
        return doc

    def read(self, request, document_name, hashcode=None, revision=None, only_metadata=False, extension=None):
        """
        Reads document data from DMS

        Method creates, instantiates and populates new Document() object.
        Using name and/or search filter criteria provided.

        Currently can read Document() with file object attached or either read only metadata.
        """
        log.debug('READ Document %s, hashcode: %s, revision: %s, only_metadata: %s, extension: %s'
                  % (document_name, hashcode, revision, only_metadata, extension) )
        doc = Document()
        operator = PluginsOperator()
        # Checking if name really possible in current DMS config.
        try:
            doc.set_filename(document_name)
        except DmsException, e:
            self.errors.append(unicode(e.parameter))
            return doc
            pass
        doc.set_hashcode(hashcode)
        doc.set_revision(revision)
        options = {'only_metadata': only_metadata,}
        if extension:
            doc.set_requested_extension(extension)
        doc.update_options(options)
        doc = operator.process_pluginpoint(pluginpoints.BeforeRetrievalPluginPoint, request, document=doc)
        self.check_errors_in_operator(operator)
        return doc

    def update(self, request, document_name, tag_string=None, remove_tag_string=None, extension=None, options=None):
        """
        Process update plugins.

        This is needed to update document properties like tags without re-storing document itself.

        Has ability to:
            - update document indexes
            TODO: continue this...
        """
        log.debug('UPDATE Document %s, tag_string: %s, remove_tag_string: %s, extension: %s, options: %s'
                  % (document_name, tag_string, remove_tag_string, extension, options) )
        # Context init
        new_indexes = self.check_options_for_option('new_indexes', options)
        new_name = self.check_options_for_option('new_name', options)

        # Sequence to make a new name for file.
        # TODO: thui deletes all old revisions, instead of real rename...
        if new_name:
            renaming_doc = self.read(request, document_name, extension=extension)
            if new_name != renaming_doc.get_filename():
                ufile = UploadedFile(renaming_doc.get_file_obj(), new_name, content_type=renaming_doc.get_mimetype())
                document = self.create(request, ufile)
                if not self.errors:
                    self.delete(request, renaming_doc.get_filename(), extension=extension)
                return document
        doc = Document()
        operator = PluginsOperator()
        doc.set_filename(document_name)
        if extension:
            doc.set_requested_extension(extension)
        doc.set_tag_string(tag_string)
        doc.set_remove_tag_string(remove_tag_string)
        if new_indexes:
            doc.update_db_info(new_indexes)
        doc = operator.process_pluginpoint(pluginpoints.BeforeUpdatePluginPoint, request, document=doc)
        self.check_errors_in_operator(operator)
        return doc

    def delete(self, request, document_name, revision=None, extension=None):
        """Deletes Document() or it's parts from DMS."""
        log.debug('DELETEE Document %s, revision: %s, extension: %s'
                  % (document_name, revision, extension) )
        doc = Document()
        operator = PluginsOperator()
        doc.set_filename(document_name)
        if extension:
            doc.set_requested_extension(extension)
        if revision:
            doc.set_revision(revision)
        doc = operator.process_pluginpoint(pluginpoints.BeforeRemovalPluginPoint, request, document=doc)
        self.check_errors_in_operator(operator)
        return doc

    def check_errors_in_operator(self, operator):
        """
        Method checks for errors and warnings PluginOperator() has and makes them own errors/warnings.

        Helper method to be used in all CRUD logic for proper PluginOperator() interactions.
        Returns Boolean depending if errors/warnings exist.
        """
        for error in operator.plugin_errors:
            self.errors.append(error)
            log.error('DocumentManager error: %s' % error)
        for warning in operator.plugin_warnings:
            self.warnings.append(warning)
            log.debug('DocumentManager warning: %s' % warning)
        if operator.plugin_errors or operator.plugin_warnings:
            return True
        else:
            return False

    def check_options_for_option(self, option, options, default=None):
        """Redundant checker if options for method has this value"""
        response = default
        if options:
            if option in options:
                response = options[option]
        return response