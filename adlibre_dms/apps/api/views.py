"""Module: Django REST framewor API Handlers

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011, 2014
License: See LICENSE for license information
"""

import json
import os
import logging
import traceback
from StringIO import StringIO

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils.decorators import method_decorator

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import FileUploadParser, MultiPartParser, FormParser
from rest_framework.decorators import renderer_classes
from rest_framework.renderers import JSONPRenderer, JSONRenderer
from rest_framework.reverse import reverse as rest_reverse

from api.decorators.auth import logged_in_or_basicauth
from api.decorators.group_required import group_required
from core.document_processor import DocumentProcessor
from core.parallel_keys import process_pkeys_request
from core.errors import DmsException
from core.http import DMSObjectResponse, DMSOBjectRevisionsData
from dms_plugins.operator import PluginsOperator
from dms_plugins.models import DoccodePluginMapping
from mdt_manager import MetaDataTemplateManager
from dms_plugins.workers.info.tags import TagsPlugin
from models import API_GROUP_NAME

from mdtui.security import list_permitted_docrules_qs


log = logging.getLogger('dms.api.handlers')

AUTH_REALM = 'Adlibre DMS'


class BaseFileHandler(APIView):
    """Typical request parsing task handler"""

    def _get_info(self, request):
        revision = request.QUERY_PARAMS.get('r', None)
        hashcode = request.QUERY_PARAMS.get('h', None)
        extra = request.QUERY_PARAMS
        log.debug('BaseFileHandler._get_info returned: %s : %s : %s.' % (revision, hashcode, extra))
        return revision, hashcode, extra


