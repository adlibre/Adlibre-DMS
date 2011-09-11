"""
Module: Piston API Handlers
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

import json, os, traceback

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from piston.handler import BaseHandler
from piston.utils import rc

from document_manager import DocumentManager
from dms_plugins import models
from doc_codes import DoccodeManagerInstance

class BaseFileHandler(BaseHandler):
    def get_file_info(self, request):
        filename = request.GET.get('filename')
        if not filename:
            raise ValueError("No filename")
        document_name, extension = os.path.splitext(filename)
        extension = extension.strip(".")

        revision = request.GET.get("r", None)
        hashcode = request.GET.get("h", None)
        
        return document_name, extension, revision, hashcode

class FileInfoHandler(BaseFileHandler):
    allowed_methods = ('GET',)
    
    def read(self, request):
        try:
            document_name, extension, revision, hashcode = self.get_file_info(request)
        except ValueError:
            return rc.BAD_REQUEST
        parent_directory = request.GET.get('parent_directory', None)
        manager = DocumentManager()
        document = manager.retrieve(request, document_name, hashcode = hashcode, revision = revision, only_metadata = True, 
                        extension = extension, parent_directory = parent_directory)
        mapping = manager.get_plugin_mapping(document)
        if manager.errors:
            if settings.DEBUG:
                print "MANAGER ERRORS: %s" % manager.errors
            return rc.BAD_REQUEST
        info = document.get_dict()
        info['document_list_url'] = reverse('ui_document_list', kwargs = {'id_rule': mapping.pk})
        info['tags'] = document.get_tags()
        info['no_doccode'] = document.get_doccode().no_doccode
        response = HttpResponse(json.dumps(info))
        return response

class FileHandler(BaseFileHandler):
    allowed_methods = ('GET', 'POST', 'DELETE', 'PUT')

    def read(self, request):
        try:
            document_name, extension, revision, hashcode = self.get_file_info(request)
        except ValueError:
            if settings.DEBUG:
                raise
            return rc.BAD_REQUEST
        parent_directory = request.GET.get('parent_directory', None)
        manager = DocumentManager()
        try:
            mimetype, filename, content = manager.get_file(request, document_name, hashcode, 
            extension, revision = revision, parent_directory = parent_directory)
        except Exception, e:
            if settings.DEBUG:
                import traceback
                print "Exception: %s" % e
                traceback.print_exc()
                raise
            else:
                return rc.BAD_REQUEST
        if manager.errors:
            print "Manager errors: %s" % manager.errors
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
            return rc.BAD_REQUEST
        return document.get_filename()

    def delete(self, request):
        filename = request.REQUEST.get('filename')
        document, extension = os.path.splitext(filename)
        extension = extension.strip(".")

        revision = request.REQUEST.get("r", None) # TODO: TestMe
        full_filename = request.REQUEST.get('full_filename', None)
        parent_directory = request.GET.get('parent_directory', None)

        manager = DocumentManager()
        try:
            manager.delete_file(request, document, revision = revision, full_filename = full_filename,
                parent_directory = parent_directory, extension = extension)
        except Exception, e:
            import traceback
            traceback.print_exc(e)
            if settings.DEBUG:
                print "Exception: %s" % e
                traceback.print_exc()
                raise
            else:
                return rc.BAD_REQUEST
        if len(manager.errors) > 0:
            print "MANAGER_ERRORS ON DELETE: %s" % manager.errors
            return rc.BAD_REQUEST
        return rc.DELETED

    def update(self, request):
      try:
        try:
            document_name, extension, revision, hashcode = self.get_file_info(request)
        except ValueError:
            return rc.BAD_REQUEST
        parent_directory = request.PUT.get('parent_directory', None)

        tag_string = request.PUT.get('tag_string', None)
        remove_tag_string = request.PUT.get('remove_tag_string', None)

        new_name = request.PUT.get('new_name', None)

        manager = DocumentManager()
        if new_name:
            document = manager.rename(request, document_name, new_name, extension, parent_directory = parent_directory)
        else:
            document = manager.update(request, document_name, tag_string = tag_string, remove_tag_string = remove_tag_string,
                                    parent_directory = parent_directory, extension = extension)
        if len(manager.errors) > 0:
            return rc.BAD_REQUEST
        return HttpResponse(json.dumps( document.get_dict() ))
      except Exception, e:
        if settings.DEBUG:
            print "Exception: %s" % e
            traceback.print_exc()
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
            except ValueError:
                pass
            file_list = manager.get_file_list(mapping, start, finish, order, searchword, tags = [tag],
                                                filter_date = filter_date)
            for item in file_list:
                ui_url = reverse('ui_document', kwargs = {'document_name': item['name']})
                if 'directory' in item.keys():
                    ui_url += "?parent_directory=" + item['directory']
                item.update({   'ui_url': ui_url,
                                'rule': mapping.get_name(),
                            })
            return file_list
        except Exception:
            if settings.DEBUG:
                import traceback
                traceback.print_exc()
                raise
            else:
                return rc.BAD_REQUEST

class TagsHandler(BaseHandler):
    allowed_methods = ('GET',)

    def read(self, request, id_rule):
        try:
            manager = DocumentManager()
            mapping = manager.get_plugin_mapping_by_kwargs(pk = id_rule)
            tags = manager.get_all_tags(doccode = mapping.get_doccode())
            return map(lambda x: x.name, tags)
        except Exception:
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
            doccode = DoccodeManagerInstance.find_for_string(document)
            if doccode:
                try:
                    mapping = models.DoccodePluginMapping.objects.get(doccode = doccode.get_id())
                except models.DoccodePluginMapping.DoesNotExist:
                    raise
                manager = DocumentManager()
                rev_count = manager.get_revision_count(document, mapping)
                if rev_count <= 0: #document without revisions is broken
                    raise
                return rev_count
            else:
                raise Exception("No Doccode")
        except Exception, e:
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
                            'doccode': x.get_doccode().get_title(),
                            'id': x.pk,
                            'ui_url': reverse('ui_document_list', kwargs = {'id_rule': x.pk})
                                }, mappings))
        return rules

class RulesDetailHandler(BaseHandler):
    allowed_methods = ('GET','POST')

    fields = ['id', 'name', ('before_storage_plugins', ('name',)), 
                            ('storage_plugins', ('name',)), 
                            ('before_retrieval_plugins', ('name',)), 
                            ('before_removal_plugins', ('name',))]

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
