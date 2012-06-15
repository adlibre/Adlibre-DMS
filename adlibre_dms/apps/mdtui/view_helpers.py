"""
Module: Metadata Template UI views helpers

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import datetime
from django.conf import settings

from forms import DocumentIndexForm
from forms import DocumentSearchOptionsForm
from forms_representator import render_fields_from_docrules
from forms_representator import get_mdts_for_docrule

def initIndexesForm(request):
    """
    DocumentIndexForm/DocumentSearchForm initialization

    in case of GET returns an empty base form,
    in case of POST returns populated (from request) form instance.
    in both cases form is rendered with MDT index fields
    """
    details = None
    search = determine_search_req(request)
    try:
        # Try to use cached MDT's
        details = request.session['mdts']
    except KeyError:
        if search:
            session_var = 'search_docrule_id'
        else:
            session_var = 'indexing_docrule_id'

        # Get MDT's from CouchDB
        try:
            details = get_mdts_for_docrule(request.session[session_var])
            # Store MDT's into improvised cache
            request.session['mdts'] = details
        except KeyError:
            pass

    # Selecting form depending on request type
    if search:
        form = DocumentSearchOptionsForm()
    else:
        form = DocumentIndexForm()

    if details and not details == 'error':
        # MDT's exist for ths docrule adding fields to form
        if search:
            fields = render_fields_from_docrules(details, request.POST or None, search=True)
        else:
            fields = render_fields_from_docrules(details, request.POST or None)
        if fields:
            form.setFields(fields)

    if request.POST:
        form.setData(request.POST)
        form.validation_ok()

    return form

def processDocumentIndexForm(request):
    """
    Handles document index form validation/population/data handling

    Works for search/indexing calls
    """
    form = initIndexesForm(request)
    secondary_indexes = {}
    search = determine_search_req(request)
    if form.validation_ok() or search:
        for key, field in form.fields.iteritems():
            # UPPERCASE Init if set attribute
            upper = False
            try:
                if field.is_uppercase:
                    upper = True
            except AttributeError:
                pass
            # FIXME: Nested exceptions.. bad
            try:
                # For dynamic form fields
                if not upper:
                    secondary_indexes[field.field_name] = form.data[unicode(key)].strip(' \t\n\r')
                else:
                    secondary_indexes[field.field_name] = form.data[unicode(key)].upper().strip(' \t\n\r')
            except (AttributeError, KeyError):
                try:
                    # For native form fields
                    if not upper:
                        secondary_indexes[key] = form.data[unicode(key)].strip(' \t\n\r')
                    else:
                        secondary_indexes[key] = form.data[unicode(key)].upper().strip(' \t\n\r')
                except KeyError:
                    pass

        if secondary_indexes:
            return secondary_indexes
        else:
            return None

def determine_search_req(request):
    """
    Helper to find out if provided request is search or indexing

    Returns Boolean value
    Currently determining if search by the url
    Warning! (MUST BE CHANGED IF RENAMING SEARCH URL)
    """
    if 'search' in request.path:
        search = True
    else:
        search = False
    return search

def get_mdts_for_documents(documents):
    """Returns list of mdts for provided documents list"""
    indexes = {}
    resp = None
    if documents:
        for document in documents:
            xes = document.mdt_indexes
            for ind in xes:
                indexes[ind] = ""
        resp = indexes.keys()
    return resp

def extract_secondary_keys_from_form(form):
    """Extracts secondary keys list from Indexes form."""
    keys_list = []
    for field_id, field in form.fields.iteritems():
        try:
            # if field is dynamic
            if field.field_name:
                if not field.__class__.__name__ == "DateField":
                    keys_list.append(field.field_name)
        except AttributeError:
            # standard field
            pass
    return keys_list

def _cleanup_session_var(request, var):
    """Cleanup Session var helper"""
    try:
        request.session[var] = None
        del request.session[var]
    except KeyError:
        pass

def cleanup_search_session(request):
    """Makes MDTUI forget abut searching keys entered before."""
    vars = ('document_search_dict', 'search_docrule_id',)
    for var in vars:
        _cleanup_session_var(request, var)

def cleanup_indexing_session(request):
    """Makes MDTUI forget abut indexing keys entered before."""
    vars = ('document_keys_dict', 'indexing_docrule_id', 'barcode',)
    for var in vars:
        _cleanup_session_var(request, var)

def cleanup_mdts(request):
    """Cleanup MDT's in improvised cache."""
    _cleanup_session_var(request, 'mdts')