class FileHandler(BaseFileHandler):
    """CRUD Methods for documents

    GET method file API negotiation:
    Main request to this URL supports getting a specific DMS code with or without extension.
    To request a file from DMS call this API hook with specifying a code after the final hook slash:
    e.g. to request a DMS file with code AAA-0001 it is required to call:
    /[this url]/AAA-0001

    It is possible to specify a format the file is required from DMS.
    e.g. to request a code AAA-0001 from DMS with extension .pdf enter the following:
    /[this url]/AAA-0001.pdf
    This extension is highly optional. DMS will make attempt to convert a file into suggested format.
    It can only happen if configured so.
    It is impossible to force DMS to name the file into unsupported or not configured format.

    GET additional parameters:
    @param r: is used for specifying exact revision of the requested document.
              Omitting this parameter returns the latest revision of the document.
    @param h: hashcode of requested dcoument. In case ve have a hashcode stamp for it.


    POST method file API negotiation:
    POST method is used to create new documents in the system only.
    It is impossible to update existing documents with POST. PUT request supports that.
    POST filename should be provided based on the same pattern as for get.

    Filename without extension is counted as code. Tt will be stored under new file and uncategorized code,
    in case file name does not correspond to any code.

    PUT is a method of modifying data in DMS.
    It is suitable to do most of the indexing logic through PUT request.
    To call a PUT you need to have a document to update. So only possible way is specifying a code.

    PUT parameters are wide enough and may be changed in near future:

    @param tag_string: is a tags, separated with comas string to update for using SQL tags plugin.
    @param remove_tag_string': is a remove tags string to update for using SQL tags plugin.
    @param new_name: is a name of file to be updated
    @param new_type: is an id of new document type
    @param new_indexes: is a set of indexes in special format that used to be updated
    @param update_file: is a file to store against that code. Update file creates new file revision.


    DELETE is a call to remove a code from DMS.
    It is possible to remove entire file or either particular file revision.

    @param r: to remove a revision number specify this parameter.

    """
    allowed_methods = ('GET', 'POST', 'DELETE', 'PUT')
    parser_classes = (FileUploadParser, MultiPartParser, FormParser)

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required(API_GROUP_NAME))  # FIXME: Should be more granular permissions
    def post(self, request, code, suggested_format=None):
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        processor = DocumentProcessor()
        options = {
            'user': request.user,
            'barcode': code,
        }
        document = processor.create(uploaded_file, options)
        if len(processor.errors) > 0:
            log.error('FileHandler.create manager errors: %s' % processor.errors)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        log.info('FileHandler.create request fulfilled for %s' % document.get_filename())
        return Response(status=status.HTTP_201_CREATED)

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required(API_GROUP_NAME))  # FIXME: Should be more granular permissions
    def get(self, request, code=None, suggested_format=None):
        if not code:
            return Response([])
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
            if not document.docrule in user_permissions:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        if processor.errors:
            log.error('FileHandler.read manager errors: %s' % processor.errors)
            return Response(status=status.HTTP_404_NOT_FOUND)
        if document.marked_deleted:
            log.error('FileHandler.read request to marked deleted document: %s' % code)
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            response = DMSObjectResponse(document)
            log.info('FileHandler.read request fulfilled for code: %s, options: %s' % (code, options))
        return response

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required(API_GROUP_NAME))  # FIXME: Should be more granular permissions
    def put(self, request, code, suggested_format=None):
        """Used to work with "update" sequence of DMS code.

        to update a code you need to send a PUT request here.
        PUT must contain:

        @param code: the DMS "code" of file to be updated. e.g.: ADL-0001
        @param suggested_format: format of file for code to be updated. To have ability to post files in certain format.
        """
        context = {'request': request}
        conten_type = request.content_type
        uploaded_obj = None
        if 'multipart/form-data' in conten_type:
            # We have a file upload encoded with multipart/form-data
            file_content = StringIO(request.body)
            parser = MultiPartParser()
            dnf = parser.parse(file_content, media_type=conten_type, parser_context=context)
            extra = dnf.data
            if 'file' in dnf.files:
                uploaded_obj = dnf.files['file']
        else:
            extra = request.QUERY_PARAMS
        # TODO: do we require SQL tagging logic in this API call?
        sql_tag_string = extra.get('tag_string', None)
        sql_remove_tag_string = extra.get('remove_tag_string', None)
        new_name = extra.get('new_name', None)
        new_type = extra.get('new_type', None)
        index_data = extra.get('indexing_data', None)
        if index_data:
            index_data = json.loads(index_data)
        processor = DocumentProcessor()
        options = {
            'tag_string': sql_tag_string,
            'remove_tag_string': sql_remove_tag_string,
            'extension': suggested_format,
            'new_name': new_name,
            'new_type': new_type,
            'new_indexes': index_data,
            'update_file': uploaded_obj,
            'user': request.user,
        }
        document = processor.update(code, options)
        if len(processor.errors) > 0:
            log.error('FileHandler.update manager errors %s' % processor.errors)
            if settings.DEBUG:
                print processor.errors
                raise Exception('FileHandler.update manager errors')
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        log.info('FileHandler.update request fulfilled for code: %s, extension: %s'
                 % (code, suggested_format))
        resp = DMSOBjectRevisionsData(document).data
        return Response(resp, status=status.HTTP_200_OK)

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required(API_GROUP_NAME))  # FIXME: Should be more granular permissions
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
            return Response(status=status.HTTP_400_BAD_REQUEST)
        log.info(
            'FileHandler.delete request fulfilled for code: %s, format: %s, rev: %s, hash: %s.'
            % (code, suggested_format, revision, hashcode)
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class OldFileHandler(BaseFileHandler):
    """Deprecated Files handler logic"""
    allowed_methods = ('GET', 'POST')

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required(API_GROUP_NAME))
    def post(self, request, code, suggested_format=None):
        if 'file' in request.FILES:
            uploaded_file = request.FILES['file']
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        processor = DocumentProcessor()
        options = {
            'user': request.user,
            'barcode': code,
        }
        if uploaded_file.size == 0:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        document = processor.create(uploaded_file, options)
        if len(processor.errors) > 0:
            log.error('OldFileHandler.create errors: %s' % processor.errors)
            error = processor.errors[0]
            if error.__class__.__name__ in ['unicode', 'str']:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            if error.code == 409:
                new_processor = DocumentProcessor()
                options['update_file'] = uploaded_file
                document = new_processor.update(code, options)
                if len(new_processor.errors) > 0:
                    return Response(status=status.HTTP_400_BAD_REQUEST)
        log.info('OldFileHandler.create request fulfilled for %s' % document.get_filename())
        return Response(document.get_filename(), status=status.HTTP_200_OK)

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required(API_GROUP_NAME))
    def get(self, request, code, suggested_format=None):
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
            if not document.docrule in user_permissions:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        if processor.errors:
            log.error('OldFileHandler.read manager errors: %s' % processor.errors)
            return Response(status=status.HTTP_404_NOT_FOUND)
        if document.marked_deleted:
            log.error('OldFileHandler.read request to marked deleted document: %s' % code)
            return Response(status=status.HTTP_404_NOT_FOUND)
        else:
            response = DMSObjectResponse(document)
            log.info('OldFileHandler.read request fulfilled for code: %s, options: %s' % (code, options))
        return response


