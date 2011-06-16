"""
Module: Piston API Handlers
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

import os

from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from piston.handler import BaseHandler
from piston.utils import rc

from document_manager import DocumentManager
from dms_plugins import models

class FileHandler(BaseHandler):
    allowed_methods = ('GET', 'POST', 'DELETE',)

    def read(self, request):
        filename = request.GET.get('filename')
        document, extension = os.path.splitext(filename)
        request_extension = extension.strip(".")

        revision = request.GET.get("r", None) # TODO: TestMe
        hashcode = request.GET.get("h", None) # TODO: TestMe

        manager = DocumentManager()
        mimetype, filename, content = manager.get_file(request, document, hashcode, extension)
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
            file_list = manager.get_file_list(mapping)
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
                mapping = get_object_or_404(models.DoccodePluginMapping, doccode = doccode.get_id())
                manager = DocumentManager()
                rev_count = manager.get_revision_count(document, mapping)
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
        rules = list(map(lambda x: {'doccode': x.get_doccode().get_title(),
                                'id': x.pk
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