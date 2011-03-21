import os

from django.http import HttpResponse

from piston.handler import BaseHandler
from piston.utils import rc

from fileshare.models import Rule
from fileshare.models import (available_validators, available_doccodes,
    available_storages, available_securities)
from fileshare.converter import FileConverter


class FileHandler(BaseHandler):
    allowed_methods = ('GET','POST','DELETE',)

    # TODO: these methods needs security wrapper.
    # TODO: These methods need to support version, versions.
    
    def read(self, request):
        filename = request.GET.get('filename')
        document, extension = os.path.splitext(filename)
        extension = extension.strip(".")
        rule = Rule.objects.match(document)
        storage = rule.get_storage()
        filepath = storage.get(document)
        if not filepath:
            return HttpResponse("No file match")
        new_file = FileConverter(filepath, extension)
        mimetype, content = new_file.convert()

        response = HttpResponse(content, mimetype=mimetype)
        response["Content-Length"] = len(content)
        return response


    def create(self, request):
        document, extension = os.path.splitext(request.FILES['filename'].name)
        extension = extension.strip(".")
        rule = Rule.objects.match(document)
        if rule:
            storage = rule.get_storage()
            storage.store(request.FILES['filename'])
            return rc.CREATED
        else:
            return rc.BAD_REQUEST


    def delete(self, request):
        filename = request.GET.get('filename')
        document, extension = os.path.splitext(filename)
        extension = extension.strip(".")
        rule = Rule.objects.match(document)
        if rule:
            storage = rule.get_storage()
            storage.delete(filename)
            return rc.DELETED
        else:
            return rc.BAD_REQUEST


# FIXME: As per local.py, there is
# dependenc on rules, which I don't
# really like, but might not be avoidable
class FileListHandler(BaseHandler):
    allowed_methods = ('GET','POST')

    def read(self, request, id_rule):
        rule = Rule.objects.get(id=id_rule)
        file_list = rule.get_storage().get_list(id_rule)
        return file_list


# How many files do we have for a document.
class RevisionCountHandler(BaseHandler):
    allowed_methods = ('GET','POST')

    def read(self, request, document):        
        document, extension = os.path.splitext(document)
        extension = extension.strip(".")
        rule = Rule.objects.match(document)

        if rule:
            storage = rule.get_storage()
            return storage.get_revision_count(document)
        else:
            return rc.BAD_REQUEST


class RulesHandler(BaseHandler):
    allowed_methods = ('GET','POST')

    verbose_name = 'rule'
    verbose_name_plural = 'rules'

    def read(self, request):
        rules = []
        for rule in Rule.objects.all():
            readable_rule = {
                'doccode' : rule.get_doccode().name,
                'id' : rule.id
            }
            rules.append(readable_rule)
        return rules


class RulesDetailHandler(BaseHandler):
    allowed_methods = ('GET','POST')
    fields = ('id', 'doccode', 'storage', 'active','validators', 'securities')

    verbose_name = 'rule'
    verbose_name_plural = 'rules'

    def read(self, request, id_rule):
        rule = Rule.objects.get(id=id_rule)
        rule.doccode = rule.get_doccode().name
        rule.storage = rule.get_storage().name
        securities = rule.get_securities()
        rule.securities = ",".join([security.name for security in securities])
        validators = rule.get_validators()
        rule.validators = ",".join([validator.name for validator in validators])
        return rule


class PluginsHandler(BaseHandler):
    allowed_methods = ('GET','POST')

    verbose_name = 'plugin'
    verbose_name_plural = 'plugins'

    def read(self, request):
        plugins = []
        for plugin in available_doccodes():
            plugins.append(plugin)
        for plugin in available_validators():
            plugins.append(plugin)
        for plugin in available_securities():
            plugins.append(plugin)
        return plugins

