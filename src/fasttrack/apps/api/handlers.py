import os

from django.http import HttpResponse

from piston.handler import BaseHandler
from piston.utils import rc

from fileshare.models import Rule
from converter import FileConverter


class FileHandler(BaseHandler):
    allowed_methods = ('GET','POST')

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
            return rc.ALL_OK
        return rc.BAD_REQUEST

