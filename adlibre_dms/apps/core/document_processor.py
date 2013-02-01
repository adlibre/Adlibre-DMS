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

class DocumentProcessor(object):
    """Main DMS CRUD logic operations handler.

    Architecture:
        - this manager defines main DMS core level of interaction.
        - works with "options" object, that is a dict. e.g.:
            options = {
                'hashcode': 03245634599134569234,
                'revision': 1,
                'extension': pdf,
                # ...
            }
        - has a CRUD architecture usually taking a document_name or uploaded_file as a first variable
            and using "options" dict for interaction/processing actions.
        - typical intaraction cycle is:

            class Manager()

            def create(uploaded_file, options=None)
                # Context init
                barcode = None
                index_info = None
                # ...
                if options:
                    if 'barcode' in options:
                        barcode = options['barcode']
                    # ...

    TODO:
        - should not use django "request" object, that is wrong and must be refactored in future releases.
            # TODO: discuss this... may trim a bit of flexibility for potential development.
        - should have similar architecture in all calls (CRUD)
        - should have better difference between create and update
            currently: create new revision == Create task, this is wrong.
        - should not delete all the Document() revisions on rename.
    """
    # TODO: refactor so that 'request' is not used here. # (Should we? Potential loss of flexibility in plugins.)
    def __init__(self):
        self.errors = []
        self.warnings = []

    # TODO: new_revision == create call. This is wrong.
    # TODO: use options={'barcode': ... , 'index_info': ... ,} instead of adding params.
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

    def read(self, request, document_name, options=None):
        """
        Reads document data from DMS

        Method creates, instantiates and populates new Document() object.
        Using name and/or search filter criteria provided.

        Currently can read Document() with file object attached or either read only metadata.
        """
        log.debug('READ Document %s with options: %s' % (document_name, options))
        doc = Document()
        operator = PluginsOperator()
        # Checking if name really possible in current DMS config.
        try:
            doc.set_filename(document_name)
        except DmsException, e:
            self.errors.append(unicode(e.parameter))
            return doc
            pass
        doc = self.init_Document_with_data(options, doc)
        doc = operator.process_pluginpoint(pluginpoints.BeforeRetrievalPluginPoint, request, document=doc)
        self.check_errors_in_operator(operator)
        return doc

    # TODO: Update should not delete all the old document's revisions on rename.
    def update(self, request, document_name, options):
        """
        Process update plugins.

        This is needed to update document properties like tags without re-storing document itself.

        Has ability to:
            - update document indexes
            TODO: continue this...
        """
        log.debug('UPDATE Document %s, options: %s' % (document_name, options))
        new_name = self.check_options_for_option('new_name', options)

        # Sequence to make a new name for file.
        # TODO: this deletes all old revisions, instead of real rename of all files...
        if new_name:
            extension = self.check_options_for_option('extension', options)
            renaming_doc = self.read(request, document_name, options={'extension':extension,})
            if new_name != renaming_doc.get_filename():
                ufile = UploadedFile(renaming_doc.get_file_obj(), new_name, content_type=renaming_doc.get_mimetype())
                document = self.create(request, ufile)
                if not self.errors:
                    self.delete(request, renaming_doc.get_filename(), options={'extension': extension,})
                return document

        operator = PluginsOperator()
        doc = self.init_Document_with_data(options, document_name=document_name)
        doc = operator.process_pluginpoint(pluginpoints.BeforeUpdatePluginPoint, request, document=doc)
        self.check_errors_in_operator(operator)
        return doc

    def delete(self, request, document_name, options):
        """Deletes Document() or it's parts from DMS."""
        log.debug('DELETEE Document %s, options: %s' % (document_name, options) )
        operator = PluginsOperator()
        doc = self.init_Document_with_data(options, document_name=document_name)
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

    """Internal helper functionality"""
    def check_options_for_option(self, option, options, default=None):
        """Redundant checker if options for method has this value"""
        response = default
        if options:
            if option in options:
                response = options[option]
        return response

    def init_Document_with_data(self, options, doc=None, document_name=None ):
        """Populate given Document() class with given properties from "options" provided

        Makes expansion of interaction methods with Document() simple.
        Expand this actions to add new interactions with Document() object...

        Connector between "options" passed to this CRUD manager and later Plugin() interactions.
        """
        if doc is None:
            doc = Document()
            doc.set_filename(document_name)
        if options:
            try:
                for property_name, value in options.iteritems():
                    if property_name=='hashcode':
                        doc.set_hashcode(value)
                    if property_name=='revision':
                        doc.set_revision(value)
                    # Run for plugins without retriving document. Only count metadata.
                    if property_name=='revision_count':
                        doc.update_options({'revision_count': True,
                                            'only_metadata': True,})
                    if property_name=='extension':
                        doc.set_requested_extension(value)
                    if property_name=='tag_string':
                        doc.set_tag_string(value)
                    if property_name=='remove_tag_string':
                        doc.set_remove_tag_string(value)
                    if property_name=='new_indexes':
                        doc.update_db_info(value)
                if 'only_metadata' in options:
                    doc.update_options({'only_metadata': options['only_metadata'],})
            except Exception, e:
                self.errors.append('Error working with Object: %s' % e)
                log.error('DocumentManager().init_Document_with_data() error: %s, doc: %s, options: %s, document_name:%s'
                          % (e, doc, options, document_name))
                pass
        return doc