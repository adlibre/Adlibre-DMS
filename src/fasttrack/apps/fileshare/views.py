import mimetypes
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.utils.translation import ugettext_lazy as _
from django.views.generic.simple import direct_to_template
from django.http import Http404

from fileshare.forms import UploadForm
from fileshare.models import FileShare

def index(request, template_name='fileshare/index.html', extra_context={}):

    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
    extra_context['form'] = form    
    extra_context['file_list'] = FileShare.objects.all()
    return direct_to_template(request,
                              template_name,
                              extra_context=extra_context)


def get_file(request, hashcode, filename):
    obj = get_object_or_404(FileShare, hashcode=hashcode)
    fullpath = obj.sharefile.file.name
    statobj = os.stat(fullpath)
    contents = open(fullpath, 'rb').read()
    mimetype = mimetypes.guess_type(fullpath)[0] or 'application/octet-stream'
    response = HttpResponse(contents, mimetype=mimetype)
    response["Content-Length"] = len(contents)
    return response
