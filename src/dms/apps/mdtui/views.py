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

from couchdbkit import *

from forms import DocumentIndexForm, DocumentTypeSelectForm, DocumentUploadForm
from forms_representator import get_mdts_for_docrule, render_fields_from_docrules
from document_manager import DocumentManager


INDEXING_ERROR_STRINGS = {
    1:'{"status": "Error. You have not selected Doccument Type Rule."}',
    2:'{"status": "Error. You have not entered Document Indexing Data."}',
}


def search(request, step=None, template='mdtui/search.html'):
    context = {}
    form = DocumentTypeSelectForm(request.POST or None)
    # Hack to make the navigation work for testing the templates
    if request.POST:
        if step == "1":
            if form.is_valid():
                try:
                    docrule = form.data["docrule"]
                except:
                    return HttpResponse(INDEXING_ERROR_STRINGS[1])
                    # TODO: refactor this (unright but quick)
                request.session['docrule_id'] = docrule
                step = str(int(step) + 1)
                return HttpResponseRedirect(reverse('mdtui-search-' + step))
                # else: return form on current step with errors
        elif step == "2":
            secondary_indexes = processDocumentIndexForm(request)
            if secondary_indexes:
                    request.session["document_keys_dict"] = secondary_indexes
                    step = str(int(step) + 1)
#        else:
#            step = str(int(step) - 1)
#            return HttpResponseRedirect(reverse('mdtui-search-' + step))

    else:
        if step == "1":
            form = DocumentTypeSelectForm()
        elif step == "2":
            form = initDocumentIndexForm(request)

    context.update({ 'form': form,
                    'step': step,
                    })
    return render_to_response(template, context, context_instance=RequestContext(request))


def search_results(request, step=None, template='mdtui/search.html'):

    # FIXME, move the db connection to helper function
    # Connect to Couch
    server = Server()
    try:
        db = server.get_or_create_db('dmscouch') # FIXME, settings.py
    except:
        raise

    Document.set_db(db) # Using base Document class from couchdbkit
    documents = Document.view('dmscouch/all')

    # Copy _id to id to prevent template variable name issue
    # http://stackoverflow.com/questions/6676045/accessing-couchdbs-uuid-in-django-templates
    for d in documents:
        setattr(d, 'id', d._id)

    # these should be set by the metadata template
    mdt_indexes = { 'key1': 'Key 1',
                'key2': 'Key 2',
                'CodeSomething': 'Some Code',
                }

    context = { 'step': step,
                'mdt_indexes': mdt_indexes,
                'documents': documents,
                }
    return render_to_response(template, context, context_instance=RequestContext(request))



def indexing(request, step=None, template='mdtui/indexing.html'):
    # Context init
    context = {}
    document_keys = None
    form = DocumentTypeSelectForm()

    # Hack to make the navigation work for testing the templates
    if request.POST:
        if step == "1":
            form = DocumentTypeSelectForm(request.POST)
            # TODO: needs proper validation
            if form.is_valid():
                try:
                    docrule = form.data["docrule"]
                except:
                    return HttpResponse(INDEXING_ERROR_STRINGS[1])
                # TODO: refactor this (unright but quick)
                request.session['current_step'] = step
                request.session['docrule_id'] = docrule
                step = str(int(step) + 1)
                return HttpResponseRedirect(reverse('mdtui-index-' + step))
            # else: return form on current step with errors
        if step == "2":
            secondary_indexes = processDocumentIndexForm(request)
            if secondary_indexes:
                    request.session["document_keys_dict"] = secondary_indexes
                    step = str(int(step) + 1)
            else:
                #going backwards
                step = str(int(step)-1)
            return HttpResponseRedirect(reverse('mdtui-index-' + step))
    else:
        if step == "1":
            form = DocumentTypeSelectForm()
        if step == "2":
            try:
                docrule = request.session['docrule_id']
            except KeyError:
                # This error only should appear if something breaks
                return HttpResponse(INDEXING_ERROR_STRINGS[1])
            if not request.POST:
                form = initDocumentIndexForm(request)

    try:
        document_keys = request.session["document_keys_dict"]
    except KeyError:
        pass
    
    context.update( { 'step': step,
                      'form': form,
                      'document_keys': document_keys,
                    })
    return render_to_response(template, context, context_instance=RequestContext(request))

def uploading(request, step=None, template='mdtui/indexing.html'):
    document_keys = None
    context = {}
    try:
        document_keys = request.session["document_keys_dict"]
    except KeyError:
        return HttpResponse(INDEXING_ERROR_STRINGS[2])
    form = DocumentUploadForm(request.POST or None, request.FILES or None)
    if step == "3":
        if request.POST:
            if form.is_valid():
                manager = DocumentManager()
                manager.store(request, form.files['file'], request.session["document_keys_dict"])
                if not manager.errors:
                    step = str(int(step) + 1)
                else:
                    step = str(int(step) - 1)
                    return HttpResponse(request, "; ".join(map(lambda x: x[0], manager.errors)))

    context.update( { 'step': step,
                      'form': form,
                      'document_keys': document_keys,
                    })
    if step == "4":
        if request.POST:
            # document uploaded forget everything
            request.session["document_keys_dict"] = None
            request.session['docrule_id'] = None
            del request.session['docrule_id']
            del request.session["document_keys_dict"]
    return render_to_response(template, context, context_instance=RequestContext(request))

def barcode(request):
    return HttpResponse('Barcode Printing')

def initDocumentIndexForm(request):
        """
        DocumentIndexForm initialization
        in case of GET returns an empty base form,
        in case of POST returns populated (from request) form instance.
        in both cases form is rendered with MDT index fields
        """
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

def processDocumentIndexForm(request):
        form = initDocumentIndexForm(request)
        secondary_indexes = {}
        if form.validation_ok():
            for key, field in form.fields.iteritems():
                try:
                    # for native form fields
                    secondary_indexes[field.field_name] = form.data[unicode(key)]
                except:
                    # for dynamical form fields
                    secondary_indexes[key] = form.data[unicode(key)]
            #print secondary_indexes
            if secondary_indexes:
                return secondary_indexes
            else:
                return None