class FileInfoHandler(BaseFileHandler):
    """Returns document file info data"""
    allowed_methods = ('GET',)

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required(API_GROUP_NAME))  # FIXME: Should be more granular permissions
    def get(self, request, code, suggested_format=None):
        revision, hashcode, extra = self._get_info(request)
        only_metadata = True
        indexing_data = extra.get('indexing_data', None)
        # Security measure for variable
        if indexing_data:
            indexing_data = True
            only_metadata = False
        processor = DocumentProcessor()
        options = {
            'revision': revision,
            'hashcode': hashcode,
            'only_metadata': only_metadata,
            'extension': suggested_format,
            'indexing_data': indexing_data,
            'user': request.user,
        }
        document = processor.read(code, options)
        if document.marked_deleted:
            log.error('FileInfoHandler.read request to marked deleted document: %s' % code)
            return Response(status=status.HTTP_404_NOT_FOUND)
        if processor.errors:
            log.error('FileInfoHandler.read errors: %s' % processor.errors)
            if settings.DEBUG:
                raise Exception('FileInfoHandler.read manager.errors')
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        info = DMSOBjectRevisionsData(document).jsons
        log.info(
            'FileInfoHandler.read request fulfilled for %s, ext %s, rev %s, hash %s'
            % (code, suggested_format, revision, hashcode)
        )
        return Response(info, status=status.HTTP_200_OK)


class FileListHandler(APIView):
    """Provides list of documents to be able to browse via document type rule id."""
    allowed_methods = ('GET', )

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required(API_GROUP_NAME))  # FIXME: Should be more granular permissions
    def get(self, request, id_rule):
        operator = PluginsOperator()
        try:
            mapping = operator.get_plugin_mapping_by_docrule_id(id_rule)
        except DmsException:
            return Response(status=status.HTTP_404_NOT_FOUND)
        start = int(request.GET.get('start', 0))
        finish = request.GET.get('finish', None)
        order = request.GET.get('order', None)
        searchword = request.GET.get('q', None)
        tag = request.GET.get('tag', None)
        filter_date = request.GET.get('created_date', None)
        if finish:
            finish = int(finish)
        file_list = operator.get_file_list(
            mapping,
            start,
            finish,
            order,
            searchword,
            tags=[tag],
            filter_date=filter_date
        )
        for item in file_list:
            document_name = item['name']
            code, suggested_format = os.path.splitext(document_name)
            if not suggested_format:
                api_url = reverse('api_file', kwargs={'code': code, })
            else:
                suggested_format = suggested_format[1:]  # Remove . from file ext
                api_url = reverse('api_file', kwargs={'code': code, 'suggested_format': suggested_format, })
            thumb_url = reverse('api_thumbnail', kwargs={'code': item['name']})
            item.update({
                'ui_url': api_url,
                'thumb_url': thumb_url,
                'rule': mapping.get_name(),
            })
        log.info(
            """FileListHandler.read request fulfilled for:
            start %s, finish %s, order %s, searchword %s, tag %s, filter_date %s."""
            % (start, finish, order, searchword, tag, filter_date)
        )
        return Response(file_list, status=status.HTTP_200_OK)


class TagsHandler(APIView):
    """Provides list of tags for id_rule"""
    allowed_methods = ('GET',)

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required(API_GROUP_NAME))  # FIXME: Should be more granular permissions
    def get(self, request, id_rule):
        # FIXME: Requirement for this whole API hook is wrong.
        # Tags should be got with document metadata. Not with a separate reequest.
        try:
            operator = PluginsOperator()
            mapping = operator.get_plugin_mapping_by_docrule_id(id_rule)
            docrule = mapping.get_docrule()
            tags = TagsPlugin().get_all_tags(docrule=docrule)
            log.info('TagsHandler.read request fulfilled for rule %s' % id_rule)
            return Response(json.dumps(tags), status=status.HTTP_200_OK)
        except Exception, e:  # FIXME
            log.error('TagsHandler.read Exception %s' % e)
            if settings.DEBUG:
                raise
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)


