"""
Module: Metadata Template UI Views

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

import json
import datetime
import logging

from restkit.client import RequestError

from django.core.urlresolvers import reverse
from django.core.cache import get_cache
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect, render_to_response, HttpResponseRedirect
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from api.decorators.group_required import group_required
from dmscouch.models import CouchDocument
from forms import DocumentUploadForm, BarcodePrintedForm, DocumentSearchOptionsForm
from core.document_processor import DocumentProcessor
from core.search import DMSSearchManager, DMSSearchQuery
from doc_codes.models import DocumentTypeRule
from view_helpers import initIndexesForm
from view_helpers import processDocumentIndexForm
from view_helpers import initEditIndexesForm
from view_helpers import processEditDocumentIndexForm
from view_helpers import get_mdts_for_documents
from view_helpers import extract_secondary_keys_from_form
from view_helpers import cleanup_search_session
from view_helpers import cleanup_indexing_session
from view_helpers import cleanup_mdts
from view_helpers import _cleanup_session_var
from view_helpers import unify_index_info_couch_dates_fmt
from search_helpers import check_for_forbidden_new_keys_created
from search_helpers import ranges_validator
from search_helpers import recognise_dates_in_search
from search_helpers import cleanup_document_keys
from search_helpers import check_for_secondary_keys_pairs
from search_helpers import get_mdts_by_names
from forms_representator import get_mdts_for_docrule
from forms_representator import make_mdt_select_form
from forms_representator import get_mdt_from_search_mdt_select_form
from forms_representator import make_document_type_select_form
from forms_representator import make_document_type_select
from parallel_keys import ParallelKeysManager
from data_exporter import export_to_csv
from security import SEC_GROUP_NAMES
from security import filter_permitted_docrules


log = logging.getLogger('dms.mdtui.views')

MDTUI_ERROR_STRINGS = {
    'NO_DOCRULE': 'You have not selected the Document Type.',
    'NO_DOC': 'Document does not exist',
    'NO_INDEX': 'You have not entered Document Indexing Data. Document will not be searchable by indexes.',
    'NO_S_KEYS': 'You have not defined Document Searching Options.',
    'NO_TYPE': 'You have not defined Document Type. Can only search by "Creation Date".',
    'NO_DB': 'Database Connection absent. Check CouchDB server connection.',
    'NO_DOCUMENTS_FOUND': 'Nothing to export because of empty documents results.',
    'NO_MDTS': 'No Meta Data templates found for selected Document Type.',
    'NEW_KEY_VALUE_PAIR': 'Adding new indexing key: ',
    'NO_MDT_NO_DOCRULE': 'You must select Meta Data Template or Document Type.',
    'NOT_VALID_INDEXING': 'You can not barcode or upload document without any indexes',
    'ERROR_EDIT_INDEXES_FINISHED': 'You can not visit this page directly',
    'LOCKED_KEY_ATTEMPT': 'You are trying to add forbidden value to a restricted key: ',
    'ADMINLOCKED_KEY_ATTEMPT': 'Only Administrator can add a value to this key: ',
    'EDIT_TYPE_WARNING': 'Note you will lose all your document indexes and enter them again for new document type.',
    'EDIT_TYPE_ERROR': 'You have selected the same document type.',
}

MUI_SEARCH_PAGINATE = getattr(settings, 'MUI_SEARCH_PAGINATE', 20)

@login_required
@group_required(SEC_GROUP_NAMES['search'])
def search_type(request, step, template='mdtui/search.html'):
    """Search Step 1: Select Search MDT"""
    warnings = []
    cleanup_indexing_session(request)

    # Initialising MDT or Docrule form according to data provided
    valid_call = True
    required_mdt = True
    required_docrule = True
    if request.POST:
        # Cleaning search session selections
        cleanup_search_session(request)
        cleanup_mdts(request)
        # Checking if docrule or mdt selected
        try:
            if request.POST['docrule']:
                required_mdt = False
        except KeyError:
            pass
        try:
            if request.POST['mdt']:
                required_docrule = False
        except KeyError:
            pass
        # Do not process in case docrule and MDT provided
        try:
            if request.POST['docrule'] and request.POST['mdt']:
                valid_call = False
                warnings.append(MDTUI_ERROR_STRINGS['NO_MDT_NO_DOCRULE'])
        except KeyError:
            pass

    # Rendering forms accordingly
    mdts_filtered_form = make_mdt_select_form(request.user, required_mdt)
    mdts_form = mdts_filtered_form(request.POST or None)
    docrules_filtered_form = make_document_type_select_form(request.user, required_docrule)
    docrules_form = docrules_filtered_form(request.POST or None)

    # POST Validation for either docrule OR mdt selected
    if request.POST and valid_call:
        if mdts_form.is_valid() and not required_docrule:
            mdts = None
            mdt_form_id = None
            try:
                mdt_form_id = mdts_form.data["mdt"]
            except KeyError:
                pass
            # CouchDB connection Felt down warn user
            if mdt_form_id:
                try:
                    mdt_names = get_mdt_from_search_mdt_select_form(mdt_form_id, mdts_filtered_form)
                    request.session['search_mdt_id'] = mdt_form_id
                    mdts = get_mdts_by_names(mdt_names)
                    docrules_list = mdts['1']['docrule_id']
                    if not request.user.is_superuser:
                        request.session['search_docrule_ids'] = filter_permitted_docrules(docrules_list, request.user)
                    else:
                        request.session['search_docrule_ids'] = docrules_list
                except RequestError:
                    warnings.append(MDTUI_ERROR_STRINGS['NO_DB'])
                if mdts:
                    request.session['mdts'] = mdts
                    if valid_call:
                        return HttpResponseRedirect(reverse('mdtui-search-options'))
            else:
                if not MDTUI_ERROR_STRINGS['NO_MDTS'] in warnings:
                    warnings.append(MDTUI_ERROR_STRINGS['NO_MDTS'])

        if docrules_form.is_valid() and not required_mdt:
            # If Docrule selected than MDT is not required and MDT's form is valid in fact
            docrule_form_id = None
            try:
                docrule_form_id = docrules_form.data["docrule"]
            except KeyError:
                pass
            if docrule_form_id:
                request.session['searching_docrule_id'] = docrule_form_id
                mdts = get_mdts_for_docrule(docrule_form_id)
                if mdts:
                    request.session['mdts'] = mdts
                    if valid_call:
                        return HttpResponseRedirect(reverse('mdtui-search-options'))
            else:
                if not MDTUI_ERROR_STRINGS['NO_MDTS'] in warnings:
                    warnings.append(MDTUI_ERROR_STRINGS['NO_MDTS'])
    else:
        # Populating forms with preexisting data if provided
        mdt_id = None
        docrule_id = None
        # Trying to set docrule if previously selected
        try:
            docrule_id = request.session['searching_docrule_id']
        except KeyError:
            pass
        if docrule_id:
            docrules_form = docrules_filtered_form({'docrule': docrule_id})

        # Trying to set mdt if previously selected
        try:
            mdt_id = request.session['search_mdt_id']
        except KeyError:
            pass
        if mdt_id:
            mdts_form = mdts_filtered_form({'mdt': mdt_id})

    context = {
        'warnings': warnings,
        'step': step,
        'mdts_form': mdts_form,
        'docrules_form': docrules_form,
    }
    return render_to_response(template, context, context_instance=RequestContext(request))


@login_required
@group_required(SEC_GROUP_NAMES['search'])
def search_options(request, step, template='mdtui/search.html'):
    """Search Step 2: Search Options"""
    warnings = []
    autocomplete_list = None
    mdt_id = None
    # Trying to get stuff we require OR warn user
    try:
        mdt_id = request.session['search_mdt_id']
    except KeyError:
        pass
    if not mdt_id:
        try:
            request.session['searching_docrule_id']
        except KeyError:
            warnings.append(MDTUI_ERROR_STRINGS['NO_MDTS'])

    # CouchDB connection Felt down warn user
    try:
        form = initIndexesForm(request)
        autocomplete_list = extract_secondary_keys_from_form(form)
    except (RequestError,AttributeError) :
        form = DocumentSearchOptionsForm
        warnings.append(MDTUI_ERROR_STRINGS['NO_DB'])

    if request.POST:
        try:
            secondary_indexes = processDocumentIndexForm(request)
        except RequestError:
            secondary_indexes = None
            warnings.append(MDTUI_ERROR_STRINGS['NO_DB'])

        if secondary_indexes:
            request.session['document_search_dict'] = secondary_indexes
            return HttpResponseRedirect(reverse('mdtui-search-results'))

    context = {
        'form': form,
        'warnings': warnings,
        'step': step,
        'autocomplete_fields': autocomplete_list,
    }
    return render_to_response(template, context, context_instance=RequestContext(request))

@login_required
@group_required(SEC_GROUP_NAMES['search'])
def search_results(request, step=None, template='mdtui/search.html'):
    """Search Step 3: Search Results"""
    document_keys = None
    docrule_ids = []
    document_names = []
    warnings = []
    mdts_list = []
    paginated_documents = []
    export = False
    cache_documents_for = 3600 # Seconds
    page = request.GET.get('page')
    force_clean_cache = request.session.get('cleanup_caches', False)
    # Sorting UI interactions
    sorting_field = request.POST.get('sorting_key', '') or ''
    order = request.POST.get('order', '') or ''
    if sorting_field and order:
        request.session["sorting_field"] = sorting_field
        request.session["order"] = order
    else:
        try:
            sorting_field = request.session["sorting_field"]
            order = request.session["order"]
        except KeyError:
            pass
    query_order = ''
    if order == "icon-chevron-up":
        query_order = "ascending"
    elif order == "icon-chevron-down":
        query_order = "descending"
    if not page:
        page = 1
    else:
        try:
            page = int(page)
        except ValueError:
            pass

    try:
        document_keys = request.session['document_search_dict']
    except KeyError:
        warnings.append(MDTUI_ERROR_STRINGS['NO_S_KEYS'])
    # Determining if we call export in fact instead of normal search and converting into internal variable
    if document_keys:
        if document_keys.__len__() == 1 and 'export_results' in document_keys:
            warnings.append(MDTUI_ERROR_STRINGS['NO_S_KEYS'])
        if 'export_results' in document_keys.iterkeys():
            if document_keys['export_results'] == 'export':
                export = True
            # Cleaning search dict afterwards
            del document_keys['export_results']
    # Getting docrules list for both search methods (Only one allowed)
    try:
        # trying to get id's list (for MDT search)
        docrule_ids = request.session['search_docrule_ids']
    except KeyError:
        pass
    if not docrule_ids:
        try:
            # If not exists making list for docrules search
            docrule_ids = [request.session['searching_docrule_id'],]
        except KeyError:
            pass

    log.debug(
        'search_results call for : page: "%s", docrule_id: "%s", document_search_dict: "%s"'
        % (page, docrule_ids, document_keys)
    )
    # turning document_search dict into something useful for the couch request
    clean_keys = cleanup_document_keys(document_keys)
    ck = ranges_validator(clean_keys)
    cleaned_document_keys = recognise_dates_in_search(ck)
    if not cleaned_document_keys:
        warnings.append(MDTUI_ERROR_STRINGS['NO_S_KEYS'])

    cache = get_cache('mui_search_results')
    # Caching by document keys and docrules list, as a cache key
    search_data = json.dumps(document_keys)+json.dumps(docrule_ids)+json.dumps(sorting_field)+json.dumps(order)
    cache_key = hash(search_data)
    if not force_clean_cache:
        cached_documents = cache.get(cache_key, None)
    else:
        cached_documents = None
        del request.session['cleanup_caches']
    if cleaned_document_keys and not cached_documents:
        if cleaned_document_keys:
            # TODO: speedup sorting using document_names from cache not to search again.
            # Redefining proper sorting results request
            if sorting_field:
                if sorting_field == "Creation Date":
                    sorting_field_query = "metadata_created_date"
                elif sorting_field == "Description":
                    sorting_field_query = "metadata_description"
                elif sorting_field == "Type":
                    sorting_field_query = "metadata_doc_type_rule_id"
                else:
                    sorting_field_query = sorting_field
            else:
                sorting_field_query = ''
            # Using DMS actual search method for this
            query = DMSSearchQuery({
                'document_keys': cleaned_document_keys,
                'docrules': docrule_ids,
                'only_names': True,
                'sorting_key': sorting_field_query,
                'sorting_order': query_order,
            })
            search_results = DMSSearchManager().search_dms(query)
            search_errors = search_results.get_errors()
            if search_errors:
                for error in search_errors:
                    warnings.append(error)
                document_names = []
            else:
                document_names = search_results.get_document_names()
        cache.set(cache_key, document_names, cache_documents_for)
        log.debug('search_results: Got search results with amount of results: %s' % document_names)
    else:
        if cleaned_document_keys:
            document_names = cached_documents
            log.debug('search_results: Getting results from cache. Num of results: %s' % document_names)

    # Produces a CSV file from search results
    if (document_names and step == 'export') or (document_names and export):
        log.debug('search_results exporting found documents to CSV')
        # Getting all the documents from
        documents = DMSSearchManager().get_found_documents(document_names)
        mdts_list = get_mdts_for_documents(documents)
        csv_response = export_to_csv(document_keys, mdts_list, documents)
        return csv_response

    # Paginating list of documents and retrieving only required one's
    if document_keys:
        paginator = Paginator(document_names, MUI_SEARCH_PAGINATE)
        try:
            paginated_documents = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            paginated_documents = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), deliver last page of results.
            paginated_documents = paginator.page(paginator.num_pages)
        paginated_documents_objects = DMSSearchManager().get_found_documents(paginated_documents.object_list)
        paginated_documents.object_list = paginated_documents_objects
        mdts_list = get_mdts_for_documents(paginated_documents_objects)

    context = { 'step': step,
                'paginated_documents': paginated_documents,
                'page': page,
                'document_keys': cleaned_document_keys,
                'mdts': mdts_list,
                'warnings': warnings,
                'sorting_field': sorting_field,
                'order': order
                }
    return render_to_response(template, context, context_instance=RequestContext(request))

@login_required
def view_object(request, code, step, template='mdtui/view.html'):
    """View PDF Document"""
    # TODO: Add certain revision view possibility for "edit revisions" view
    revision = request.GET.get('revision', None)
    pdf_url = reverse('mdtui-download-pdf', kwargs={'code': code})
    processor = DocumentProcessor()
    document = processor.read(code, options={'only_metadata': True, 'user': request.user, 'revision': revision})
    mimetype = document.get_mimetype()
    context = {
        'pdf_url': pdf_url,
        'code': code,
        'step': step,
        'mimetype': mimetype,
        'revision': revision,
    }
    if not document.get_file_revisions_data():
        db = document.get_db_info()
        if 'metadata_doc_type_rule_id' in db.iterkeys() and db['metadata_doc_type_rule_id']:
            # Indexed Document with 0 revisions (Displaying stub document from static)
            # TODO: expand this for branding. (Using custom DMS stub document)
            stub_doc_url = settings.STATIC_URL + 'pdf/stub_document.pdf'
            context.update({'mimetype': 'stub_document', 'pdf_url': stub_doc_url})
    return render(request, template, context)

@login_required
@group_required(SEC_GROUP_NAMES['edit_index'])
def edit(request, code, step='edit', template='mdtui/indexing.html'):
    """Indexing step: Edit. Made for editing indexes of document that is indexed already."""
    context = {}
    warnings = []
    error_warnings = []
    form = False
    processor = DocumentProcessor()
    autocomplete_list = None
    changed_indexes = None
    # Storing cancel (return back from edit) url
    try:
        return_url = request.session['edit_return']
    except KeyError:
        try:
            return_url = request.META['HTTP_REFERER']
            request.session['edit_return'] = return_url
        except KeyError:
            return_url = '/'
            pass
        pass

    # Only preserve indexes if returning from edit indexes confirmation step
    if 'HTTP_REFERER' in request.META and request.META['HTTP_REFERER'].endswith(reverse('mdtui-edit-finished')):
        try:
            changed_indexes = request.session['edit_processor_indexes']
        except KeyError:
            pass

    log.debug('indexing_edit view called with return_url: %s, changed_indexes: %s' % (return_url, changed_indexes))
    doc = processor.read(code, {'user': request.user, 'only_metadata': True})
    if not processor.errors and not doc.marked_deleted:
        if not request.POST:
            form = initEditIndexesForm(request, doc, changed_indexes)
            # Setting context variables required for autocomplete
            docrule_id = str(doc.get_docrule().id)
            request.session['indexing_docrule_id'] = docrule_id
            request.session['edit_mdts'] = get_mdts_for_docrule(docrule_id)
        else:
            old_db_info = doc.get_db_info()
            secondary_indexes = processEditDocumentIndexForm(request, doc)
            request.session['edit_processor_indexes'] = secondary_indexes
            request.session['edit_index_barcode'] = code
            old_docs_indexes = {'description': old_db_info['description']}
            for index_name, index_value in old_db_info['mdt_indexes'].iteritems():
                # Converting Old index dates to render according to DMS date format
                if index_value.__class__.__name__ == 'datetime':
                    old_docs_indexes[index_name] = datetime.datetime.strftime(index_value, settings.DATE_FORMAT)
                else:
                    old_docs_indexes[index_name] = index_value
            request.session['old_document_keys'] = old_docs_indexes
            return HttpResponseRedirect(reverse('mdtui-edit-finished'))
    else:
        for error in processor.errors:
            # Intercepting type Exception and using it's message or using error.__str__
            if not error.__class__.__name__ == 'unicode' and 'parameter' in error.__dict__.iterkeys():
                error_warnings.append(error.parameter)
            else:
                error_warnings.append(error)
        if doc.marked_deleted:
            error_warnings.append(MDTUI_ERROR_STRINGS['NO_DOC'])

    if form:
        autocomplete_list = extract_secondary_keys_from_form(form)
        # No form is possible when document does not exist
        context.update( {'form': form,} )
    context.update( { 'step': step,
                      'doc_name': code,
                      'type_name': doc.get_docrule().title,
                      'warnings': warnings,
                      'autocomplete_fields': autocomplete_list,
                      'edit_return': return_url,
                      'error_warnings': error_warnings,
                      })
    return render(request, template, context)

@login_required
@group_required(SEC_GROUP_NAMES['edit_index'])
def edit_type(request, code, step='edit_type', template='mdtui/indexing.html'):
    """Indexing step: Edit. Editing document type (in fact document rename)"""
    context = {}
    warnings = [MDTUI_ERROR_STRINGS['EDIT_TYPE_WARNING'], ]
    error_warnings = []
    form = False
    processor = DocumentProcessor()
    return_url = reverse('mdtui-edit', kwargs={'code': code})

    log.debug('indexing_edit_type view called with code: %s' % code)
    doc = processor.read(code, {'user': request.user,})
    if not processor.errors:
        empty_form = make_document_type_select_form(request.user, True, doc.get_docrule())
        form = empty_form(request.POST or None)
        if request.POST:
            if form.is_valid():
                docrule = form.cleaned_data['docrule']
                current_docrule = doc.get_docrule()
                if not docrule == current_docrule:
                    options = {
                        'user': request.user,
                        'new_type': docrule,
                    }
                    doc = processor.update(code, options)
                    if not processor.errors:
                        return HttpResponseRedirect(reverse('mdtui-edit', kwargs={'code': doc.get_filename()}))
                else:
                    warnings = [MDTUI_ERROR_STRINGS['EDIT_TYPE_ERROR'], ]
    # Can cause errors in two places here (on doc read and update)
    if processor.errors:
        for error in processor.errors:
            error_warnings.append(error)
    context.update({
        'step': step,
        'doc_name': code,
        'docrule': doc.get_docrule(),
        'warnings': warnings,
        'form': form,
        'type_edit_return': return_url,
        'error_warnings': error_warnings,
    })
    return render(request, template, context)

@login_required
@group_required(SEC_GROUP_NAMES['edit_index'])
def edit_file_delete(request, code):
    """Deletes specified code or revision from system (Marks deleted)"""
    # Decision of where to go back after or instead of removal
    return_url = reverse('mdtui-home')
    if 'edit_return' in request.session:
        return_url = request.session['edit_return']
    if request.method == 'POST':
        revision = request.POST.get('revision', False)

        if revision:
            return_url = reverse('mdtui-edit-revisions', kwargs={'code': code})
        processor = DocumentProcessor()
        processor.read(code, {'user': request.user, 'only_metadata': True})
        if not processor.errors:
            # Selecting to delete (Mark deleted) revision or whole document
            options = {'user': request.user}
            if revision:
                options['mark_revision_deleted'] = revision
            else:
                options['mark_deleted'] = True
            processor.delete(code, options)
            if not processor.errors:
                request.session['cleanup_caches'] = True
                return HttpResponseRedirect(return_url)
    return HttpResponseRedirect(return_url)

@login_required
@group_required(SEC_GROUP_NAMES['index'])
def edit_file_revisions(request, code, step='edit_revisions', template='mdtui/indexing.html'):
    """Editing file revisions for given code"""
    form = DocumentUploadForm(request.POST or None, request.FILES or None)
    revision_file = request.FILES.get('file', None)
    errors = []
    context = {
        'step': step,
        'doc_name': code,
        'upload_form': form,
        'barcode': None,  # for compatibility with scripts (We are reusing modal scripts in templates)
    }
    processor = DocumentProcessor()
    doc = processor.read(code, {'user': request.user, 'only_metadata': True})
    if not processor.errors and not doc.marked_deleted:
        if revision_file and form.is_valid():
            options = {
                'user': request.user,
                'update_file': revision_file,
            }
            processor.update(code, options)
            if not processor.errors:
                return HttpResponseRedirect(request.path)
            else:
                errors.append(processor.errors)
        frd = doc.get_file_revisions_data()
        context.update({
            'file_revision_data': frd,
            'file_revision_data_order_list': sorted(frd.iterkeys()),
            'index_data': doc.get_db_info(),
        })
    else:
        errors = [MDTUI_ERROR_STRINGS['NO_DOC'] + '. Maybe you should go index it first?']
    context.update({'error_warnings': errors})
    return render(request, template, context)

@login_required
@group_required(SEC_GROUP_NAMES['edit_index'])
def edit_result(request, step='edit_finish', template='mdtui/indexing.html'):
    """Confirmation step for editing indexes"""
    # initialising context
    required_vars = ('edit_processor_indexes', 'edit_index_barcode', 'old_document_keys', 'edit_return', "edit_mdts")
    variables = {}
    warnings = []
    for var in required_vars:
        try:
            variables[var] = request.session[var]
        except KeyError:
            variables[var] = ''
            # Error handling into warnings
            if not var == 'edit_return':
                error_name = MDTUI_ERROR_STRINGS['ERROR_EDIT_INDEXES_FINISHED']
                log.error('indexing_finished error: variable: %s,  %s' % (var, error_name))
                if not error_name in warnings:
                    warnings.append(error_name)
            pass
    log.debug('indexing_edit_result called with: step: "%s", variables: "%s",' % (step, variables))

    if request.POST:
        code = variables['edit_index_barcode']
        processor = DocumentProcessor()
        options = {
            'new_indexes': variables['edit_processor_indexes'],
            'user': request.user,
        }
        processor.update(code, options=options)
        if not processor.errors:
            # cleanup session here because editing is finished
            for var in required_vars:
                _cleanup_session_var(request, var)
            return HttpResponseRedirect(variables['edit_return'])
        else:
            for error in processor.errors:
                warnings.append(error)
    # Building new indexes for confirmation rendering
    context_secondary_indexes = {}
    if 'edit_processor_indexes' in variables.iterkeys() and variables['edit_processor_indexes']:
        for index, value in variables['edit_processor_indexes'].iteritems():
            if not index in ['metadata_user_name', 'metadata_user_id']:
                context_secondary_indexes[index] = value
    context = {
        'step': step,
        'document_keys': context_secondary_indexes,
        'barcode': variables['edit_index_barcode'],
        'old_document_keys': variables['old_document_keys'],
        'edit_return': variables['edit_return'],
        'warnings': warnings,
    }
    return render(request, template, context)

@login_required
@group_required(SEC_GROUP_NAMES['index'])
def indexing_select_type(request, step=None, template='mdtui/indexing.html'):
    """Indexing: Step 1 : Select Document Type"""
    # Context init
    context = {'step': step,}
    docrule = None
    active_docrule = None
    warnings = []
    docrules_list = make_document_type_select(user=request.user)
    cleanup_search_session(request)
    cleanup_mdts(request)
    log.debug('indexing_select_type view called with docrule: %s' % docrule)
    if request.POST:
        for item, value in request.POST.iteritems():
            if not item == u'csrfmiddlewaretoken':
                docrule = int(item)
        request.session['indexing_docrule_id'] = docrule
        mdts = get_mdts_for_docrule(docrule)
        if mdts:
            request.session['mdts'] = mdts
            return HttpResponseRedirect(reverse('mdtui-index-details'))
        else:
            warnings.append(MDTUI_ERROR_STRINGS['NO_MDTS'])
    else:
        # initializing form with previously selected docrule.
        try:
            docrule = request.session['indexing_docrule_id']
        except KeyError:
            pass
        if docrule:
            active_docrule = docrule

    context.update({
        'active_docrule': active_docrule,
        'docrules_list': docrules_list,
        'warnings': warnings,
    })
    return render_to_response(template, context, context_instance=RequestContext(request))


@login_required
@group_required(SEC_GROUP_NAMES['index'])
def indexing_details(request, step=None, template='mdtui/indexing.html'):
    """Indexing: Step 2 : Index Details"""
    # Context init
    context = {}
    document_keys = None
    warnings = []
    errors = []
    cleanup_search_session(request)
    docrule_id = None

    try:
        docrule_id = request.session['indexing_docrule_id']
    except KeyError:
        warnings.append(MDTUI_ERROR_STRINGS['NO_DOCRULE'])

    try:
        document_keys = request.session["document_keys_dict"]
    except KeyError:
        pass

    log.debug('indexing_details view called with docrule_id: %s, document_keys: %s, warnings: %s' % (docrule_id, document_keys, warnings))
    if request.POST:
        secondary_indexes = processDocumentIndexForm(request)
        if secondary_indexes:
            request.session["document_keys_dict"] = secondary_indexes
            # Checking for forbidden keys and changing view behaviour if found
            forbidden_keys = check_for_forbidden_new_keys_created(secondary_indexes, docrule_id, request.user)
            if forbidden_keys:
                for forbidden_key in forbidden_keys:
                    if forbidden_key[1] == 'adminlock':
                        errors.append(MDTUI_ERROR_STRINGS['ADMINLOCKED_KEY_ATTEMPT'] + forbidden_key[0])
                    elif forbidden_key[1] == 'locked':
                        errors.append(MDTUI_ERROR_STRINGS['LOCKED_KEY_ATTEMPT'] + forbidden_key[0])
                # Reinitializing form
                form = initIndexesForm(request)
            else:
                # Success, allocate barcode and move on
                dtr = DocumentTypeRule.objects.get(pk=docrule_id)
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
                      'error_warnings': errors,
                    })
    return render_to_response(template, context, context_instance=RequestContext(request))


@login_required
@group_required(SEC_GROUP_NAMES['index'])
def indexing_source(request, step=None, template='mdtui/indexing.html'):
    """Indexing: Step 3: Upload File / Associate File / Print Barcode"""
    context = {}
    warnings = []
    valid_call = True
    temp_vars = {}
    upload_file = None
    # Check session variables, init context and add proper user warnings
    for var_name, context_var, action in [
        ('document_keys', "document_keys_dict", 'NO_INDEX'),
        ('barcode', 'barcode', 'NO_INDEX'),
        ('index_info', 'document_keys_dict', 'NO_S_KEYS'),
        ('docrule', 'indexing_docrule_id', 'NO_DOCRULE'),
    ]:
        try:
            temp_vars[var_name] = None # Make sure it will definitely be there (Proper init)
            temp_var = request.session[context_var]
            temp_vars[var_name] = temp_var
        except KeyError:
            valid_call = False
            if not MDTUI_ERROR_STRINGS[action] in warnings:
                warnings.append(MDTUI_ERROR_STRINGS[action])
    document_keys = temp_vars['document_keys']
    barcode = temp_vars['barcode']
    index_info = temp_vars['index_info']
    docrule = str(temp_vars['docrule'])

    # Init Forms correctly depending on url posted
    if request.GET.get('uploaded') is None:
        upload_form = DocumentUploadForm()
    else:
        upload_form = DocumentUploadForm(request.POST or None, request.FILES or None)

    if request.GET.get('barcoded') is None:
        barcode_form = BarcodePrintedForm()
    else:
        barcode_form = BarcodePrintedForm(request.POST or None)

    log.debug('indexing_source view called with document_keys: %s, barcode: %s, index_info: %s, docrule: %s' % (document_keys, barcode, index_info, docrule))
    # Appending warnings for creating a new parrallel key/value pair.
    new_sec_key_pairs = check_for_secondary_keys_pairs(index_info, docrule)
    if new_sec_key_pairs:
        for new_key, new_value in new_sec_key_pairs.iteritems():
            warnings.append(MDTUI_ERROR_STRINGS['NEW_KEY_VALUE_PAIR'] + new_key + ': ' + new_value)

    if upload_form.is_valid() or barcode_form.is_valid() and valid_call:
        if valid_call:
            # Unifying dates to CouchDB storage formats.
            # TODO: maybe make it a part of the CouchDB storing manager.
            clean_index = unify_index_info_couch_dates_fmt(index_info)

            # Storing into DMS with main Document Processor and current indexes
            processor = DocumentProcessor()
            options = {
                'user': request.user,
                'index_info': clean_index,
                'barcode': barcode,
            }
            if upload_form.is_valid():
                upload_file = upload_form.files['file']
            else:
                options['only_metadata'] = True
            processor.create(upload_file, options)

            if not processor.errors:
                return HttpResponseRedirect(reverse('mdtui-index-finished'))
            else:
                # FIXME: dodgy error handling
                return HttpResponse(str(processor.errors))
        else:
            warnings.append(MDTUI_ERROR_STRINGS['NOT_VALID_INDEXING'])

    context.update({
        'step': step,
        'valid_call': valid_call,
        'upload_form': upload_form,
        'barcode_form': barcode_form,
        'document_keys': document_keys,
        'warnings': warnings,
        'barcode': barcode,
    })
    return render_to_response(template, context, context_instance=RequestContext(request))

@login_required
@group_required(SEC_GROUP_NAMES['index'])
def indexing_finished(request, step=None, template='mdtui/indexing.html'):
    """Indexing: Step 4: Finished"""
    context = { 'step': step,  }
    for name, item in ( ('document_keys', 'document_keys_dict'),
                        ('barcode', 'barcode'),
                        ('docrule_id', 'indexing_docrule_id') ):
        if item in request.session:
            try:
                context.update({name: request.session[item],})
            except KeyError:
                pass

    log.debug('indexing_finished called with: step: "%s", context: "%s",' %
              (step, context))

    # Document uploaded forget everything
    cleanup_indexing_session(request)
    cleanup_mdts(request)
    return render(request, template, context)


@login_required
def mdt_parallel_keys(request):
    """
    Returns suggestions for typeahead.

    Renders parallel keys and simple "one key" requests.
    NB, Don't rename this to parallel_keys. It conflicts with imported lib of same name.
    """
    # Limiting autocomplete to start searching from NUMBER of keys
    # Change it to 0 to search all, starting from empty value
    letters_limit = 2
    # Limit of response results
    suggestions_limit = 8

    valid_call = True
    autocomplete_req = None
    docrule_id = None
    key_name = None
    doc_mdts={}
    resp = []
    # Trying to get docrule for indexing calls
    try:
        docrule_id = request.session['indexing_docrule_id']
    except KeyError:
        pass

    # Trying to get docrule for searching calls
    try:
        if not docrule_id:
            docrule_id = request.session['searching_docrule_id']
        # No docrule present in session. Invalidating view call.
        if not docrule_id:
            valid_call = False
    except KeyError:
        pass

    try:
        key_name = request.POST[u'key_name']
        autocomplete_req = request.POST[u'autocomplete_search'].strip(' \t\n\r')
    except KeyError:
        valid_call = False

    try:
        doc_mdts = request.session["mdts"]
    except KeyError:
        pass

    try:
        doc_mdts = request.session["edit_mdts"]
    except KeyError:
        pass

    # Nothing queried for autocomplete and no MDTS found. Invalidating call
    if not autocomplete_req or not doc_mdts:
        valid_call = False

    log.debug(
        'mdt_parallel_keys call: docrule_id: "%s", key_name: "%s", autocomplete: "%s" Call is valid: "%s", MDTS: %s' %
        (docrule_id, key_name, autocomplete_req, valid_call, doc_mdts)
    )
    # TODO: Can be optimised for huge document's amounts in future (Step: Scalability testing)
    """
    # We can collect all the documents keys for each docrule in MDT related to requested field and load them into queue.
    # Then check them for duplicated values and/or make a big index with all the document's keys in it
    # to fetch only document indexes we need on first request. (Instead of 'include_docs=True')
    # E.g. Make autocomplete Couch View to output index with all Document's mdt_indexes ONLY.
    #
    # Total amount of requests will be 3 instead of 2 (for 2 docrules <> 1 MDT) but they will be smaller.
    # And that will be good for say 1 000 000 documents. However, DB size will rise too.
    # (Because we will copy all the doc's indexes into separate specific response for Typehead in fact)
    # Final step is to load all unique suggestion documents that are passed through our filters.
    # (Or if we will build this special index it won't be necessary)
    # (Only if we require parallel keys to be parsed)
    # It can be done by specifying multiple keys that we need to load here. ('key' ws 'keys' *args in CouchDB request)
    """
    if valid_call:
        manager = ParallelKeysManager()
        for mdt in doc_mdts.itervalues():
            mdt_keys =[mdt[u'fields'][mdt_key][u'field_name'] for mdt_key in mdt[u'fields']]
            log.debug('mdt_parallel_keys selected for suggestion MDT-s keys: %s' % mdt_keys)
            if key_name in mdt_keys:
                # Autocomplete key belongs to this MDT
                mdt_docrules = mdt[u'docrule_id']
                if docrule_id:
                    # In case of index get Parallel keys from all MDT for docrule
                    mdt_fields = manager.get_keys_for_docrule(docrule_id, doc_mdts)
                else:
                    # In case of search get only from selected MDT
                    mdt_fields = manager.get_parallel_keys_for_mdts(doc_mdts)
                pkeys = manager.get_parallel_keys_for_key(mdt_fields, key_name)
                for docrule in mdt_docrules:
                    # Only search through another docrules if response is not full
                    if resp.__len__() > suggestions_limit:
                        break
                    # db call to search in docs
                    if pkeys:
                        # Making no action if not enough letters
                        if autocomplete_req.__len__() > letters_limit:
                            # Suggestion for several parallel keys
                            documents = CouchDocument.view(
                                'dmscouch/search_autocomplete',
                                startkey=[docrule, key_name, autocomplete_req],
                                endkey=[docrule, key_name, unicode(autocomplete_req)+u'\ufff0'],
                                include_docs=True,
                                reduce=False
                            )
                            # Adding each selected value to suggestions list
                            for doc in documents:
                                # Only append values until we've got 'suggestions_limit' results
                                if resp.__len__() > suggestions_limit:
                                    break
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
                            startkey=[docrule, key_name, autocomplete_req],
                            endkey=[docrule, key_name, unicode(autocomplete_req)+u'\ufff0'],
                            group = True,
                        )
                        # Fetching unique responses to suggestion set
                        for doc in documents:
                            # Only append values until we've got 'suggestions_limit' results
                            if resp.__len__() > suggestions_limit:
                                break
                            resp_array = {key_name: doc['key'][2]}
                            suggestion = json.dumps(resp_array)
                            if not suggestion in resp:
                                resp.append(suggestion)
    log.debug('mdt_parallel_keys response: %s' % resp)
    return HttpResponse(json.dumps(resp))


@login_required
def download_pdf(request, code):
    """Returns Document For Download"""
    # right now we just redirect to API, but in future we might want to decouple from API app.
    revision = request.GET.get('revision', None)
    url = reverse('api_file', kwargs={'code': code, 'suggested_format': 'pdf'})
    if revision:
        url += '?r=%s' % revision
    log.debug('GET pdf from api url: %s for user: %s' % (url, unicode(request.user)))
    return redirect(url)
