"""
Module: Piston API Handlers
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

import json, os, traceback
import logging

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from piston.handler import BaseHandler
from piston.utils import rc

from document_manager import DocumentManager
from dms_plugins import models
from doc_codes.models import DocumentTypeRuleManagerInstance
from mdt_manager import MetaDataTemplateManager


log = logging.getLogger('dms.api.handlers')

class BaseFileHandler(BaseHandler):
    def get_file_info(self, request):

        filename = request.GET.get('filename')

        if not filename:
            log.error('No filename passed to get_file_info')
            raise ValueError('No filename')

        document_name, extension = os.path.splitext(filename)
        extension = extension.strip(".")

        revision = request.GET.get('r', None)
        hashcode = request.GET.get('h', None)

        log.debug('BaseFileHandler.get_file_info returned: %s : %s : %s : %s.' % (document_name, extension, revision, hashcode))
        return document_name, extension, revision, hashcode


class FileInfoHandler(BaseFileHandler):
    allowed_methods = ('GET',)
    
    def read(self, request):
        try:
            document_name, extension, revision, hashcode = self.get_file_info(request)
        except ValueError:
            log.error('FileInfoHandler.read ValueError')
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST
        parent_directory = None
        #parent_directory = request.GET.get('parent_directory', None) # FIXME TODO: this is wrong!!!!!! security breach...
        manager = DocumentManager()
        document = manager.retrieve(request, document_name, hashcode=hashcode, revision=revision, only_metadata=True,
                        extension=extension, parent_directory=parent_directory)
        mapping = manager.get_plugin_mapping(document)
        if manager.errors:
            log.error('FileInfoHandler.read errors: %s' % manager.errors)
            if settings.DEBUG:
                raise Exception('FileInfoHandler.read manager.errors')
            else:
                return rc.BAD_REQUEST
        info = document.get_dict()
        info['document_list_url'] = reverse('ui_document_list', kwargs = {'id_rule': mapping.pk})
        info['tags'] = document.get_tags()
        info['no_doccode'] = document.get_docrule().no_doccode
        response = HttpResponse(json.dumps(info))
        return response


class FileHandler(BaseFileHandler):
    allowed_methods = ('GET', 'POST', 'DELETE', 'PUT')

    def read(self, request):
        try:
            document_name, extension, revision, hashcode = self.get_file_info(request)
        except ValueError:
            log.error('FileHandler.read ValueError')
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST
        parent_directory = None
        #parent_directory = request.GET.get('parent_directory', None) # FIXME TODO: this is wrong!!!!!! security breach...
        manager = DocumentManager()
        try:
            mimetype, filename, content = manager.get_file(request, document_name, hashcode, 
                    extension, revision=revision, parent_directory=parent_directory)
        except Exception, e:
            log.error('FileHandler.read exception %s' % e)
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST
        if manager.errors:
            #print "Manager errors: %s" % manager.errors
            return rc.BAD_REQUEST
        response = HttpResponse(content, mimetype=mimetype)
        response["Content-Length"] = len(content)
        response['Content-Disposition'] = 'filename=%s' % filename
        return response

    def create(self, request):
        document, extension = os.path.splitext(request.FILES['file'].name)
        extension = extension.strip(".")

        manager = DocumentManager()
        document = manager.store(request, request.FILES['file'])
        if len(manager.errors) > 0:
            log.error('FileHandler.create manager errors: %s' % manager.errors)
            return rc.BAD_REQUEST
        return document.get_filename()

    def delete(self, request):
        filename = request.REQUEST.get('filename')
        document, extension = os.path.splitext(filename)
        extension = extension.strip(".")

        revision = request.REQUEST.get("r", None) # TODO: TestMe
        full_filename = request.REQUEST.get('full_filename', None)
        parent_directory = None
        #parent_directory = request.GET.get('parent_directory', None) # FIXME: Why are we allowing this with the API?
        manager = DocumentManager()
        try:
            manager.delete_file(request, document, revision=revision, full_filename=full_filename,
                    parent_directory=parent_directory, extension=extension)
        except Exception, e:
            log.error('FileHandler.delete exception %s' % e)
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST
        if len(manager.errors) > 0:
            if settings.DEBUG:
                print manager.errors
            return rc.BAD_REQUEST
        return rc.DELETED

    def update(self, request):
        try:
            try:
                document_name, extension, revision, hashcode = self.get_file_info(request)
            except ValueError:
                log.error('FileHandler.update ValueError')
                if settings.DEBUG:
                    raise
                else:
                    return rc.BAD_REQUEST
            parent_directory = None
            #parent_directory = request.PUT.get('parent_directory', None)

            tag_string = request.PUT.get('tag_string', None)
            remove_tag_string = request.PUT.get('remove_tag_string', None)

            new_name = request.PUT.get('new_name', None)

            manager = DocumentManager()
            if new_name:
                document = manager.rename(request, document_name, new_name, extension, parent_directory=parent_directory)
            else:
                document = manager.update(request, document_name, tag_string=tag_string, remove_tag_string=remove_tag_string,
                        parent_directory=parent_directory, extension=extension)
            if len(manager.errors) > 0:
                log.error('FileHandler.update manager errors %s' % manager.errors)
                if settings.DEBUG:
                    raise Exception('FileHandler.update manager errors')
                else:
                    return rc.BAD_REQUEST
            return HttpResponse(json.dumps( document.get_dict() ))
        except Exception, e: # FIXME
            log.error('FileHandler.update exception %s' % e)
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST


class FileListHandler(BaseHandler):
    allowed_methods = ('GET','POST')

    def read(self, request, id_rule):
        try:
            manager = DocumentManager()
            mapping = manager.get_plugin_mapping_by_kwargs(pk = id_rule)
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
            file_list = manager.get_file_list(mapping, start, finish, order, searchword, tags=[tag],
                                                filter_date = filter_date)
            for item in file_list:
                ui_url = reverse('ui_document', kwargs = {'document_name': item['name']})
                if 'directory' in item.keys():
                    ui_url += "?parent_directory=" + item['directory']
                item.update({   'ui_url': ui_url,
                                'rule': mapping.get_name(),
                            })
            return file_list
        except Exception, e:
            log.error('FileListHandler.read Exception %s' % e)
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST


class TagsHandler(BaseHandler):
    allowed_methods = ('GET',)

    def read(self, request, id_rule):
        try:
            manager = DocumentManager()
            mapping = manager.get_plugin_mapping_by_kwargs(pk=id_rule)
            tags = manager.get_all_tags(doccode=mapping.get_docrule())
            return map(lambda x: x.name, tags)
        except Exception, e: # FIXME
            log.error('TagsHandler.read Exception %s' % e)
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST

# How many files do we have for a document.
class RevisionCountHandler(BaseHandler):
    allowed_methods = ('GET','POST')

    def read(self, request, document):
        document, extension = os.path.splitext(document)
        try:
            doccode = DocumentTypeRuleManagerInstance.find_for_string(document)
            if doccode:
                try:
                    mapping = models.DoccodePluginMapping.objects.get(doccode=doccode.get_id())
                except models.DoccodePluginMapping.DoesNotExist:
                    log.error('RevisionCountHandler.read DoccodePluginMapping.DoesNotExist exception raised')
                    raise
                manager = DocumentManager()
                rev_count = manager.get_revision_count(document, mapping)
                if rev_count <= 0: # document without revisions is broken FIXME: In future this is ok!
                    log.info('RevisionCountHandler.read rev_count %s.' % str(rev_count))
                    raise Exception('No document revisions')
                return rev_count
            else:
                log.error('RevisionCountHandler.read No Doccode')
                raise Exception('No Doccode')
        except Exception, e: # FIXME
            log.error('RevisionCountHandler.read Exception %s' % e)
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST


class RulesHandler(BaseHandler):
    allowed_methods = ('GET','POST')

    verbose_name = 'rule'
    verbose_name_plural = 'rules'

    def read(self, request):
        manager = DocumentManager()
        mappings = manager.get_plugin_mappings()
        rules = list(map(lambda x: {
                            'doccode': x.get_docrule().get_title(),
                            'id': x.pk,
                            'ui_url': reverse('ui_document_list', kwargs = {'id_rule': x.pk})
                                }, mappings))
        return rules


class RulesDetailHandler(BaseHandler):
    allowed_methods = ('GET','POST')

    fields = ['id', 'name', ('before_storage_plugins', ('name',)), 
                            ('storage_plugins', ('name',)), 
                            ('before_retrieval_plugins', ('name',)), 
                            ('before_removal_plugins', ('name',)),
                            ('database_storage_plugins', ('name',)),]

    verbose_name = 'rule'
    verbose_name_plural = 'rules'

    def read(self, request, id_rule):
        manager = DocumentManager()
        try:
            mapping = manager.get_plugin_mapping_by_kwargs(pk=id_rule)
        except Exception, e: # FIXME
            log.error('RulesDetailHandler.read Exception %s' % e)
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST
        return mapping


class PluginsHandler(BaseHandler):
    allowed_methods = ('GET','POST')

    verbose_name = 'plugin'
    verbose_name_plural = 'plugins'

    def read(self, request):
        manager = DocumentManager()
        try:
            plugin_list = manager.get_plugin_list()
        except Exception, e: # FIXME
            log.error('PluginsHandler.read Exception %s' % e)
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST
        return plugin_list


class MetaDataTemplateHandler(BaseHandler):
    allowed_methods = ('GET','POST', 'DELETE')

    def read(self, request):
        if not request.user.is_authenticated():
            return rc.FORBIDDEN
        try:
            docrule_id = request.GET['docrule_id']
        except Exception, e: # FIXME
            log.error('MetaDataTemplateHandler.read Exception %s' % e)
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST
        manager = MetaDataTemplateManager()
        manager.docrule_id = docrule_id
        mdts_dict = manager.get_mdts_for_docrule(manager.docrule_id)
        if mdts_dict == 'error':
            log.error('MetaDataTemplateHandler.read mdts_dict==error')
            return rc.NOT_FOUND
        return mdts_dict

    def create(self, request):
        if not request.user.is_authenticated():
            log.info('MetaDataTemplateHandler.create unauthenticated user')
            return rc.FORBIDDEN
        try:
            mdt = request.POST['mdt']
            data = json.loads(str(mdt))
        except Exception, e: # FIXME
            log.error('MetaDataTemplateHandler.create Exception %s' % e)
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST
        manager = MetaDataTemplateManager()
        if not manager.validate_mdt(mdt):
            return rc.BAD_REQUEST
        status = manager.store(data)
        if status == 'error':
            log.error('MetaDataTemplateHandler.create status==error')
            return rc.BAD_REQUEST
        return status

    def delete(self, request):
        if not request.user.is_authenticated():
            log.info('MetaDataTemplateHandler.delete unauthenticated user')
            return rc.FORBIDDEN
        try:
            mdt_id = request.REQUEST.get('mdt_id')
        except Exception, e:
            log.error('MetaDataTemplateHandler.delete Exception %s' % e)
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST
        manager = MetaDataTemplateManager()
        mdt_resp = manager.delete_mdt(mdt_id)
        if mdt_resp == 'done':
            return rc.DELETED
        else:
            return rc.NOT_FOUND