class RevisionCountHandler(APIView):
    """Returns revision count for a document"""
    allowed_methods = ('GET', )

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required(API_GROUP_NAME))  # FIXME: Should be more granular permissions
    def get(self, request, document):
        document, extension = os.path.splitext(document)
        processor = DocumentProcessor()
        document = processor.read(document, options={'revision_count': True, 'user': request.user, })
        rev_count = document.get_revision()
        if rev_count <= 0:
            log.info('RevisionCountHandler.read rev_count %s.' % str(rev_count))
            if settings.DEBUG:
                raise Exception('No document revisions')
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        if processor.errors:
            log.error('RevisionCountHandler.read Exception %s' % processor.errors[0])
            return Response(status=status.HTTP_400_BAD_REQUEST)
        log.info('RevisionCountHandler.read request fulfilled for document %s, extension %s' % (document, extension))
        return HttpResponse(rev_count)


class RulesHandler(APIView):
    """Returns list of all doc type rules in the system"""
    allowed_methods = ('GET', )

    verbose_name = 'rule'
    verbose_name_plural = 'rules'

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required(API_GROUP_NAME))  # FIXME: Should be more granular permissions
    def get(self, request):
        """Returns list of Document Type Rule <=> Plugins mapping

        @param request: Django request object
        @return: json of document type rules
        """
        doc_types_mappings = DoccodePluginMapping.objects.all()
        rules_json = []
        for rule in doc_types_mappings:
            rules_json.append(
                dict(
                    doccode=rule.get_docrule().get_title(),
                    id=rule.pk,
                )
            )
        log.info('RulesHandler.read request fulfilled')
        return Response(rules_json, status=status.HTTP_200_OK)


class RulesDetailHandler(APIView):
    """Returns detailed information about a doc type rule"""
    allowed_methods = ('GET', )

    fields = [
        'id',
        'name',
        ('before_storage_plugins', ('name',)),
        ('storage_plugins', ('name',)),
        ('before_retrieval_plugins', ('name',)),
        ('before_removal_plugins', ('name',)),
        ('database_storage_plugins', ('name',)),
    ]

    verbose_name = 'rule'
    verbose_name_plural = 'rules'

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required(API_GROUP_NAME))  # FIXME: Should be more granular permissions
    def get(self, request, id_rule):
        """RulesDetailHandler READ method for GET requests

        @param request: is a django request object
        @param id_rule: is an id (PK) of a document type rule we are trying to return
        """
        operator = PluginsOperator()
        try:
            mapping = operator.get_plugin_mapping_by_docrule_id(id_rule)
        except DmsException:
            log.error('RulesDetailHandler.read DmsException: Rule not found. 404')
            if settings.DEBUG:
                raise
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        # Removing mapping key that is not json serializable.
        resp_data = dict(
            active=mapping.active,
            doccode_id=mapping.doccode_id,
            id=mapping.id,
            doccode=mapping.doccode.title,
            before_retrieval_plugins=[plugin.name for plugin in mapping.before_retrieval_plugins.all()],
            storage_plugins=[plugin.name for plugin in mapping.storage_plugins.all()],
            database_storage_plugins=[plugin.name for plugin in mapping.database_storage_plugins.all()],
            before_removal_plugins=[plugin.name for plugin in mapping.before_removal_plugins.all()],
            before_storage_plugins=[plugin.name for plugin in mapping.before_storage_plugins.all()],
        )
        log.info('RulesDetailHandler.read request fulfilled for rule %s' % id_rule)
        return Response(json.dumps(resp_data), status=status.HTTP_200_OK)


class PluginsHandler(APIView):
    """Returns a list of plugins installed in the system"""
    allowed_methods = ('GET', )

    verbose_name = 'plugin'
    verbose_name_plural = 'plugins'

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required(API_GROUP_NAME))  # FIXME: Should be more granular permissions
    def get(self, request):
        operator = PluginsOperator()
        try:
            plugin_list = operator.get_plugin_list()
        except Exception, e:  # FIXME
            log.error('PluginsHandler.read Exception %s' % e)
            if settings.DEBUG:
                raise
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)
        # Removing plugins key that is not json serializable.
        def clean_keys(p):
            if "_state" in p.__dict__:
                del p.__dict__["_state"]
            return p
        p_list = [clean_keys(p).__dict__ for p in plugin_list]
        log.info('PluginsHandler.read request fulfilled')
        return Response(p_list, status=status.HTTP_200_OK)


