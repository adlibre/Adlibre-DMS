"""
Module: Metadata Template UI Views
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

from django.core.urlresolvers import reverse, resolve
from django.http import HttpResponse
from django.shortcuts import render_to_response, HttpResponseRedirect, get_object_or_404
from django.template import RequestContext, loader
from forms import DocumentIndexForm, DocumentTypeSelectForm
from forms_representator import get_mdts_for_docrule, render_fields_from_docrules
from forms import DOCRULE_CHOICES

INDEXING_ERROR_STRINGS = {
    1:'{"status": "Error. You have not selected Doccument Type Rule."}'
}


def search(request, step=None, template='mdtui/search.html'):

    # Hack to make the navigation work for testing the templates
    if request.POST:
        step = str(int(step) + 1)
        return HttpResponseRedirect(reverse('mdtui-search-' + step))

    context = { 'step': step, }
    return render_to_response(template, context, context_instance=RequestContext(request))


def indexing(request, step=None, template='mdtui/indexing.html'):
    # initial data (if no steps yet made)
    context = {}
    form = DocumentTypeSelectForm()
#    if request.REQUEST.get('step'):
#        step = request.REQUEST.get('step')

    # Hack to make the navigation work for testing the templates
    if request.POST:
        step = str(int(step) + 1)
        if step == "2":
            form = DocumentTypeSelectForm(request.POST)
            # TODO: refactor this (unright but quick)
            if form.is_valid():
                try:
                    docrule = form.data["docrule"]
                except:
                    return HttpResponse(INDEXING_ERROR_STRINGS[1])
                request.session['current_step'] = step
                request.session['docrule_id'] = docrule
                return HttpResponseRedirect(reverse('mdtui-index-' + step))
            # else: return form on current step with errors
        if step == "3":
            form=initDocumentIndexForm(request)
            if form.validation_ok():
                secondary_indexes = {}
                for key, field in form.fields.iteritems():
                    try:
                        # for native form fields
                        secondary_indexes[field.field_name] = form.data[unicode(key)]
                    except:
                        # for dynamical form fields
                        secondary_indexes[key] = form.data[unicode(key)]
                print secondary_indexes
                if secondary_indexes:
                    request.session["document_keys_dict"] = secondary_indexes

    else:
        if step == "1":
            form = DocumentTypeSelectForm()
        if step == "2":
            form=initDocumentIndexForm(request)
            
    context.update( { 'step': step,
                      'form': form,
                      'document_keys': request.session["document_keys_dict"]
                    })
    return render_to_response(template, context, context_instance=RequestContext(request))

def initDocumentIndexForm(request):
        """
        DocumentIndexForm initialization for different purposes HELPER.
        in case of GET returns an empty base form,
        in case of POST returns populated (from request) form instance.
        in both cases form is rendered with additional (MDT's defined) fields
        """
        try:
            docrule = request.session['docrule_id']
        except:
            # This error only should appear if something breaks
            return HttpResponse(INDEXING_ERROR_STRINGS[1])
        details = get_mdts_for_docrule(request.session['docrule_id'])

        form = DocumentIndexForm()
        if not details == 'error':
            # MDT's exist for ths docrule adding fields to form
            fields = render_fields_from_docrules(details)
            #print fields
            if fields:
                form.setFields(fields)
        if request.POST:
            form.setData(request.POST)
        return form