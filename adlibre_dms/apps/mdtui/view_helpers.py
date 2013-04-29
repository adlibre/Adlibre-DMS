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

    initial_data = {}
    if not search:
        if 'document_keys_dict' in request.session.iterkeys():
            initial_data = request.session['document_keys_dict']

    # Selecting form depending on request type
    if search:
        form = DocumentSearchOptionsForm()
    else:
        form = DocumentIndexForm()
        # Form initial document creation date set on each request (Issue #731)
        if not initial_data:
            form.fields['date'].initial = datetime.datetime.now()
            form.base_fields['date'].initial = datetime.datetime.now()
        else:
            if 'date' in initial_data.iterkeys():
                form.fields['date'].initial = datetime.datetime.strptime(initial_data['date'], settings.DATE_FORMAT)
                form.base_fields['date'].initial = datetime.datetime.strptime(initial_data['date'], settings.DATE_FORMAT)

    if details and not details == 'error':
        # MDT's exist for ths docrule adding fields to form
        if search:
            fields = render_fields_from_docrules(details, request.POST or None, search=True)
        else:
            fields = render_fields_from_docrules(details, request.POST or None)
        if fields:
            form.setFields(fields)

    if request.POST:
        # Populating ata into form for POST data
        form.setData(request.POST)
    elif initial_data:
        # Populating initial data for partially proper form rendering
        form.populateFormSecondary(initial_data)
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
    """Convertor of field sbmited data to DMS secondary key"""
    index_tuple = ()
    # UPPERCASE Init if set attribute
    force_upper = False
    if "is_uppercase" in field.__dict__ and field.is_uppercase == True:
        force_upper = True
    # Choices field processing init
    choice_field = False
    if field.__class__.__name__ == "ChoiceField":
        choice_field = True
    if choice_field:
        fvalue = False
        if unicode(key) in data.iterkeys():
            searched_value = int(data[unicode(key)])
            for choice in field.choices:
                if choice[0]==searched_value:
                    fvalue = choice[1]
                    break
        else:
            for choice in field.choices:
                if choice[0]==key:
                    fvalue = choice[1]
                    break
        if fvalue:
            index_tuple = (field.field_name, fvalue)
    else:
        if unicode(key) in data.iterkeys():
            if "field_name" in field.__dict__:
                # For Dynamic form fields
                if not force_upper:
                    index_tuple = (field.field_name, data[unicode(key)].strip(' \t\n\r'))
                else:
                    index_tuple = (field.field_name, data[unicode(key)].upper().strip(' \t\n\r'))
            else:
                # For native form fields
                if not force_upper:
                    index_tuple = (key, data[unicode(key)].strip(' \t\n\r'))
                else:
                    index_tuple = (key, data[unicode(key)].upper().strip(' \t\n\r'))
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
    """Extracts text (autocomplete capable) secondary keys list from Indexes form."""
    keys_list = []
    for field_id, field in form.fields.iteritems():
        if 'field_name' in field.__dict__.iterkeys():
            if field.field_name:
                f_name = field.__class__.__name__
                if f_name != "DateField" or f_name != "ChoiceField":
                    keys_list.append(field.field_name)
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
                # Simple check if we can convert it...
                datetime.datetime.strptime(value, settings.DATE_FORMAT)
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
            "edit_mdts",
    )
    for var in vars:
        _cleanup_session_var(request, var)

def cleanup_indexing_session(request):
    """Makes MDTUI forget abut indexing data entered before."""
    vars = (
            'document_keys_dict',
            'indexing_docrule_id',
            'barcode',
            "edit_mdts",
    )
    for var in vars:
        _cleanup_session_var(request, var)

def cleanup_mdts(request):
    """Cleanup MDT's in improvised cache."""
    _cleanup_session_var(request, 'mdts')
