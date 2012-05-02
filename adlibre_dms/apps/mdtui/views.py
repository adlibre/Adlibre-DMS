"""
Module: Metadata Template UI Views
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

import json
import logging

from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render, redirect, render_to_response, HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from dmscouch.models import CouchDocument
from forms import DocumentTypeSelectForm, DocumentUploadForm, BarcodePrintedForm, DocumentSearchOptionsForm
from document_manager import DocumentManager
from doc_codes.models import DocumentTypeRule
from view_helpers import initIndexesForm
from view_helpers import processDocumentIndexForm
from view_helpers import get_mdts_for_documents
from view_helpers import extract_secondary_keys_from_form
from view_helpers import cleanup_search_session
from view_helpers import cleanup_indexing_session
from view_helpers import cleanup_mdts
from search_helpers import cleanup_document_keys
from search_helpers import document_date_range_only_search
from search_helpers import document_date_range_with_keys_search
from search_helpers import recognise_dates_in_search
from search_helpers import document_date_range_present_in_keys
from search_helpers import dates_ranges_exist
from search_helpers import ranges_validator
from forms_representator import get_mdts_for_docrule
from parallel_keys import ParallelKeysManager
from data_exporter import export_to_csv

from restkit.client import RequestError


log = logging.getLogger('dms.mdtui.views')

MDTUI_ERROR_STRINGS = {
    1:'You have not selected the Document Type.',
    2:'You have not entered Document Indexing Data. Document will not be searchable by indexes.',
    3:'You have not defined Document Searching Options.',
    4:'You have not defined Document Type. Can only search by "Creation Date".',
    5:'Database Connection absent. Check CouchDB server connection.',
    'NO_DOCUMENTS_FOUND': 'Nothing to export because of empty documents results.'
}


@login_required
def search_type(request, step, template='mdtui/search.html'):
    """
    Search Step 1: Select Search Type
    """
    docrule = None
    warnings = []
    cleanup_indexing_session(request)
    cleanup_mdts(request)
    form = DocumentTypeSelectForm(request.POST or None)
    if request.POST:
            if form.is_valid():
                mdts = None
                docrule = form.data["docrule"]
                request.session['docrule'] = docrule
                # CouchDB connection Felt down warn user
                try:
                    mdts = get_mdts_for_docrule(docrule)
                except RequestError:
                    warnings.append(MDTUI_ERROR_STRINGS[5])
                if mdts:
                    request.session['mdts'] = mdts
                    return HttpResponseRedirect(reverse('mdtui-search-options'))
            else:
                warnings.append(MDTUI_ERROR_STRINGS[1])
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
                'warnings': warnings,
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
    autocomplete_list = None
    try:
        request.session["docrule"]
    except KeyError:
        warnings.append(MDTUI_ERROR_STRINGS[4])

    # CouchDB connection Felt down warn user
    try:
        form = initIndexesForm(request)
        autocomplete_list = extract_secondary_keys_from_form(form)
    except (RequestError,AttributeError) :
        form = DocumentSearchOptionsForm
        warnings.append(MDTUI_ERROR_STRINGS[5])

    if request.POST:
        try:
            secondary_indexes = processDocumentIndexForm(request)
        except RequestError:
            secondary_indexes = None
            warnings.append(MDTUI_ERROR_STRINGS[5])

        if secondary_indexes:
            request.session["document_search_dict"] = secondary_indexes
            return HttpResponseRedirect(reverse('mdtui-search-results'))

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
    warnings = []
    mdts_list = None
    try:
        document_keys = request.session["document_search_dict"]
        docrule_id = request.session['docrule']
    except KeyError:
        warnings.append(MDTUI_ERROR_STRINGS[3])
    log.debug('search_results call: docrule_id: "%s", document_search_dict: "%s"' % (docrule_id, document_keys))
    if document_keys:
        # turning document_search dict into something useful for the couch request
        clean_keys = cleanup_document_keys(document_keys)
        ck = ranges_validator(clean_keys)
        cleaned_document_keys = recognise_dates_in_search(ck)
        keys = [key for key in cleaned_document_keys.iterkeys()]
        dr_exist = dates_ranges_exist(cleaned_document_keys)
        dd_range_keys = document_date_range_present_in_keys(keys)
        keys_cnt = cleaned_document_keys.__len__()
        # Selecting appropriate search method
        if dd_range_keys and keys_cnt == 2:
            documents = document_date_range_only_search(cleaned_document_keys, docrule_id)
        else:
            documents = document_date_range_with_keys_search(cleaned_document_keys, docrule_id)

        mdts_list = get_mdts_for_documents(documents)

    # Produces a CSV file from search results
    if documents and step == 'export':
        log.debug('search_results exporting found documents to CSV')
        csv_response = export_to_csv(document_keys, mdts_list, documents)
        return csv_response

    context = { 'step': step,
                'documents': documents,
                'document_keys': document_keys,
                'mdts': mdts_list,
                'warnings': warnings,
                }
    return render_to_response(template, context, context_instance=RequestContext(request))


@login_required
def search_viewer(request, code, step, template='mdtui/view.html'):
    """
    Search Step 4: View Document
    """

    pdf_url = reverse('mdtui-download-pdf', kwargs = { 'code': code, })
    context = { 'pdf_url': pdf_url, 'code': code, 'step':step }
    return render(request, template, context)


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
    cleanup_mdts(request)
    
    if request.POST:
        if form.is_valid():
            docrule = form.data["docrule"]
            request.session['docrule_id'] = docrule
            mdts = get_mdts_for_docrule(docrule)
            if mdts:
                request.session['mdts'] = mdts
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
    document_keys = None
    warnings = []
    cleanup_search_session(request)
    docrule_id = None

    try:
        docrule_id = request.session['docrule_id']
    except KeyError:
        warnings.append(MDTUI_ERROR_STRINGS[1])

    try:
        document_keys = request.session["document_keys_dict"]
    except KeyError:
        pass

    if request.POST:
        secondary_indexes = processDocumentIndexForm(request)
        if secondary_indexes:
                request.session["document_keys_dict"] = secondary_indexes
                # Success, allocate barcode
                dtr = DocumentTypeRule.objects.get(doccode_id=docrule_id)
                request.session["barcode"] = dtr.allocate_barcode()
                return HttpResponseRedirect(reverse('mdtui-index-source'))
        else:
            # Return validation with errors...
            form = initIndexesForm(request)
    else:
        form = initIndexesForm(request)

    autocomplete_list = extract_secondary_keys_from_form(form)

    context.update( { 'step': step,
                      'form': form,
                      'document_keys': document_keys,
                      'autocomplete_fields': autocomplete_list,
                      'warnings': warnings,
                    })
    return render_to_response(template, context, context_instance=RequestContext(request))


@login_required
def indexing_source(request, step=None, template='mdtui/indexing.html'):
    """
    Indexing: Step 3: Upload File / Associate File / Print Barcode
    """
    document_keys = None
    context = {}
    warnings = []
    index_info = None
    docrule = None
    barcode = None

    # Check session variables
    try:
        document_keys = request.session["document_keys_dict"]
    except KeyError:
        warnings.append(MDTUI_ERROR_STRINGS[2])

    try:
        barcode = request.session['barcode']
    except KeyError:
        warnings.append(MDTUI_ERROR_STRINGS[2])

    try:
        index_info = request.session["document_keys_dict"]
    except KeyError:
        warnings.append(MDTUI_ERROR_STRINGS[3])

    try:
        docrule = request.session['docrule_id']
    except KeyError:
        warnings.append(MDTUI_ERROR_STRINGS[1])

    # Init Forms
    upload_form = DocumentUploadForm(request.POST or None, request.FILES or None)
    barcode_form = BarcodePrintedForm(request.POST or None)

    if upload_form.is_valid() or barcode_form.is_valid():
        if not warnings:
            if upload_form.is_valid():
                upload_file = upload_form.files['file']
            else:
                # HACK: upload a stub document as our first revision
                import os
                upload_file = open(os.path.join(os.path.split(__file__)[0], 'stub_document.pdf'), 'rb')

            manager = DocumentManager()
            manager.store(request, upload_file, index_info=index_info, barcode=barcode)

            if not manager.errors:
                return HttpResponseRedirect(reverse('mdtui-index-finished'))
            else:
                # FIXME: dodgy error handling
                return HttpResponse(str(manager.errors))

    context.update( { 'step': step,
                      'upload_form': upload_form,
                      'barcode_form': barcode_form,
                      'document_keys': document_keys,
                      'warnings': warnings,
                      'barcode': barcode,
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
        log.debug('indexing_finished called with: step: "%s", document_keys_dict: "%s",' %
                  (step, context['document_keys']))
    except KeyError:
        pass

    try:
        context.update({'docrule_id':request.session["docrule_id"],})
    except KeyError:
        pass
    # document uploaded forget everything
    cleanup_indexing_session(request)
    cleanup_mdts(request)
    return render(request, template, context)


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
    mdts={}
    resp = []
    # Trying to get docrule for indexing calls
    try:
        docrule_id = request.session['docrule_id']
    except KeyError:
        pass
    # Trying to get docrule for searching calls
    try:
        if not docrule_id:
            docrule_id = request.session['docrule']
    except KeyError:
        pass

    try:
        key_name = request.POST[u'key_name']
        autocomplete_req = request.POST[u'autocomplete_search']
    except KeyError:
        valid_call = False

    try:
        mdts = request.session["mdts"]
    except KeyError:
        pass

    log.debug(
        'mdt_parallel_keys call: docrule_id: "%s", key_name: "%s", autocomplete: "%s" Call is valid: "%s", MDTS: %s' %
        (docrule_id, key_name, autocomplete_req, valid_call, mdts)
    )
    if valid_call:
        manager = ParallelKeysManager()
        mdts = manager.get_keys_for_docrule(docrule_id, mdts)
        pkeys = manager.get_parallel_keys_for_key(mdts, key_name)
        # db call to search in docs
        if pkeys:
            # Suggestion for several parallel keys
            documents = CouchDocument.view(
                'dmscouch/search_autocomplete', # Name of couch view "couchapps/dmscouch/_design/views/search_autocomplete"
                startkey=[key_name, autocomplete_req],
                endkey=[key_name, unicode(autocomplete_req)+u'\ufff0' ], # http://wiki.apache.org/couchdb/HTTP_view_API
                include_docs=True # TODO: think about optimising this call (E.G. response with 10000 docs = 1MB request)
                                  # Maybe!!! add 1 more db view call to get docs with unique those secondary keys pairs...
            )
            # Adding each selected value to suggestions list
            for doc in documents:
                resp_array = {}
                if pkeys:
                    for pkey in pkeys:
                        resp_array[pkey['field_name']] = doc.mdt_indexes[pkey['field_name']]
                suggestion = json.dumps(resp_array)
                # filtering from existing results
                if not suggestion in resp:
                    resp.append(suggestion)
        else:
            # Simple 'single' key suggestion
            documents = CouchDocument.view(
                'dmscouch/search_autocomplete',
                startkey=[key_name, autocomplete_req],
                endkey=[key_name, unicode(autocomplete_req)+u'\ufff0' ],
                include_docs=True # TODO: change indexes not to load the full document but required fields (MAYBE)
            )
            # Fetching unique responses to suggestion set
            for doc in documents:
                resp_array = {key_name: doc.mdt_indexes[key_name]}
                suggestion = json.dumps(resp_array)
                if not suggestion in resp:
                    resp.append(suggestion)
    log.debug('mdt_parallel_keys response: %s' % resp)
    return HttpResponse(json.dumps(resp))

@login_required
def download_pdf(request, code):
    """
    Returns Document For Download
    """
    # right now we just redirect to API, but in future we might want to decouple from API app.
    url = reverse('api_file', kwargs={'code': code, 'suggested_format': 'pdf'},)
    return redirect(url)