class MetaDataTemplateHandler(APIView):
    """Read / Create / Delete Meta Data Templates

    @param docrule_id: is used for read
    @param mdt_id: is used for delete

    Example MDT:

    ::

        {
            "docrule_id": "used to assign this to document type rules",
            "description": "<-- description of this metadata template -->",
            "fields": {
                // examples:
                "<-- field number -->":
                     {
                       "type": "string|integer|date",
                       "length": "<--optional-->",
                       "field_name":"<-- field name used in UI -->",
                       "description": "<-- description used in UI -->"
                },
                "1": {
                       "type": "integer",
                       "field_name": "Employee ID",
                       "description": "Unique (Staff) ID of the person"
                },
                "2": {
                       "type": "string",
                       "length": 60,
                       "field_name": "Employee Name",
                       "description": "Name of the person associated with the document"
                }
            },
            // parallel fields mapping
            "parallel": {
                "<-- set id -->": ["<-- first 'field' -->", "<-- second 'field' -->"]
                "1": [ "1", "2"],
            }
        }


    """
    allowed_methods = ('GET', 'POST', 'DELETE')
    parser_classes = (FormParser, MultiPartParser)

    """

    """

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required(API_GROUP_NAME))  # FIXME: Should be more granular permissions
    def post(self, request):
        # Catch post with no payload
        try:
            mdt = request.POST['mdt']
        except KeyError:
            log.error('MetaDataTemplateHandler.create attempted with no payload.')
            if settings.DEBUG:
                raise
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        # Catch improper MDT payload
        try:
            data = json.loads(str(mdt))
        except ValueError, e:
            log.error('MetaDataTemplateHandler.create attempted with bad json payload. %s' % e)
            if settings.DEBUG:
                raise
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        # Try and validate MDT
        manager = MetaDataTemplateManager()
        if not manager.validate_mdt(mdt):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Store MDT
        result = manager.store(data)
        if result is False:
            log.error('MetaDataTemplateHandler.create error occurred on store.')
            return Response(status=status.HTTP_409_CONFLICT)

        log.info('MetaDataTemplateHandler.create request fulfilled.')
        return Response(result, status=status.HTTP_200_OK)

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required(API_GROUP_NAME))  # FIXME: Should be more granular permissions
    def get(self, request):
        # Catch get with no payload
        docrule_id = request.GET.get('docrule_id', None)
        if not docrule_id:
            log.error('MetaDataTemplateHandler.read attempted with no payload.')
            return Response([])

        log.debug('MetaDataTemplateHandler.read underway with docrule_id %s.' % docrule_id)

        # Retrieve MDT from docrule_id
        manager = MetaDataTemplateManager()
        result = manager.get_mdts_for_docrule(docrule_id)

        log.debug('MetaDataTemplateHandler.read result: %s.' % result)

        if not result:
            log.error('MetaDataTemplateHandler.read error with docrule_id %s' % docrule_id)
            return Response(status=status.HTTP_404_NOT_FOUND)

        log.info('MetaDataTemplateHandler.read request fulfilled for docrule_id %s' % docrule_id)
        return Response(result, status=status.HTTP_200_OK)

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    @method_decorator(group_required(API_GROUP_NAME))  # FIXME: Should be more granular permissions
    def delete(self, request):
        body = request.body
        # Catch improper mdt_id in request
        try:
            mdt_id = request.DATA.get('mdt_id')
            log.info('MetaDataTemplateHandler.delete attempted with valid request %s' % mdt_id)
        except KeyError, e:
            log.error('MetaDataTemplateHandler.delete attempted with invalid request %s' % e)
            if settings.DEBUG:
                raise
            else:
                return Response(status=status.HTTP_400_BAD_REQUEST)

        if mdt_id is None:
            if body:
                try:
                    d = json.loads(body)
                    mdt_id = d['mdt_id']
                except:
                    log.error('MetaDataTemplateHandler.delete attempted with invalid request %s' % body)
                    return Response(status=status.HTTP_400_BAD_REQUEST)

        # Catch mdt_id is None
        if mdt_id is None:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        # Delete MDT via Manager
        manager = MetaDataTemplateManager()
        result = manager.delete_mdt(mdt_id)
        if result is True:
            log.info('MetaDataTemplateHandler.delete request fulfilled for mdt_id %s' % mdt_id)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            log.info('MetaDataTemplateHandler.delete request not found for mdt_id %s' % mdt_id)
            return Response(status=status.HTTP_404_NOT_FOUND)


