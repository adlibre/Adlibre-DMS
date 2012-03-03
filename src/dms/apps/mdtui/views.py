"""
Module: Metadata Template UI Views
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""
import datetime

from django.core.urlresolvers import reverse, resolve
from django.http import HttpResponse
from django.shortcuts import render_to_response, HttpResponseRedirect, get_object_or_404
from django.template import RequestContext, loader

from dmscouch.models import CouchDocument

from forms import DocumentIndexForm, DocumentTypeSelectForm, DocumentUploadForm
from forms_representator import get_mdts_for_docrule, render_fields_from_docrules
from document_manager import DocumentManager


MDTUI_ERROR_STRINGS = {
    1:'{"status": "Error. You have not selected Doccument Type Rule."}',
    2:'{"status": "Error. You have not entered Document Indexing Data."}',
    3:'{"status": "Error. You have not defined Document Searching Keys."}',
    4:'{"status": "Error. You have not defined Document Type Rule. Search form can not be created."}'
}


def search_type(request, step, template='mdtui/search.html'):
    context = { 'step': step, }
    form = DocumentTypeSelectForm(request.POST or None)
    if request.POST:
            if form.is_valid():
                try:
                    docrule = form.data["docrule"]
                except:
                    return HttpResponse(MDTUI_ERROR_STRINGS[1])
                    # TODO: refactor this (unright but quick)
                request.session['docrule'] = docrule
                return HttpResponseRedirect(reverse('mdtui-search-options'))
            else:
                pass
                # TODO: return form on current step with errors
    else:
        form = DocumentTypeSelectForm()

    context.update({ 'form': form, })
    return render_to_response(template, context, context_instance=RequestContext(request))


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


def search_viewer(request, code, step, template='mdtui/search.html'):
    context = { 'step': step,
                'code': code,
                }
    return render_to_response(template, context, context_instance=RequestContext(request))



def indexing(request, step=None, template='mdtui/indexing.html'):
    # Context init
    context = {}
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

def initDocumentIndexForm(request):
        """
        DocumentIndexForm initialization
        in case of GET returns an empty base form,
        in case of POST returns populated (from request) form instance.
        in both cases form is rendered with MDT index fields
        """
        try:
            details = get_mdts_for_docrule(request.session['docrule_id'])
        except KeyError:
            details = get_mdts_for_docrule(request.session['docrule'])

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
        search = None
        try:
            search = request.session["docrule"]
        except: pass
        if form.validation_ok() or search:
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

def convert_search_res(search_res, match_len):
    docs_list = {}
    matched_docs = []
    for row in search_res:
        if row.get_id in docs_list.keys():
            docs_list[row.get_id] += 1
        else:
            docs_list[row.get_id] = 1
    for doc_id, mention_count in docs_list.iteritems():
        if int(mention_count) >= int(match_len):
            matched_docs.append(doc_id)
    return matched_docs

def convert_to_search_keys(document_keys, docrule_id):
    req_params = []
    for key, value in document_keys.iteritems():
        if key != "date":
            if not "date" in document_keys.keys():
                req_params.append([key, value, docrule_id],)
            else:
                req_params.append([key, value, docrule_id, str_date_to_couch(document_keys["date"])],)
    return req_params

def cleanup_document_keys(document_keys):
    # cleaning up key/value pairs that have empty values from couchdb search request
    del_list = []
    for key, value in document_keys.iteritems():
        if not value:
            del_list.append(key)
    for key in del_list:
        del document_keys[key]
    return document_keys

def str_date_to_couch(from_date):
    """
    Converts date from form date widget generated format, like '2012-03-02'
    To CouchDocument stored date. E.g.: '2012-03-02T00:00:00Z'
    """
    # TODO: HACK: normal datetime conversions here
    couch_date = from_date + 'T00:00:00Z'
#    date = datetime.datetime.strptime(from_date, "%Y-%m-%d")
#    couch_date = datetime.datetime.now()
    return couch_date

def get_mdts_for_documents(documents):
    indexes = {}
    if documents:
        for document in documents:
            xes = document.mdt_indexes
            for ind in xes:
                indexes[ind] = "index"
    return indexes.keys()