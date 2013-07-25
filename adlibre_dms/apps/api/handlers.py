"""
Module: Piston API Handlers

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011, 2012
License: See LICENSE for license information
"""

import json
import os
import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse

from piston.handler import BaseHandler
from piston.utils import rc

from django.utils.decorators import method_decorator
from api.decorators.auth import logged_in_or_basicauth
from api.decorators.group_required import group_required

from core.document_processor import DocumentProcessor
from core.parallel_keys import process_pkeys_request
from core.http import DMSObjectResponse, DMSOBjectRevisionsData
from dms_plugins.operator import PluginsOperator
from dms_plugins.models import DoccodePluginMapping
from mdt_manager import MetaDataTemplateManager
from dms_plugins.workers.info.tags import TagsPlugin

from mdtui.security import list_permitted_docrules_qs


log = logging.getLogger('dms.api.handlers')

AUTH_REALM = 'Adlibre DMS'


class BaseFileHandler(BaseHandler):

    def _get_info(self, request):
        revision = request.GET.get('r', None)
        hashcode = request.GET.get('h', None)
        extra = request.REQUEST
        log.debug('BaseFileHandler._get_info returned: %s : %s : %s.' % (revision, hashcode, extra))
        return revision, hashcode, extra


class FileHandler(BaseFileHandler):
    """CRUD Methods for documents"""
    allowed_methods = ('GET', 'POST', 'DELETE', 'PUT')

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required('api'))  # FIXME: Should be more granular permissions
    def create(self, request, code, suggested_format=None):
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
        else:
            return rc.BAD_REQUEST
        processor = DocumentProcessor()
        options = {
            'user': request.user,
            'barcode': code,
        }
        document = processor.create(uploaded_file, options)
        if len(processor.errors) > 0:
            log.error('FileHandler.create manager errors: %s' % processor.errors)
            return rc.BAD_REQUEST
        log.info('FileHandler.create request fulfilled for %s' % document.get_filename())
        return rc.CREATED

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required('api'))  # FIXME: Should be more granular permissions
    def read(self, request, code, suggested_format=None):
        revision, hashcode, extra = self._get_info(request)
        processor = DocumentProcessor()
        options = {
            'hashcode': hashcode,
            'revision': revision,
            'extension': suggested_format,
            'user': request.user,
        }
        document = processor.read(code, options)
        if not request.user.is_superuser:
            # Hack: Used part of the code from MDTUI Wrong!
            user_permissions = list_permitted_docrules_qs(request.user)
            if not document.doccode in user_permissions:
                return rc.FORBIDDEN
        if processor.errors:
            log.error('FileHandler.read manager errors: %s' % processor.errors)
            return rc.NOT_FOUND
        if document.marked_deleted:
            log.error('FileHandler.read request to marked deleted document: %s' % code)
            return rc.NOT_FOUND
        else:
            response = DMSObjectResponse(document)
            log.info('FileHandler.read request fulfilled for code: %s, options: %s' % (code, options))
        return response

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required('api'))  # FIXME: Should be more granular permissions
    def update(self, request, code, suggested_format=None):
        revision, hashcode, extra = self._get_info(request)
        uploaded_obj = None
        if 'file' in request.FILES:
            uploaded_obj = request.FILES['file']
        # TODO refactor these verbs
        tag_string = request.PUT.get('tag_string', None)
        remove_tag_string = request.PUT.get('remove_tag_string', None)
        new_name = request.PUT.get('new_name', None)
        new_type = extra.get('new_type', None)
        index_data = extra.get('indexing_data', None)
        if index_data:
            index_data = json.loads(index_data)
        processor = DocumentProcessor()
        options = {
            'tag_string': tag_string,
            'remove_tag_string': remove_tag_string,
            'extension': suggested_format,
            'new_name': new_name,
            'new_type': new_type,
            'new_indexes': index_data,
            'update_file': uploaded_obj,
            'user': request.user,
        }  # FIXME hashcode missing?
        document = processor.update(code, options)
        if len(processor.errors) > 0:
            print processor.errors
            log.error('FileHandler.update manager errors %s' % processor.errors)
            if settings.DEBUG:
                raise Exception('FileHandler.update manager errors')
            else:
                return rc.BAD_REQUEST
        log.info('FileHandler.update request fulfilled for code: %s, format: %s, rev: %s, hash: %s.'
                 % (code, suggested_format, revision, hashcode))
        resp = DMSOBjectRevisionsData(document).jsons
        return HttpResponse(resp)   # FIXME should be rc.ALL_OK


    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required('api')) # FIXME: Should be more granular permissions
    def delete(self, request, code, suggested_format=None):
        # FIXME: should return 404 if file not found, 400 if no docrule exists.
        revision, hashcode, extra = self._get_info(request)
        processor = DocumentProcessor()
        options = {
            'revision': revision,
            'extension': suggested_format,
            'user': request.user,
        }
        log.debug('FileHandler.delete attempt with %s' % options)
        processor.delete(code, options)
        if len(processor.errors) > 0:
            log.error('Manager Errors encountered %s' % processor.errors)
            return rc.BAD_REQUEST
        log.info('FileHandler.delete request fulfilled for code: %s, format: %s, rev: %s, hash: %s.' % (code, suggested_format, revision, hashcode))
        return rc.DELETED