@renderer_classes((JSONPRenderer, JSONRenderer))
class ParallelKeysHandler(APIView):
    """Read parallel keys for autocomplete

    @param docrule: is used for indexing
    @param mdt_ids: is used for search, or when docrule is uncertain
    """
    allowed_methods = ('GET', 'OPTIONS')

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    def get(self, request):

        if not request.user.is_authenticated():
            log.error('ParallelKeysHandler.read attempted with unauthenticated user.')
            return Response(status=status.HTTP_401_UNAUTHORIZED)

        mdts_ids = None
        docrule_id = request.GET.get('docrule', None)
        key_name = request.GET.get('key', None)
        autocomplete_req = request.GET.get('req', None)

        if not docrule_id:
            mdts_ids = request.GET.get('mdt_ids', None)
            if not mdts_ids:
                return Response([], status=status.HTTP_400_BAD_REQUEST)

        if (docrule_id or mdts_ids) and key_name and autocomplete_req:
            manager = MetaDataTemplateManager()
            if mdts_ids:
                doc_mdts = manager.get_mdts_by_name(mdts_ids)
            else:
                doc_mdts = manager.get_mdts_for_docrule(docrule_id)
            resp = process_pkeys_request(docrule_id, key_name, autocomplete_req, doc_mdts)
            return Response(resp)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


class ThumbnailsHandler(APIView):
    """Work with thumbnails of files"""
    allowed_methods = ('GET', )

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    def get(self, request, code):

        # TODO: stabilize by removing try/except here and fixing ALL the possible issues.
        try:
            if not request.user.is_authenticated():
                log.error('ThumbnailsHandler.read attempted with unauthenticated user.')
                return Response(status=status.HTTP_401_UNAUTHORIZED)

            processor = DocumentProcessor()
            doc = processor.read(code, options={'user': request.user, 'thumbnail': True})
            if not processor.errors:
                return DMSObjectResponse(doc, thumbnail=True)
            else:
                return Response(status=status.HTTP_404_NOT_FOUND)
        except:
            log.error('ThumbnailsHandler Error: %s' % traceback.print_exc())
            raise


class VersionHandler(APIView):
    """Api hook to check the DMS work state"""
    allowed_methods = ('GET', )

    @method_decorator(logged_in_or_basicauth(AUTH_REALM))
    def get(self, request):
        return Response(settings.PRODUCT_VERSION, status=status.HTTP_200_OK)


class ApiDocs(APIView):
    """API Root calls list

    Returns named list of API calls to be made.
    """
    allowed_methods = ('GET', )

    def get(self, request, format=None):
        code='testcode'
        urls = {
            'main': rest_reverse('api_main', request=request, format=format),
            'viersion': rest_reverse('api_version', request=request, format=format),
            'api_file': rest_reverse('api_file', kwargs={'code': 'code'}, request=request, format=format),
            'api_file_info': reverse('api_file_info', kwargs={'code': 'code'}),
            'api_file_list': reverse('api_file_list', kwargs={'id_rule': 1}),
            'api_revision_count': reverse('api_revision_count', kwargs={'document': 'code'}),
            'api_rules': rest_reverse('api_rules', request=request, format=format),
            'api_rules_detail': reverse('api_rules_detail', kwargs={'id_rule': '1'}),
            'api_tags': reverse('api_tags', kwargs={'id_rule': '1'}),
            'api_plugins': rest_reverse('api_plugins', request=request, format=format),
            'api_mdt': rest_reverse('api_mdt', request=request, format=format),
            'api_parallel': rest_reverse('api_parallel', request=request, format=format),
            'api_thumbnail': reverse('api_thumbnail', kwargs={'code': 'code'}),
            'api_file_deprecated': reverse('api_file_deprecated', kwargs={'code': 'code'}),
        }
        return Response(urls)
