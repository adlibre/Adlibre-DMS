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

from fileshare.forms import UploadForm, SettingForm
from fileshare.models import (FileShare, FileShareSetting, available_validators,
    available_splitters, get_storage, get_splitter)


def index(request, template_name='fileshare/index.html', extra_context={}):
    try:
        filesetting = FileShareSetting.objects.get(id=1)
    except:
        return HttpResponse("No setting found")
    form = UploadForm(request.POST or None, request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            document = form.files['file']
            storage = get_storage()
            splitter = get_splitter()
            storage.store(document, splitter)
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


def setting(request, template_name='fileshare/setting.html',
                   extra_context={}):

    filesetting, created = FileShareSetting.objects.get_or_create(id=1)
    if request.method == 'POST':
        form = SettingForm(request.POST)
        if form.is_valid():
            filesetting.validator = form.cleaned_data['validator']
            filesetting.splitter = form.cleaned_data['splitter']
            filesetting.storage = form.cleaned_data['storage']
            filesetting.save()
    else:
        data = {
            'splitter' : filesetting.splitter,
            'validator' : filesetting.validator,
            'storage' : filesetting.storage
        }
        form = SettingForm(initial=data)

    extra_context['form'] = form
    return direct_to_template(request, template_name, extra_context=extra_context)