class OldFileHandler(BaseFileHandler):
    """Deprecated Files handler logic"""
    allowed_methods = ('GET', 'POST')

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required('api'))
    def create(self, request, code, suggested_format=None):
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
        else:
            return rc.BAD_REQUEST
        processor = DocumentProcessor()
        options = {
            'user': request.user,
            'barcode': code,
        }
        document = processor.create(uploaded_file, options)
        if len(processor.errors) > 0:
            log.error('OldFileHandler.create errors: %s' % processor.errors)
            error = processor.errors[0]
            if error.code == 409:
                new_processor = DocumentProcessor()
                options['update_file'] = uploaded_file
                document = new_processor.update(code, options)
                if len(new_processor.errors) > 0:
                    return rc.BAD_REQUEST
        log.info('OldFileHandler.create request fulfilled for %s' % document.get_filename())
        return document.get_filename()

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required('api'))
    def read(self, request, code, suggested_format=None):
        revision, hashcode, extra = self._get_info(request)
        processor = DocumentProcessor()
        options = {
            'hashcode': hashcode,
            'revision': revision,
            'extension': suggested_format,
            'user': request.user,
        }
        document = processor.read(code, options)
        if not request.user.is_superuser:
            # Hack: Used part of the code from MDTUI Wrong!
            user_permissions = list_permitted_docrules_qs(request.user)
            if not document.doccode in user_permissions:
                return rc.FORBIDDEN
        if processor.errors:
            log.error('OldFileHandler.read manager errors: %s' % processor.errors)
            return rc.NOT_FOUND
        if document.marked_deleted:
            log.error('OldFileHandler.read request to marked deleted document: %s' % code)
            return rc.NOT_FOUND
        else:
            response = DMSObjectResponse(document)
            log.info('OldFileHandler.read request fulfilled for code: %s, options: %s' % (code, options))
        return response


class FileInfoHandler(BaseFileHandler):
    """
    Returns document file info data
    """
    allowed_methods = ('GET',)

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required('api'))  # FIXME: Should be more granular permissions
    def read(self, request, code, suggested_format=None):
        revision, hashcode, extra = self._get_info(request)
        processor = DocumentProcessor()
        options = {
            'revision': revision,
            'hashcode': hashcode,
            'only_metadata': True,
            'extension': suggested_format,
            'user': request.user,
        }
        document = processor.read(code, options)
        if document.marked_deleted:
            log.error('FileInfoHandler.read request to marked deleted document: %s' % code)
            return rc.NOT_FOUND
        if processor.errors:
            log.error('FileInfoHandler.read errors: %s' % processor.errors)
            if settings.DEBUG:
                raise Exception('FileInfoHandler.read manager.errors')
            else:
                return rc.BAD_REQUEST
        info = DMSOBjectRevisionsData(document).jsons
        log.info('FileInfoHandler.read request fulfilled for %s, ext %s, rev %s, hash %s' % (code, suggested_format, revision, hashcode))
        return HttpResponse(info)


class FileListHandler(BaseHandler):
    """
    Provides list of documents to facilitate browsing via document type rule id.
    """
    allowed_methods = ('GET', 'POST')

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required('api')) # FIXME: Should be more granular permissions
    def read(self, request, id_rule):
        try:
            operator = PluginsOperator()
            mapping = operator.get_plugin_mapping_by_id(id_rule)
            start = 0
            finish = None
            try:
                start = int(request.GET.get('start', 0))
                finish = request.GET.get('finish', None)
                order = request.GET.get('order', None)
                searchword = request.GET.get('q', None)
                tag = request.GET.get('tag', None)
                filter_date = request.GET.get('created_date', None)
                if finish:
                    finish = int(finish)
            except ValueError, e:
                log.error('FileListHandler.read ValueError %s' % e)
                if settings.DEBUG:
                    raise
                else:
                    pass
            file_list = operator.get_file_list(mapping, start, finish, order, searchword, tags=[tag],
                                                filter_date = filter_date)
            for item in file_list:
                ui_url = reverse('ui_document', kwargs={'document_name': item['name']})
                thumb_url = reverse('api_thumbnail', kwargs={'code': item['name']})
                item.update({   'ui_url': ui_url,
                                'thumb_url': thumb_url,
                                'rule': mapping.get_name(),
                            })
            log.info('FileListHandler.read request fulfilled for start %s, finish %s, order %s, searchword %s, tag %s, filter_date %s.'
                                    % (start, finish, order, searchword, tag, filter_date))
            return file_list
        except Exception, e:
            log.error('FileListHandler.read Exception %s' % e)
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST


class TagsHandler(BaseHandler):
    """
    Provides list of tags for id_rule
    """
    allowed_methods = ('GET',)

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required('api')) # FIXME: Should be more granular permissions
    def read(self, request, id_rule):
        # FIXME: Requirement for this whole API hook is wrong.
        # Tags should be got with document metadata. Not with a separate reequest.
        try:
            operator = PluginsOperator()
            mapping = operator.get_plugin_mapping_by_id(id_rule)
            docrule = mapping.get_docrule()
            tags = TagsPlugin().get_all_tags(doccode=docrule)
            log.info('TagsHandler.read request fulfilled for rule %s' % id_rule)
            return map(lambda x: x.name, tags)
        except Exception, e:  # FIXME
            log.error('TagsHandler.read Exception %s' % e)
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST


class RevisionCountHandler(BaseHandler):
    """
    Returns revision count for a document
    """
    allowed_methods = ('GET','POST')

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required('api')) # FIXME: Should be more granular permissions
    def read(self, request, document):
        document, extension = os.path.splitext(document)
        processor = DocumentProcessor()
        document = processor.read(document, options={'revision_count': True, 'user': request.user,})
        rev_count = document.get_revision()
        if rev_count <= 0:
            log.info('RevisionCountHandler.read rev_count %s.' % str(rev_count))
            if settings.DEBUG:
                raise Exception('No document revisions')
            else:
                return rc.BAD_REQUEST
        if processor.errors:
            log.error('RevisionCountHandler.read Exception %s' % processor.errors[0])
            return rc.BAD_REQUEST
        log.info('RevisionCountHandler.read request fulfilled for document %s, extension %s' % (document, extension))
        return rev_count


class RulesHandler(BaseHandler):
    """
    Returns list of all doc type rules in the system
    """
    allowed_methods = ('GET', 'POST')

    verbose_name = 'rule'
    verbose_name_plural = 'rules'

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required('api'))  # FIXME: Should be more granular permissions
    def read(self, request):
        """Returns list of Document Type Rule <=> Plugins mapping

        @param request:
        @return: list of document type rules
        """
        doc_types_mappings = DoccodePluginMapping.objects.all()
        rules_json = []
        for rule in doc_types_mappings:
            rules_json.append(
                dict(
                    doccode=rule.get_docrule().get_title(),
                    id=rule.pk,
                    ui_url=reverse('ui_document_list', kwargs={'id_rule': rule.pk}),
                )
            )
        log.info('RulesHandler.read request fulfilled')
        return rules_json


class RulesDetailHandler(BaseHandler):
    """
    Returns detailed information about a doc type rule
    """
    allowed_methods = ('GET','POST')

    fields = ['id', 'name', ('before_storage_plugins', ('name',)), 
                            ('storage_plugins', ('name',)), 
                            ('before_retrieval_plugins', ('name',)), 
                            ('before_removal_plugins', ('name',)),
                            ('database_storage_plugins', ('name',)),]

    verbose_name = 'rule'
    verbose_name_plural = 'rules'

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required('api'))  # FIXME: Should be more granular permissions
    def read(self, request, id_rule):
        operator = PluginsOperator()
        try:
            mapping = operator.get_plugin_mapping_by_id(id_rule)
        except Exception, e: # FIXME
            log.error('RulesDetailHandler.read Exception %s' % e)
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST
        log.info('RulesDetailHandler.read request fulfilled for rule %s' % id_rule)
        return mapping


class PluginsHandler(BaseHandler):
    """
    Returns a list of plugins installed in the system
    """
    allowed_methods = ('GET','POST')

    verbose_name = 'plugin'
    verbose_name_plural = 'plugins'

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required('api')) # FIXME: Should be more granular permissions
    def read(self, request):
        operator = PluginsOperator()
        try:
            plugin_list = operator.get_plugin_list()
        except Exception, e: # FIXME
            log.error('PluginsHandler.read Exception %s' % e)
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST
        log.info('PluginsHandler.read request fulfilled')
        return plugin_list


