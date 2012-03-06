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
from django.contrib.auth.decorators import login_required

from dmscouch.models import CouchDocument

from forms import DocumentTypeSelectForm, DocumentUploadForm

from document_manager import DocumentManager
from view_helpers import *


MDTUI_ERROR_STRINGS = {
    1:'{"status": "Error. You have not selected Doccument Type Rule."}',
    2:'{"status": "Error. You have not entered Document Indexing Data."}',
    3:'{"status": "Error. You have not defined Document Searching Keys."}',
    4:'{"status": "Error. You have not defined Document Type Rule. Search form can not be created."}'
}

@login_required
def search_type(request, step, template='mdtui/search.html'):
    context = { 'step': step, }
    form = DocumentTypeSelectForm(request.POST or None)
    if request.POST:
            if form.is_valid():
                try:
                    docrule = form.data["docrule"]
                except:
                    return HttpResponse(MDTUI_ERROR_STRINGS[1])
                request.session['docrule'] = docrule
                return HttpResponseRedirect(reverse('mdtui-search-options'))
            else:
                pass
                # TODO: return form on current step with errors
    else:
        form = DocumentTypeSelectForm()

    context.update({ 'form': form, })
    return render_to_response(template, context, context_instance=RequestContext(request))

@login_required
def search_options(request, step, template='mdtui/search.html'):
    context = { 'step': step, }
    try:
        docrule = request.session["docrule"]
    except KeyError:
        return HttpResponse(MDTUI_ERROR_STRINGS[4])

    form = initDocumentIndexForm(request)
    # excluding description from search form
    try:
        del form.fields["description"]
    except: pass
    try:
        del form.base_fields["description"]
    except: pass

    if request.POST:
        secondary_indexes = processDocumentIndexForm(request)
        if secondary_indexes:
            request.session["document_search_dict"] = secondary_indexes
            return HttpResponseRedirect(reverse('mdtui-search-results'))
    else:
        # date field should be empty
        form.fields["date"].initial = None

    context.update({ 'form': form, })
    return render_to_response(template, context, context_instance=RequestContext(request))

@login_required
def search_results(request, step=None, template='mdtui/search.html'):
    document_keys = None
    docrule_id = None
    documents = None
    search_res = None
    try:
        document_keys = request.session["document_search_dict"]
        docrule_id = request.session['docrule']
    except KeyError:
        return HttpResponse(MDTUI_ERROR_STRINGS[3])

    # turning document_search dict into something useful for the couch request
    cleaned_document_keys  = cleanup_document_keys(document_keys)
    if "date" in cleaned_document_keys.keys() and cleaned_document_keys.__len__() == 1:
        # only one crytheria 'date' in search request, requesting another view
        #print 'searching only by date: ', str_date_to_couch(cleaned_document_keys["date"]), ' docrule:', docrule_id
        documents = CouchDocument.view('dmscouch/search_date', key=[str_date_to_couch(cleaned_document_keys["date"]), docrule_id], include_docs=True )
    else:
        #print 'multiple keys search'
        couch_req_params = convert_to_search_keys(cleaned_document_keys, docrule_id)
        if couch_req_params:
            search_res = CouchDocument.view('dmscouch/search', keys=couch_req_params )
            # docuents now returns ANY search type results.
            # we need to convert it to ALL
            docs_list = convert_search_res(search_res, couch_req_params.__len__())
            documents = CouchDocument.view('_all_docs', keys=docs_list, include_docs=True )
    mdts_list = get_mdts_for_documents(documents)

    context = { 'step': step,
                'documents': documents,
                'document_keys': document_keys,
                'mdts': mdts_list,
                }
    return render_to_response(template, context, context_instance=RequestContext(request))

@login_required
def search_viewer(request, code, step, template='mdtui/search.html'):
    context = { 'step': step,
                'code': code,
                }
    return render_to_response(template, context, context_instance=RequestContext(request))


@login_required
def indexing(request, step=None, template='mdtui/indexing.html'):
    # Context init
    context = {}
    docrule = None
    document_keys = None
    form = DocumentTypeSelectForm()

    try:
        # search done. Cleaning up session for indexing to avoid collisions in functions
        del request.session["document_search_dict"]
        del request.session['docrule']
    except: pass
    # Hack to make the navigation work for testing the templates
    if request.POST:
        if step == "1":
            form = DocumentTypeSelectForm(request.POST)
            # TODO: needs proper validation
            if form.is_valid():
                try:
                    docrule = form.data["docrule"]
                except:
                    return HttpResponse(MDTUI_ERROR_STRINGS[1])
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
            # form initing with docrule set if it was done previous
            try:
                docrule = request.session["docrule_id"]
            except:
                pass
            form = DocumentTypeSelectForm()
            # HACK to set form data to previously set up if returning back to this page from later steps
            if docrule:
                form.base_fields["docrule"].initial = form.fields["docrule"].choices[int(docrule)]
        if step == "2":
            try:
                docrule = request.session['docrule_id']
            except KeyError:
                # This error only should appear if something breaks
                return HttpResponse(MDTUI_ERROR_STRINGS[1])
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

@login_required
def uploading(request, step=None, template='mdtui/indexing.html'):
    document_keys = None
    context = {}
    try:
        document_keys = request.session["document_keys_dict"]
    except KeyError:
        return HttpResponse(MDTUI_ERROR_STRINGS[2])
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




