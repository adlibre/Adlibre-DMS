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
from forms import EditDocumentIndexForm
from forms_representator import render_fields_from_docrules
from forms_representator import get_mdts_for_docrule
from forms_representator import construct_edit_indexes_data
from adlibre.date_converter import str_date_to_couch

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
        # Form initial document creation date set on each request (Issue #731)
        form.fields['date'].initial = datetime.datetime.now()
        form.base_fields['date'].initial = datetime.datetime.now()

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
            index_tuple = process_indexes_field(key, field, form.data)
            if index_tuple:
                secondary_indexes[index_tuple[0]] = index_tuple[1]
        if secondary_indexes:
            return secondary_indexes
        else:
            return None

def processEditDocumentIndexForm(request, doc):
    form = initEditIndexesForm(request, doc)
    secondary_indexes = {}
    if form.validation_ok():
        for key, field in form.fields.iteritems():
            index_tuple = process_indexes_field(key, field, form.data)
            if index_tuple:
                secondary_indexes[index_tuple[0]] = index_tuple[1]
    if secondary_indexes:
        secondary_indexes['metadata_user_name'] = request.user.username
        secondary_indexes['metadata_user_id'] = str(request.user.pk)
        return secondary_indexes
    else:
        return None

def process_indexes_field(key, field, data):
    index_tuple = ()
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
            index_tuple = (field.field_name, data[unicode(key)].strip(' \t\n\r'))
        else:
            index_tuple = (field.field_name, data[unicode(key)].upper().strip(' \t\n\r'))
    except (AttributeError, KeyError):
        try:
            # For native form fields
            if not upper:
                index_tuple = (key, data[unicode(key)].strip(' \t\n\r'))
            else:
                index_tuple = (key, data[unicode(key)].upper().strip(' \t\n\r'))
        except KeyError:
            pass
    return index_tuple

def initEditIndexesForm(request, doc, given_indexes=None):
    """
    Edit form creating with population from existing document

    Inherits initIndexesForm with faking it's data to be rendered properly
    """
    initial_indexes = None
    docrule_id = str(doc.get_docrule().id)
    POST = request.POST
    # TODO: cashe MDTS
    mdts = get_mdts_for_docrule(docrule_id)
    # Faking POST request to populate from with initial indexes properly
    if not POST:
        # Constructing form indexes from previous data or doc metadata
        if given_indexes or doc.db_info:
            initial_indexes = construct_edit_indexes_data(mdts, given_indexes or doc.db_info)
            # Converting dates into strings if relevant.
            for key, value in initial_indexes.iteritems():
                # Metaclass based conversions to
                if value.__class__.__name__ == 'datetime':
                    initial_indexes[key] = value.strftime(settings.DATE_FORMAT)
            request.POST = initial_indexes
    form = EditDocumentIndexForm()
    if mdts and not mdts == 'error':
        # MDT's exist for this docrule adding fields to form
        fields = render_fields_from_docrules(mdts, request.POST or None)
        if fields:
            form.setFields(fields)
    if not POST:
        form.setData(initial_indexes)
    # TODO: test validation working here, if relevant
    else:
        form.setData(POST)
        form.validation_ok()
    return form

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

def unify_index_info_couch_dates_fmt(index_info):
    """
    Applies standardization to secondary keys 'date' type keys.
    """
    clean_info = {}
    index_keys = [key for key in index_info.iterkeys()]
    for index_key in index_keys:
        if not index_key=='date':
            try:
                value = index_info[index_key]
                index_date = datetime.datetime.strptime(value, settings.DATE_FORMAT)
                clean_info[index_key] = str_date_to_couch(value)
            except ValueError:
                clean_info[index_key] = index_info[index_key]
                pass
        else:
            clean_info[index_key] = index_info[index_key]
    return clean_info

def _cleanup_session_var(request, var):
    """Cleanup Session var helper"""
    try:
        request.session[var] = None
        del request.session[var]
    except KeyError:
        pass

def cleanup_search_session(request):
    """Makes MDTUI forget abut found search data."""
    vars = (
            'document_search_dict',
            'search_docrule_id',
            'search_mdt_id',
            'search_docrule_ids',
            'searching_docrule_id',
            'search_results',
    )
    for var in vars:
        _cleanup_session_var(request, var)

def cleanup_indexing_session(request):
    """Makes MDTUI forget abut indexing data entered before."""
    vars = (
            'document_keys_dict',
            'indexing_docrule_id',
            'barcode',
    )
    for var in vars:
        _cleanup_session_var(request, var)

def cleanup_mdts(request):
    """Cleanup MDT's in improvised cache."""
    _cleanup_session_var(request, 'mdts')
