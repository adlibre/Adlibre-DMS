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

__all__ = ['DocumentProcessor']


class DocumentProcessor(object):
    """Main DMS CRUD logic operations handler.

    Architecture:
        - this manager defines main DMS core level of interaction.
        - works with "options" object, that is a dict. e.g.:
            options = {
                'hashcode': 03245634599134569234,
                'revision': 1,
                'extension': pdf,
                'user': request.user,
                # ...
            }
        - has a CRUD architecture usually taking a document_name or uploaded_file as a first variable
            and using "options" dict for interaction/processing actions.
        - typical interaction cycle is:

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
        - should have better difference between create and update
            currently: create new revision == Create task, this is wrong.
        - should not delete all the Document() revisions on rename.
    """
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.document_name = ''
        self.document_file = None

    # TODO: new_revision == create call. This is wrong.
    def create(self, uploaded_file, options):
        """
        Creates a new Document() and saves it into DMS.

        Should have at least 2 essential options:
        @uploaded_file is http://docs.djangoproject.com/en/1.3/topics/http/file-uploads/#django.core.files.uploadedfile.UploadedFile or file object
        @user is https://docs.djangoproject.com/en/dev/topics/auth/default/#user-objects (Normal Django user)

        Valid only if no DMS Object with such code exists in the system. Has a validation for that.
        """
        barcode = self.option_in_options('barcode', options)
        valid = True
        log.debug('CREATE Document %s, barcode: %s' % (uploaded_file, barcode))
        operator = PluginsOperator()
        doc = self.init_Document_with_data(options, document_file=uploaded_file)
        # Setting new file name and type.
        try:
            if barcode is not None:
                doc.set_filename(barcode)
                log.debug('Allocated Barcode %s.' % barcode)
            else:
                doc.set_filename(os.path.basename(uploaded_file.name))
        except DmsException, e:
            # Appending error to processor, usually in case we have received a "No docrule" file.
            log.error(e)
            self.errors.append(unicode(e.parameter))
            return None
            pass
        # Checking if file with this code already exists in system with certain code (barcode) is specified
        doc_name = doc.get_filename()
        if doc_name:
            # Extract code from filename
            if '.' in doc_name:
                doc_name, extension = os.path.splitext(doc_name)
            # Check the DMS for existence of this code
            possible_doc = self.read(doc_name, {'only_metadata': True, 'user': doc.user})
            if possible_doc.file_revision_data and not self.errors \
                or ('mdt_indexes' in possible_doc.db_info and possible_doc.db_info['mdt_indexes']):
                error = DmsException('Document "%s" already exists' % doc_name, 409)
                self.errors.append(error)
                valid = False
            if self.errors:
                if self.errors.__len__() == 1 and self.errors[0].code == 404:
                    self.errors = []
        # Processing plugins
        if valid:
            if doc.uncategorized:
                doc.allocate_next_uncategorized()
            doc = operator.process_pluginpoint(pluginpoints.BeforeStoragePluginPoint, document=doc)
            if not operator.plugin_errors:
                if uploaded_file:
                    # Storage plugins should not run in case Uploaded_file is none
                    operator.process_pluginpoint(pluginpoints.StoragePluginPoint, document=doc)
                doc = operator.process_pluginpoint(pluginpoints.DatabaseStoragePluginPoint, document=doc)
            self.check_errors_in_operator(operator)
        return doc

    def read(self, document_name, options):
        """
        Reads Document() data from DMS

        Method creates, instantiates and populates new Document() object.
        Using name and/or search filter criteria provided.

        Currently can read Document() with file object attached or either read only file info data.

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
        doc = operator.process_pluginpoint(pluginpoints.BeforeRetrievalPluginPoint, document=doc)
        self.check_errors_in_operator(operator)
        return doc

    # TODO: Update should not delete all the old document's revisions on rename.
    def update(self, document_name, options):
        """
        Process update plugins.

        This is needed to update document properties like tags without re-storing document itself.

        Has ability to:
            - update document indexes
            - update document revision (upload new file to existing code)
            - update document tags
            TODO: continue this...

        @param options: should be dict with certain keys and values set that represent call requirements.
            keys and their meaning:
                - 'new_type' to change Document type.
                    Should be of DocumentTypeRule model instance selected with desired type OR unicode PK of that model
        """
        log.debug('UPDATE Document %s, options: %s' % (document_name, options))
        new_name = self.option_in_options('new_name', options)
        new_file_revision = self.option_in_options('update_file', options)
        user = self.option_in_options('user', options)

        # Sequence to make a new name for file.
        # TODO: this deletes all old revisions, instead of real rename of all files...
        # Must become a plugins sequence task.
        if new_name:
            extension = self.option_in_options('extension', options)
            renaming_doc = self.read(document_name, options={'extension': extension, 'user': user})
            if new_name != renaming_doc.get_filename():
                ufile = UploadedFile(renaming_doc.get_file_obj(), new_name, content_type=renaming_doc.get_mimetype())
                document = self.create(ufile, {'user': user})
                if not self.errors:
                    self.delete(renaming_doc.get_filename(), options={'extension': extension, 'user': user})
                return document

        operator = PluginsOperator()
        doc = self.init_Document_with_data(options, document_name=document_name)
        # Storing new file revision of an object. It requires content setup from uploaded file.
        if new_file_revision:
            if 'content_type' in new_file_revision.__dict__.iterkeys():
                doc.set_mimetype(new_file_revision.content_type)
            else:
                error = 'Error updating file revision for file: %s' % new_file_revision
                log.error(error)
                self.errors.append(error)
        doc = operator.process_pluginpoint(pluginpoints.BeforeUpdatePluginPoint, document=doc)
        doc = operator.process_pluginpoint(pluginpoints.UpdatePluginPoint, document=doc)
        doc = operator.process_pluginpoint(pluginpoints.DatabaseUpdatePluginPoint, document=doc)
        self.check_errors_in_operator(operator)
        return doc

    def delete(self, document_name, options):
        """Deletes Document() or it's parts from DMS."""
        log.debug('DELETEE Document %s, options: %s' % (document_name, options) )
        operator = PluginsOperator()
        doc = self.init_Document_with_data(options, document_name=document_name)
        if self.option_in_options('delete_revision', options):
            doc = self.read(document_name, options)
        doc = operator.process_pluginpoint(pluginpoints.BeforeRemovalPluginPoint, document=doc)
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
    def option_in_options(self, option, options, default=None):
        """Redundant checker if options for method has this value

        @option is a name of an option being requested
        @options is a {} of options to query an option
        @default is a value of the option that is returned if the option does not exist in options
        """
        response = default
        if options:
            if option in options:
                response = options[option]
        return response

    def init_Document_with_data(self, options, doc=None, document_name=None, document_file=None):
        """Populate given Document() class with given properties from "options" provided

        Makes expansion of interaction methods with Document() simple.
        Expand this actions to add new interactions with Document() object...

        Connector between "options" passed to this CRUD manager and later Plugin() interactions.

        @options is a dict of operation options (that change behaviour of operations)
        @doc is a Document() instance
        @document_name is a name of a document being processed
        @document_file is a file object being processed
        """
        if doc is None:
            doc = Document()
        # All methods sequence, besides create()
        if document_name:
            doc.set_filename(document_name)
        # Usually create() method sequence
        if document_file:
            doc.set_file_obj(document_file)
            if hasattr(document_file, 'content_type'):
                doc.set_mimetype(document_file.content_type)
        if options:
            try:
                for property_name, value in options.iteritems():
                    if property_name == 'hashcode':
                        doc.set_hashcode(value)
                    if property_name == 'revision':
                        doc.set_revision(value)
                    # Run for plugins without retrieving document. Only count file info data.
                    if property_name == 'revision_count':
                        doc.update_options({'revision_count': True,
                                            'only_metadata': True})
                    if property_name == 'extension':
                        doc.set_requested_extension(value)
                    if property_name == 'tag_string':
                        if value:
                            doc.set_tag_string(value)
                            doc.update_options({property_name: value})
                    if property_name == 'remove_tag_string':
                        if value:
                            doc.set_remove_tag_string(value)
                            doc.update_options({property_name: value})
                    if property_name == 'new_indexes':
                        doc.update_db_info(value)
                    if property_name == 'user':
                        doc.set_user(value)
                    if property_name == 'index_info':
                        # Not to modify original data during workflow
                        data = value.copy()
                        doc.set_db_info(data)
                    if property_name == 'new_type':
                        if value:
                            doc.set_change_type(value)
                    if property_name == 'mark_deleted':
                        if value:
                            doc.update_options({property_name: True})
                    if property_name == 'mark_revision_deleted':
                        if value:
                            doc.update_options({property_name: value})
                    if property_name == 'thumbnail':
                        if value:
                            doc.update_options({property_name: True})
                    if property_name == 'delete_revision':
                        if value:
                            doc.update_options({property_name: value})
                            doc.set_revision(int(value))
                    if property_name == 'update_file':
                        doc.set_file_obj(value)
                        if value:
                            # Option for update function so we know we have a file update sequence
                            doc.update_options({property_name: True})
                if 'only_metadata' in options:
                    doc.update_options({'only_metadata': options['only_metadata']})
            except Exception, e:
                self.errors.append('Error working with Object: %s' % e)
                log.error(
                    'DocumentManager().init_Document_with_data() error: %s, doc: %s, options: %s, document_name: %s'
                    % (e, doc, options, document_name))
                pass
            # Every method call should have a Django User inside. Validating that.
            if not 'user' in options and not options['user']:
                error = 'Wrong DocumentProcessor() method call. Should have a proper "user" option set'
                log.error(error)
                self.errors.append(error)
                raise DmsException(error, 500)
        return doc