"""
Module: SEARCH TYPE VARIATIONS GENERAL SEARCH HELPERS

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import logging
import datetime

from django.conf import settings

from operator import itemgetter

from forms_representator import SEARCH_STRING_REPR

from parallel_keys import ParallelKeysManager
from mdt_manager import MetaDataTemplateManager
from dmscouch.models import CouchDocument
from adlibre.date_converter import date_standardized
from adlibre.date_converter import str_date_to_couch

log = logging.getLogger('dms.mdtui.views')

DATE_RANGE_CONSTANTS = {
    'min': unicode(date_standardized('1960-01-01')),
    'max': unicode(date_standardized('2100-01-01')),
}

def document_date_range_only_search(cleaned_document_keys, docrule_ids):
    log.debug('Date range search only')
    resp_list = []
    for docrule_id in docrule_ids:
        startkey = [str_date_to_couch(cleaned_document_keys["date"]), docrule_id]
        endkey = [str_date_to_couch(cleaned_document_keys["end_date"]), docrule_id]
        # Getting all documents withing this date range
        all_docs = CouchDocument.view('dmscouch/search_date', startkey=startkey, endkey=endkey)
        # Filtering by docrule_ids and getting docs
        doc_list = []
        for document in all_docs:
            if document['metadata_doc_type_rule_id'] in docrule_ids:
                doc_list.append(document.get_id)
        # Appending to fetch docs list if not already there
        for doc_name in doc_list:
            if not doc_name in resp_list:
                resp_list.append(doc_name)

    documents = CouchDocument.view('_all_docs', keys=resp_list, include_docs=True )
    if documents:
        log.debug(
            'Search results by date range: from: "%s", to: "%s", docrules: "%s", documents: "%s"' %
            (startkey[0], endkey[0], docrule_ids, map(lambda doc: doc["id"], documents))
        )
    else:
        log.debug(
            'Search results by date range: from: "%s", to: "%s", docrules: "%s", documents: None' %
            (startkey[0], endkey[0], docrule_ids)
        )
    return documents

def document_date_range_with_keys_search(cleaned_document_keys, docrule_ids):
    log.debug('Date range search with additional keys specified')
    resp_set = {}
    docs_list = {}
    # For each docrule user search is requested
    for docrule_id in docrule_ids:
        # Getting list of date range filtered docs for each provided secondary key
        # Except for internal keys
        for key, value in cleaned_document_keys.iteritems():
            if not (key == 'date') and not (key == 'end_date'):
                if not value.__class__.__name__ == 'tuple':
                    # Normal search
                    startkey = convert_to_search_keys_for_date_range(cleaned_document_keys, key, docrule_id)
                    endkey = convert_to_search_keys_for_date_range(cleaned_document_keys, key, docrule_id, end=True)
                else:
                    # Got date range key
                    startkey = convert_to_search_keys_for_date_range(cleaned_document_keys, key, docrule_id, date_range=True)
                    endkey = convert_to_search_keys_for_date_range(cleaned_document_keys, key, docrule_id, end=True, date_range=True)
                if startkey and endkey:
                    # Appending results list to mixed set of results.
                    search_res = CouchDocument.view('dmscouch/search', startkey=startkey, endkey=endkey)
                    if docrule_id in resp_set.iterkeys():
                        resp_set[docrule_id].append(search_res)
                    else:
                        resp_set[docrule_id] = [search_res]
        # Extracting documents for each CouchDB response set.
        docs_list[docrule_id] = convert_search_res_for_range(resp_set, cleaned_document_keys, docrule_id)
    # Listing all documents to retrieve and getting them
    retrieve_docs = []
    for d_list in docs_list.itervalues():
        if d_list:
            for item in d_list:
                retrieve_docs.append(item)
    documents = CouchDocument.view('_all_docs', keys=retrieve_docs, include_docs=True)
    if documents:
        log.debug(
            'Search results by date range with additional keys: "%s", docrule: "%s", documents: "%s"' %
            (cleaned_document_keys, docrule_ids, map(lambda doc: doc["id"], documents))
        )
    else:
        log.debug(
            'Search results by date range with additional keys: "%s", docrule: "%s", documents: None' %
            (cleaned_document_keys, docrule_ids)
        )
    return documents

def cleanup_document_keys(document_keys):
    """
    Cleaning up key/value pairs that have empty values from CouchDB search request
    """
    del_list = []
    for key, value in document_keys.iteritems():
        if not value:
            del_list.append(key)
    for key in del_list:
        del document_keys[key]
    return document_keys

def ranges_validator(cleaned_document_keys):
    """
    Validates search keys for ranges.
    Adds range measures to single date keys
    """
    keys_list = [key for key in cleaned_document_keys.iterkeys()]
    for key in keys_list:
        # Secondary key START date provided. Checking if end period exists
        if key.endswith(SEARCH_STRING_REPR['field_label_from']):
            pure_key = key.rstrip(SEARCH_STRING_REPR['field_label_from'])
            desired_key = pure_key + SEARCH_STRING_REPR['field_label_to']
            if not desired_key in keys_list:
                cleaned_document_keys[desired_key] = DATE_RANGE_CONSTANTS['max']
        # Secondary key END date provided. Checking if start period exists
        if key.endswith(SEARCH_STRING_REPR['field_label_to']):
            pure_key = key.rstrip(SEARCH_STRING_REPR['field_label_to'])
            desired_key = pure_key + SEARCH_STRING_REPR['field_label_from']
            if not desired_key in keys_list:
                cleaned_document_keys[desired_key] = DATE_RANGE_CONSTANTS['min']
        # Indexing date MIN/MAX provided
        if u'date' in keys_list:
            if not u'end_date' in keys_list:
                cleaned_document_keys[u'end_date'] = DATE_RANGE_CONSTANTS['max']
        if u'end_date' in keys_list:
            if not u'date' in keys_list:
                cleaned_document_keys[u'date'] = DATE_RANGE_CONSTANTS['min']
    return cleaned_document_keys

def recognise_dates_in_search(cleaned_document_keys):
    """Finding ranges in cleaned keys and converting them to tuple pairs"""
    proceed = False
    keys_list = [key for key in cleaned_document_keys.iterkeys()]
    # TODO: implement this
    # Converting document date range to tuple for consistency
#    if 'date' in keys_list and 'end_date' in keys_list:
#        print 'Refactor! date range in search conversion'

    # Validating date fields (except main date field) exist in search query
    # Simple iterator to optimise calls without dates
    for key in keys_list:
        if key.endswith(SEARCH_STRING_REPR['field_label_from'] or SEARCH_STRING_REPR['field_label_to']):
            # we have to do this conversion
            proceed = True
    if proceed:
        # Validating if date fields are really date ranges
        for key in keys_list:
            if key.endswith(SEARCH_STRING_REPR['field_label_from']):
                # We have start of the dates sequence. Searching for an end key
                pure_key = key.rstrip(SEARCH_STRING_REPR['field_label_from'])
                desired_key = pure_key + SEARCH_STRING_REPR['field_label_to']
                if desired_key in keys_list:
                    # We have a date range. Constructing dates range tuple
                    from_value = cleaned_document_keys[key]
                    to_value = cleaned_document_keys[desired_key]
                    del cleaned_document_keys[key]
                    del cleaned_document_keys[desired_key]
                    cleaned_document_keys[pure_key]=(from_value, to_value)
    return cleaned_document_keys

def convert_search_res_for_range(resp_set, cleaned_document_keys, docrule_id):
    """
    Converts search results from type ANY to type ALL

    (evey key exist in document)
    For CouchDB documents list provided by search.
    """
    set_list = []
    all_docs = {}
    # Extracting documents mentions ang grouping by set
    for set in resp_set[docrule_id]:
        docs_ids_mentions = []
        for doc in set:
            docname = doc.get_id
            docs_ids_mentions.append(docname)
            all_docs[docname] = 0
        set_list.append(docs_ids_mentions)
    # Counting docs mentioned in all sets
    for doc in all_docs:
        for set in set_list:
            if doc in set:
                all_docs[doc] += 1
    # Comparing search mentions and adding to response if all keys match
    docs_ids_list = []
    for key, value in all_docs.iteritems():
        if value >= resp_set[docrule_id].__len__():
            docs_ids_list.append(key)
    return docs_ids_list

def convert_to_search_keys_for_date_range(document_keys, pkey, docrule_id, end=False, date_range=False):
    """
    Makes proper keys request set for 'dmscouch/search' CouchDB view.

    Takes date range into account.
    """
    req_params = []
    dd_range = document_date_range_present_in_keys(document_keys)
    for key, value in document_keys.iteritems():
        if key == pkey:
            if not date_range:
                # Simple key DB search request for document dates (or without document dates) range
                if not dd_range:
                    req_params = [key, value, docrule_id]
                else:
                    if not end:
                        req_params = [key, value, docrule_id, str_date_to_couch(document_keys["date"])]
                    else:
                        req_params = [key, value, docrule_id, str_date_to_couch(document_keys["end_date"])]
            else:
                # Assuming date range is our date tuple
                # Creating DB request for document dates (or without document dates) range
                if not end:
                    if dd_range:
                        req_params = [key, str_date_to_couch(value[0]), docrule_id, str_date_to_couch(document_keys["date"])]
                    else:
                        req_params = [key, str_date_to_couch(value[0]), docrule_id]
                else:
                    if dd_range:
                        req_params = [key, str_date_to_couch(value[1]), docrule_id, str_date_to_couch(document_keys["end_date"])]
                    else:
                        req_params = [key, str_date_to_couch(value[1]), docrule_id]
    return req_params

def document_date_range_present_in_keys(keys):
    """Helper to recognise document date range in search keys"""
    dd_range_present = False
    start = False
    end = False
    for key in keys:
        if key == 'date':
            start = True
        elif key == 'end_date':
            end = True
    if start or end:
        dd_range_present = True
    return dd_range_present

def search_results_by_date(documents):
    """Sorts search results into list by CouchDB document's 'created date'."""
    newlist = sorted(documents, key=itemgetter('metadata_created_date'))
    return newlist

