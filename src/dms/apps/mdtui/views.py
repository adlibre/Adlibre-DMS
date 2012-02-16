"""
Module: MDT UI Views
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

from django.core.urlresolvers import reverse, resolve
from django.shortcuts import render_to_response, HttpResponseRedirect, get_object_or_404
from django.template import RequestContext, loader


def search(request, step=None, template='mdtui/search.html'):

    # Hack to make the navigation work for testing the templates
    if request.POST:
        step = str(int(step) + 1)
        return HttpResponseRedirect(reverse('mdtui-search-' + step))

    context = { 'step': step, }
    return render_to_response(template, context, context_instance=RequestContext(request))


def indexing(request, step=None, template='mdtui/indexing.html'):

#    if request.REQUEST.get('step'):
#        step = request.REQUEST.get('step')

    # Hack to make the navigation work for testing the templates
    if request.POST:
        step = str(int(step) + 1)
        return HttpResponseRedirect(reverse('mdtui-index-' + step))

    context = { 'step': step, }
    return render_to_response(template, context, context_instance=RequestContext(request))