class MetaDataTemplateHandler(BaseHandler):
    """
    Read / Create / Delete Meta Data Templates
    """
    allowed_methods = ('GET', 'POST', 'DELETE')

    """
    docrule_id is used for read
    mdt_id is used for delete
    """

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required('api')) # FIXME: Should be more granular permissions
    def create(self, request):

        if not request.user.is_authenticated():
            log.error('MetaDataTemplateHandler.create attempted with unauthenticated user.')
            return rc.FORBIDDEN

        # Catch post with no payload
        try:
            mdt = request.POST['mdt']
        except KeyError, e:
            log.error('MetaDataTemplateHandler.create attempted with no payload.')
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST

        # Catch improper MDT payload
        try:
            data = json.loads(str(mdt))
        except ValueError, e:
            log.error('MetaDataTemplateHandler.create attempted with bad json payload. %s' % e)
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST

        # Try and validate MDT
        manager = MetaDataTemplateManager()
        if not manager.validate_mdt(mdt):
            return rc.BAD_REQUEST

        # Store MDT
        result = manager.store(data)
        if result is False:
            log.error('MetaDataTemplateHandler.create error occurred on store.')
            return rc.DUPLICATE_ENTRY

        log.info('MetaDataTemplateHandler.create request fulfilled.')
        return result

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required('api')) # FIXME: Should be more granular permissions
    def read(self, request):
        if not request.user.is_authenticated():
            log.error('MetaDataTemplateHandler.read attempted with unauthenticated user.')
            return rc.FORBIDDEN

        # Catch get with no payload
        try:
            docrule_id = request.GET['docrule_id'] # FIXME: Need to standardize the arguments / nomenclature
        except KeyError, e:
            log.error('MetaDataTemplateHandler.read attempted with no payload.')
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST

        log.debug('MetaDataTemplateHandler.read underway with docrule_id %s.' % docrule_id)

        # Retrieve MDT from docrule_id
        manager = MetaDataTemplateManager()
        result = manager.get_mdts_for_docrule(docrule_id)

        log.debug('MetaDataTemplateHandler.read result: %s.' % result)

        if not result:
            log.error('MetaDataTemplateHandler.read error with docrule_id %s' % docrule_id)
            return rc.NOT_FOUND

        log.info('MetaDataTemplateHandler.read request fulfilled for docrule_id %s' % docrule_id)
        return result

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required('api')) # FIXME: Should be more granular permissions
    def delete(self, request):
        if not request.user.is_authenticated():
            log.error('MetaDataTemplateHandler.delete attempted with unauthenticated user.')
            return rc.FORBIDDEN

        # Catch improper mdt_id in request
        try:
            mdt_id = request.REQUEST.get('mdt_id')
            log.info('MetaDataTemplateHandler.delete attempted with valid request %s' % mdt_id)
        except KeyError, e:
            log.error('MetaDataTemplateHandler.delete attempted with invalid request %s' % e)
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST

        # Catch mdt_id is None
        if mdt_id is None:
            return rc.BAD_REQUEST

        # Delete MDT via Manager
        manager = MetaDataTemplateManager()
        result = manager.delete_mdt(mdt_id)
        if result is True:
            log.info('MetaDataTemplateHandler.delete request fulfilled for mdt_id %s' % mdt_id)
            return rc.DELETED
        else:
            log.info('MetaDataTemplateHandler.delete request not found for mdt_id %s' % mdt_id)
            return rc.NOT_FOUND


class ParallelKeysHandler(BaseHandler):
    """
    Read / Create / Delete Meta Data Templates
    """
    allowed_methods = ('GET', 'OPTIONS')

    """
    docrule is used for indexing
    mdt_ids is used for search, or when docrule is uncertain
    """

    def read(self, request):

        if not request.user.is_authenticated():
            log.error('ParallelKeysHandler.read attempted with unauthenticated user.')
            return rc.FORBIDDEN

        mdts_ids = None
        docrule_id = request.GET.get('docrule', None)
        key_name = request.GET.get('key', None)
        autocomplete_req = request.GET.get('req', None)

        if not docrule_id:
            mdts_ids = request.GET.get('mdt_ids', None)
            if not mdts_ids:
                return rc.BAD_REQUEST

        if (docrule_id or mdts_ids) and key_name and autocomplete_req:
            manager = MetaDataTemplateManager()
            if mdts_ids:
                doc_mdts = manager.get_mdts_by_name(mdts_ids)
            else:
                doc_mdts = manager.get_mdts_for_docrule(docrule_id)
            resp = process_pkeys_request(docrule_id, key_name, autocomplete_req, doc_mdts)
            return resp
        else:
            return rc.NOT_FOUND


class ThumbnailsHandler(BaseHandler):
    """Work with thumbnails of files"""
    allowed_methods = ('GET', )

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    def read(self, request, code):

        if not request.user.is_authenticated():
            log.error('ThumbnailsHandler.read attempted with unauthenticated user.')
            return rc.FORBIDDEN

        processor = DocumentProcessor()
        doc = processor.read(code, options={'user': request.user, 'thumbnail': True})
        if not processor.errors:
            return DMSObjectResponse(doc, thumbnail=True)
        else:
            return rc.NOT_FOUND

