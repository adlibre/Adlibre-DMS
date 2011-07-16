"""
Module: Piston API Handlers
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

import json, os

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from piston.handler import BaseHandler
from piston.utils import rc

from document_manager import DocumentManager
from dms_plugins import models

class BaseFileHandler(BaseHandler):
    def get_file_info(self, request):
        filename = request.GET.get('filename')
        if not filename:
            raise ValueError("No filename")
        document_name, extension = os.path.splitext(filename)
        extension = extension.strip(".")

        revision = request.GET.get("r", None) # TODO: TestMe
        hashcode = request.GET.get("h", None) # TODO: TestMe
        
        return document_name, extension, revision, hashcode

class FileInfoHandler(BaseFileHandler):
    allowed_methods = ('GET',)
    
    def read(self, request):
        try:
            document_name, extension, revision, hashcode = self.get_file_info(request)
        except ValueError:
            return rc.BAD_REQUEST
        manager = DocumentManager()
        document = manager.retrieve(request, document_name, hashcode = hashcode, revision = revision, only_metadata = True, 
                        extension = extension)
        mapping = manager.get_plugin_mapping(document)
        if manager.errors:
            return rc.BAD_REQUEST
        info = document.get_dict()
        info['document_list_url'] = reverse('ui_document_list', kwargs = {'id_rule': mapping.pk})
        response = HttpResponse(json.dumps(info))
        return response

class FileHandler(BaseFileHandler):
    allowed_methods = ('GET', 'POST', 'DELETE',)

    def read(self, request):
        try:
            document_name, extension, revision, hashcode = self.get_file_info(request)
        except ValueError:
            return rc.BAD_REQUEST
        manager = DocumentManager()
        mimetype, filename, content = manager.get_file(request, document_name, hashcode, extension, revision = revision)
        if manager.errors:
            return rc.BAD_REQUEST
        response = HttpResponse(content, mimetype=mimetype)
        response["Content-Length"] = len(content)
        response['Content-Disposition'] = 'filename=%s' % filename

        return response


    def create(self, request):
        document, extension = os.path.splitext(request.FILES['file'].name)
        extension = extension.strip(".")

        revision = request.GET.get("r", None) # TODO: TestMe

        manager = DocumentManager()
        document = manager.store(request, request.FILES['file'])
        if len(manager.errors) > 0:
            return rc.BAD_REQUEST
        return document.get_filename()

    def delete(self, request):
        filename = request.GET.get('filename')
        document, extension = os.path.splitext(filename)
        extension = extension.strip(".")

        revision = request.GET.get("r", None) # TODO: TestMe

        manager = DocumentManager()
        manager.delete_file(request, document, revision = revision)
        if len(manager.errors) > 0:
            return rc.BAD_REQUEST
        return rc.DELETED

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
                if finish:
                    finish = int(finish)
            except ValueError:
                pass
            file_list = manager.get_file_list(mapping, start, finish, order)
            for item in file_list:
                item.update({   'ui_url': reverse('ui_document', kwargs = {'document_name': item['name']}),
                                'rule': mapping.get_name(),
                            })
            return file_list
        except Exception:
            raise
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
            from doc_codes import DoccodeManagerInstance
            doccode = DoccodeManagerInstance.find_for_string(document)
            if doccode:
                try:
                    mapping = models.DoccodePluginMapping.objects.get(doccode = doccode.get_id())
                except models.DoccodePluginMapping.DoesNotExist:
                    return rc.BAD_REQUEST
                manager = DocumentManager()
                rev_count = manager.get_revision_count(document, mapping)
                if rev_count <= 0: #document without revisions is broken
                    return rc.BAD_REQUEST
                return rev_count
            else:
                return rc.BAD_REQUEST
        except Exception, e:
            return rc.BAD_REQUEST

class RulesHandler(BaseHandler):
    allowed_methods = ('GET','POST')

    verbose_name = 'rule'
    verbose_name_plural = 'rules'

    def read(self, request):
        manager = DocumentManager()
        mappings = manager.get_plugin_mappings()
        rules = list(map(lambda x: {
                            'doccode': x.get_doccode().get_title(),
                            'id': x.pk,
                            'ui_url': reverse('ui_document_list', kwargs = {'id_rule': x.pk})
                                }, mappings))
        return rules

class RulesDetailHandler(BaseHandler):
    allowed_methods = ('GET','POST')

    fields = ['id', 'name', ('storage_plugins', ('name',)), 
                            ('retrieval_plugins', ('name',)), 
                            ('removal_plugins', ('name',))]

    verbose_name = 'rule'
    verbose_name_plural = 'rules'

    def read(self, request, id_rule):
        manager = DocumentManager()
        try:
            mapping = manager.get_plugin_mapping_by_kwargs(pk = id_rule)
        except Exception:
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
        except Exception:
            if settings.DEBUG:
                raise
            else:
                return rc.BAD_REQUEST
        return plugin_list