def check_for_secondary_keys_pairs(input_keys_list, docrule_id):
    """Checks for parallel keys pairs if they already exist in Secondary Keys.

    Scenario:
    Existing Parallell key:
        JOHN 1234
    user enters
        MIKE 1234
    where MIKE already exists in combination with another numeric id we should still issue a warning.
    EG. The combination of key values is new! (even though no new keys have been created)
    """
    # Copying dictionary data and operating with them in function
    sec_keys_list = {}
    suspicious_keys_list = {}
    if input_keys_list:
        for key in input_keys_list.iterkeys():
            sec_keys_list[key] = input_keys_list[key]
        suspicious_keys_list = {}
    p_keys_manager = ParallelKeysManager()
    mdt_manager = MetaDataTemplateManager()
    keys_list = [key for key in sec_keys_list.iterkeys()]
    # Cleaning from not secondary keys
    for key in keys_list:
        if key == 'date' or key == 'description':
            del sec_keys_list[key]
    # Getting list of parallel keys for this docrule.
    mdts = mdt_manager.get_mdts_for_docrule(docrule_id)
    pkeys = p_keys_manager.get_parallel_keys_for_mdts(mdts)
    # Getting Pkeys lists.
    checked_keys = []
    for key in sec_keys_list.iterkeys():
        key_pkeys = p_keys_manager.get_parallel_keys_for_key(pkeys, key)
        pkeys_with_values = p_keys_manager.get_parallel_keys_for_pkeys(key_pkeys, sec_keys_list)
        # Checking if this parallel keys group already was checked.
        if not pkeys_with_values in checked_keys:
            checked_keys.append(pkeys_with_values)
            # Getting all keys for parallel key to check if it exists in any document metadata already.
            for pkey, pvalue in pkeys_with_values:
                documents = CouchDocument.view('dmscouch/search_autocomplete',
                                                key=[docrule_id, pkey, pvalue])
                # Appending non existing keys into list to be checked.
                if not documents:
                    suspicious_keys_list[pkey] = pvalue
    if suspicious_keys_list:
        log.debug('Found new unique key/values in secondary keys: ', suspicious_keys_list)
    else:
        log.debug('Found NO new unique key/values in secondary keys')
    return suspicious_keys_list

def get_mdts_by_names(names_list):
    """
    Proxy for clean implementation

    Planned to be refactored out upon implementing something like search manager
    or uniting main system core with search logic.
    """
    manager = MetaDataTemplateManager()
    mdts = manager.get_mdts_by_name(names_list)
    return mdts