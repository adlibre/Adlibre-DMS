from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.core.urlresolvers import reverse, resolve
from django.shortcuts import render_to_response, HttpResponseRedirect, get_object_or_404
from django.http import HttpRequest, HttpResponse, Http404
from django.views.generic.simple import direct_to_template
from django.template import RequestContext, loader
from django.contrib.auth.decorators import user_passes_test
from django.contrib.sessions.models import Session
from django.contrib.auth.views import login as login_base
from django.contrib.auth.models import User

def retrieve(request, step, template = 'retrieve.html'):

    context = { 'step': step, }
    return render_to_response(template, context, context_instance=RequestContext(request))


def upload(request, step, template = 'upload.html'):

    context = { 'step': step, }
    return render_to_response(template, context, context_instance=RequestContext(request))