"""
Module: Metadata Template UI Views
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

from django.core.urlresolvers import reverse, resolve
from django.http import HttpResponse
from django.shortcuts import render, render_to_response, HttpResponseRedirect, get_object_or_404
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required

from dmscouch.models import CouchDocument
from forms import DocumentTypeSelectForm, DocumentUploadForm
from document_manager import DocumentManager
from view_helpers import *
from parallel_keys import ParallelKeysManager


MDTUI_ERROR_STRINGS = {
    1:'You have not selected Doccument Type Rule.',
    2:'You have not entered Document Indexing Data. Document will not be searchable by indexes.',
    3:'You have not defined Document Searching Options.',
    4:'You have not defined Document Type Rule. Can only search by "Creation Date".',
}


@login_required
def search_type(request, step, template='mdtui/search.html'):
    """
    Search Step 1: Select Search Type
    """
    docrule = None
    form = DocumentTypeSelectForm(request.POST or None)
    if request.POST:
            if form.is_valid():
                docrule = form.data["docrule"]
                request.session['docrule'] = docrule
                return HttpResponseRedirect(reverse('mdtui-search-options'))
            else:
                return HttpResponse(MDTUI_ERROR_STRINGS[1])
    else:
        form = DocumentTypeSelectForm()
        # Trying to set docrule if previously selected
        try:
            docrule = request.session['docrule']
        except KeyError:
            pass
        if docrule:
            form = DocumentTypeSelectForm({'docrule': docrule})

    context = {
                'step': step,
                'form': form,
               }
    return render_to_response(template, context, context_instance=RequestContext(request))


@login_required
def search_options(request, step, template='mdtui/search.html'):
    """
    Search Step 2: Search Options
    """
    warnings = []
    try:
        docrule = request.session["docrule"]
    except KeyError:
        warnings.append(MDTUI_ERROR_STRINGS[4])

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

    context = {
                'form': form,
                'warnings': warnings,
                'step': step,
               }
    return render_to_response(template, context, context_instance=RequestContext(request))


@login_required
def search_results(request, step=None, template='mdtui/search.html'):
    """
    Search Step 3: Search Results
    """
    document_keys = None
    docrule_id = None
    documents = None
    search_res = None
    warnings = []
    mdts_list = None
    try:
        document_keys = request.session["document_search_dict"]
        docrule_id = request.session['docrule']
    except KeyError:
        warnings.append(MDTUI_ERROR_STRINGS[3])

    if document_keys:
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
                'warnings': warnings,
                }
    return render_to_response(template, context, context_instance=RequestContext(request))


@login_required
def search_viewer(request, code, step, template='mdtui/search.html'):
    """
   Search Step 4: View Document
    """
    context = { 'step': step,
                'code': code,
                }
    return render_to_response(template, context, context_instance=RequestContext(request))


@login_required
def indexing(request, step=None, template='mdtui/indexing.html'):
    """
    Indexing: Step 1 & 2
    """
    # Context init
    context = {}
    docrule = None
    document_keys = None
    autocomplete_list = []
    warnings = []
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
                    #step = str(int(step) + 1)
                    return HttpResponseRedirect(reverse('mdtui-index-3'))
            else:
                # validation rendering...
                form = initDocumentIndexForm(request)
    else:
        if step == "1":
            # form initing with docrule set if it was done previous
            try:
                docrule = request.session["docrule_id"]
            except:
                pass
            form = DocumentTypeSelectForm()
            if docrule:
                form = DocumentTypeSelectForm({'docrule': docrule})
        if step == "2":
            try:
                docrule = request.session['docrule_id']
            except KeyError:
                warnings.append(MDTUI_ERROR_STRINGS[1])
            form = initDocumentIndexForm(request)
            #autocomplete_list = exctract_secondary_keys_from_form(form)

    try:
        document_keys = request.session["document_keys_dict"]
    except KeyError:
        pass
    
    context.update( { 'step': step,
                      'form': form,
                      'document_keys': document_keys,
                      'autocomplete_fields': autocomplete_list,
                      'warnings': warnings,
                    })
    return render_to_response(template, context, context_instance=RequestContext(request))


@login_required
def uploading(request, step=None, template='mdtui/indexing.html'):
    """
    Indexing: Step 3: Upload File / Associate File / Print Barcode
    """
    document_keys = None
    context = {}
    warnings = []
    try:
        document_keys = request.session["document_keys_dict"]
    except KeyError:
        warnings.append(MDTUI_ERROR_STRINGS[2])
    form = DocumentUploadForm(request.POST or None, request.FILES or None)
    if step == "3":
        if request.POST:
            if form.is_valid():
                manager = DocumentManager()
                manager.store(request, form.files['file'], request.session["document_keys_dict"])
                if not manager.errors:
                    return HttpResponseRedirect(reverse('mdtui-index-finished'))
                else:
                    step = str(int(step) - 1)
                    return HttpResponse(request, "; ".join(map(lambda x: x[0], manager.errors)))

    context.update( { 'step': step,
                      'form': form,
                      'document_keys': document_keys,
                      'warnings': warnings,
                    })

    return render_to_response(template, context, context_instance=RequestContext(request))


def finished(request, step=None, template='mdtui/indexing.html'):
    """
    Indexing: Step 4: Finished
    """
    context = { 'step': step,  }

    try:
        context.update({'document_keys':request.session["document_keys_dict"],})
    except KeyError:
        pass

    # document uploaded forget everything
    request.session["document_keys_dict"] = None
    request.session['docrule_id'] = None
    del request.session['docrule_id']
    del request.session["document_keys_dict"]

    return render(request, template, context)


def barcode(request):
    """
    Indexing: Step X: Print Barcode
    """
    return HttpResponse('Barcode Printing')

def parallel_keys(request):
    """
    Returns parallel keys suggestions for autocomplete.
    """
    valid_call = True
    autocomplete_req = None
    docrule_id = None
    key_name = None
    resp = {}
    try:
        docrule_id = request.session['docrule_id']
    except:
        valid_call = False

    try:
        key_name = request.GET[u'key_name']
        autocomplete_req = request.GET[u'autocomplete_search']
    except:
        valid_call = False

    if valid_call:
        manager = ParallelKeysManager()
        mdts = manager.get_keys_for_docrule(docrule_id)
        pkeys = manager.get_parallel_keys_for_key(mdts, key_name)
        # db call to search in docs
        # TODO: emit unique keys
        # TODO: search only for this django user...
        documents = CouchDocument.view(
            'dmscouch/search_autocomplete',
            startkey=[docrule_id, key_name, autocomplete_req],
            endkey=[docrule_id, key_name, unicode(autocomplete_req)+u'\ufff0' ],
            include_docs=True
        )
        for doc in documents:
            for pkey  in pkeys:
                resp[pkey['field_name']] = doc.mdt_indexes[pkey['field_name']]
        print resp
    return HttpResponse([resp,])






