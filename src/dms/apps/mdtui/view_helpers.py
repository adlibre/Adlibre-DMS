"""
Module: Metadata Template UI views helpers
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

from forms import DocumentIndexForm
from forms_representator import get_mdts_for_docrule, render_fields_from_docrules


def initDocumentIndexForm(request):
        """
        DocumentIndexForm initialization
        in case of GET returns an empty base form,
        in case of POST returns populated (from request) form instance.
        in both cases form is rendered with MDT index fields
        """
        details = None
        try:
            try:
                details = get_mdts_for_docrule(request.session['docrule_id'])
            except KeyError:
                details = get_mdts_for_docrule(request.session['docrule'])
        except KeyError:
            pass

        form = DocumentIndexForm()
        if details:
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
        except Exception:
            pass
        if form.validation_ok() or search:
            for key, field in form.fields.iteritems():
                try:
                    # for dynamical form fields
                    secondary_indexes[field.field_name] = form.data[unicode(key)]
                except Exception:
                    # for native form fields
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
    """

    """
    indexes = {}
    resp = None
    if documents:
        for document in documents:
            xes = document.mdt_indexes
            for ind in xes:
                indexes[ind] = ""
        resp = indexes.keys()
    return resp