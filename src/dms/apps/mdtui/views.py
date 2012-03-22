"""
Module: Metadata Template UI Views
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

import json
import logging

from django.core.urlresolvers import reverse, resolve
from django.http import HttpResponse
from django.shortcuts import render, redirect, render_to_response, HttpResponseRedirect, get_object_or_404
from django.template import RequestContext, loader
from django.contrib.auth.decorators import login_required

from dmscouch.models import CouchDocument
from forms import DocumentTypeSelectForm, DocumentUploadForm
from document_manager import DocumentManager
from view_helpers import *
from parallel_keys import ParallelKeysManager

log = logging.getLogger('dms')

MDTUI_ERROR_STRINGS = {
    1:'You have not selected the Document Type.',
    2:'You have not entered Document Indexing Data. Document will not be searchable by indexes.',
    3:'You have not defined Document Searching Options.',
    4:'You have not defined Document Type. Can only search by "Creation Date".',
}


@login_required
def search_type(request, step, template='mdtui/search.html'):
    """
    Search Step 1: Select Search Type
    """
    docrule = None
    cleanup_indexing_session(request)
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
    autocomplete_list = extract_secondary_keys_from_form(form)
    try:
        # Exclude description from search form, because we can't yet search on it.
        del form.fields["description"]
    except KeyError:
        pass

    if request.POST:
        secondary_indexes = processDocumentIndexForm(request)
        if secondary_indexes:
            request.session["document_search_dict"] = secondary_indexes
            return HttpResponseRedirect(reverse('mdtui-search-results'))
    else:
        # Date field should be empty for search needs
        form.fields["date"].initial = None

    context = {
                'form': form,
                'warnings': warnings,
                'step': step,
                'autocomplete_fields': autocomplete_list,
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
            # only one criterion 'date' in search request, requesting another view
            #print 'searching only by date: ', str_date_to_couch(cleaned_document_keys["date"]), ' docrule:', docrule_id
            documents = CouchDocument.view('dmscouch/search_date', key=[str_date_to_couch(cleaned_document_keys["date"]), docrule_id], include_docs=True )
        else:
            #print 'multiple keys search'
            couch_req_params = convert_to_search_keys(cleaned_document_keys, docrule_id)
            if couch_req_params:
                search_res = CouchDocument.view('dmscouch/search', keys=couch_req_params )
                # documents now returns ANY search type results.
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
def indexing_select_type(request, step=None, template='mdtui/indexing.html'):
    """
    Indexing: Step 1 : Select Document Type
    """
    # Context init
    context = {}
    docrule = None
    document_keys = None
    autocomplete_list = []
    warnings = []
    form = DocumentTypeSelectForm(request.POST or None)
    cleanup_search_session(request)

    if request.POST:

        # TODO: needs proper validation
        if form.is_valid():
            try:
                docrule = form.data["docrule"]
            except:
                return HttpResponse(MDTUI_ERROR_STRINGS[1])
            request.session['current_step'] = step
            request.session['docrule_id'] = docrule
            return HttpResponseRedirect(reverse('mdtui-index-details'))
    else:
        # form initing with docrule set if it was done previous
        try:
            docrule = request.session["docrule_id"]
        except KeyError:
            pass
        form = DocumentTypeSelectForm()
        if docrule:
            form = DocumentTypeSelectForm({'docrule': docrule})

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
def indexing_details(request, step=None, template='mdtui/indexing.html'):
    """
    Indexing: Step 2 : Index Details
    """
    # Context init
    context = {}
    docrule = None
    document_keys = None
    autocomplete_list = []
    warnings = []
    cleanup_search_session(request)

    if request.POST:
        secondary_indexes = processDocumentIndexForm(request)
        if secondary_indexes:
                request.session["document_keys_dict"] = secondary_indexes
                return HttpResponseRedirect(reverse('mdtui-index-source'))
        else:
            # Return validation with errrors...
            form = initDocumentIndexForm(request)
    else:
        try:
            docrule = request.session['docrule_id']
        except KeyError:
            warnings.append(MDTUI_ERROR_STRINGS[1])
        form = initDocumentIndexForm(request)

    autocomplete_list = extract_secondary_keys_from_form(form)
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
def indexing_uploading(request, step=None, template='mdtui/indexing.html'):
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

    if request.POST: # or Something else eg barcode printer

        try:
            index_info = request.session["document_keys_dict"]
        except KeyError:
            warnings.append(MDTUI_ERROR_STRINGS[3])

        try:
            docrule = request.session['docrule_id']
        except KeyError:
            warnings.append(MDTUI_ERROR_STRINGS[1])

        if form.is_valid(): # Must've uploaded a file

            if not warnings:
                manager = DocumentManager()
                manager.store(request, form.files['file'], index_info=index_info or None, allocate_barcode=docrule or None)

                if not manager.errors:
                    return HttpResponseRedirect(reverse('mdtui-index-finished'))
                else:
                    # FIXME: dodgy error handling
                    return HttpResponse(str(manager.errors))

        #elif: # Something else, eg barcode printer
            # Allocate Empty Barcode
            # manager = DocumentManager()
            # manager.store(request, index_info=index_info or None, allocate_barcode=docrule or None)
            # NB need to modify DocumentManager to set_db_info and not require a file
            # Print barcode

    context.update( { 'step': step,
                      'form': form,
                      'document_keys': document_keys,
                      'warnings': warnings,
                    })

    return render_to_response(template, context, context_instance=RequestContext(request))


@login_required
def indexing_finished(request, step=None, template='mdtui/indexing.html'):
    """
    Indexing: Step 4: Finished
    """
    context = { 'step': step,  }
    try:
        context.update({'document_keys':request.session["document_keys_dict"],})
    except KeyError:
        pass
    # document uploaded forget everything
    cleanup_indexing_session(request)
    log.debug('mdtui.views.indexing_finished called with: step: "%s", document_keys_dict: "%s",' %
              (step, context['document_keys']))
    return render(request, template, context)


def indexing_barcode(request):
    """
    Indexing: Step X: Print Barcode
    """
    return HttpResponse('Barcode Printing')


@login_required
def mdt_parallel_keys(request):
    """
    Returns parallel keys suggestions for autocomplete.
    NB, Don't rename this to parallel_keys. It conflicts with imported lib of same name.
    """
    valid_call = True
    autocomplete_req = None
    docrule_id = None
    key_name = None
    resp = []
    # Trying to get docrule for indexing calls
    try:
        docrule_id = request.session['docrule_id']
    except KeyError:
        valid_call = False
    # Trying to get docrule for searching calls
    try:
        if not docrule_id:
            docrule_id = request.session['docrule']
            valid_call = True
    except KeyError:
        pass

    try:
        key_name = request.POST[u'key_name']
        autocomplete_req = request.POST[u'autocomplete_search']
    except KeyError:
        valid_call = False

    log.debug('mdtui.views.mdt_parallel_keys call with: docrule_id: "%s", key_name: "%s", autocomplete_req: "%s" Call is valid: "%s".' %
              (docrule_id, key_name, autocomplete_req, valid_call))

    if valid_call:
        manager = ParallelKeysManager()
        mdts = manager.get_keys_for_docrule(docrule_id)
        pkeys = manager.get_parallel_keys_for_key(mdts, key_name)
        # db call to search in docs
        # TODO: emit unique keys (Reduce fucntion for this view)
        # TODO: search only for this django user... <-- AC: Huh? (YG: Each document has django user id assigned (creator)
        # This way we may only suggest indexes for this user.
        documents = CouchDocument.view(
            'dmscouch/search_autocomplete',  # FIXME: hardcoded url
            startkey=[docrule_id, key_name, autocomplete_req],
            endkey=[docrule_id, key_name, unicode(autocomplete_req)+u'\ufff0' ], # FIXME: AC: What's this magic?
            include_docs=True
        )
        # Adding each selected value to suggestions list
        for doc in documents:
            resp_array = {}
            for pkey in pkeys:
                resp_array[pkey['field_name']] = doc.mdt_indexes[pkey['field_name']]
            resp.append(json.dumps(resp_array))
    log.debug('mdtui.views.mdt_parallel_keys response: %s' % resp)
    return HttpResponse(json.dumps(resp))


@login_required
def download_pdf(request, code):
    """
    Returns Document For Download
    """
    # right now we just redirect to API, but in future we might want to decouple from API app.
    url = reverse('api_file')
    return redirect('%s?filename=%s.pdf' %(url, code))