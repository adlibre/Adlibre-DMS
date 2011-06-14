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
    allowed_methods = ('GET','POST','DELETE',)

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
        mapping = get_object_or_404(models.DoccodePluginMapping, pk = id_rule)
        manager = DocumentManager()
        file_list = manager.get_file_list(mapping)
        return file_list

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

# OLD CODE
"""
class RulesHandler(BaseHandler):
    allowed_methods = ('GET','POST')

    verbose_name = 'rule'
    verbose_name_plural = 'rules'

    def read(self, request):
        try:
            d = DmsBase()
        except DmsException, (e):
            return rc.BAD_REQUEST
        else:
            rules = []
            for rule in d.get_rules():
                readable_rule = {
                    'doccode' : rule.get_doccode().name,
                    'id' : rule.id
                }
                rules.append(readable_rule)
            return rules


# TODO: Add a test for this.
class RulesDetailHandler(BaseHandler):
    allowed_methods = ('GET','POST')
    fields = ('id', 'doccode', 'storage', 'active','validators', 'securities')

    verbose_name = 'rule'
    verbose_name_plural = 'rules'

    def read(self, request, id_rule):

        try:
            d = DMS(id_rule)
        except DmsException, (e):
            return rc.BAD_REQUEST
        else:
            return d.get_rule_details()


class PluginsHandler(BaseHandler):
    allowed_methods = ('GET','POST')

    verbose_name = 'plugin'
    verbose_name_plural = 'plugins'

    def read(self, request):

        try:
            d = DmsBase()
        except DmsException, (e):
            return rc.BAD_REQUEST
        else:
            return d.get_plugins()
"""