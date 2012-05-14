"""
Module: SEARCH TYPE VARIATIONS GENERAL SEARCH HELPERS
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

from dmscouch.models import CouchDocument
import logging
from forms_representator import SEARCH_STRING_REPR

DATE_RANGE_CONSTANTS = {
    'min': u'1960-01-01',
    'max': u'2100-01-01'
}

log = logging.getLogger('dms.mdtui.views')

def document_date_range_only_search(cleaned_document_keys, docrule_id):
    log.debug('Date range search only')
    startkey = [str_date_to_couch(cleaned_document_keys["date"]), docrule_id]
    endkey = [str_date_to_couch(cleaned_document_keys["end_date"]), docrule_id]
    # Getting all documents withing this date range
    all_docs = CouchDocument.view('dmscouch/search_date', startkey=startkey, endkey=endkey)
    # Filtering by docrule_id and getting docs
    resp_list = filter_couch_docs_by_docrule_id(all_docs, docrule_id)
    documents = CouchDocument.view('_all_docs', keys=resp_list, include_docs=True )
    if documents:
        log.debug(
            'Search results by date range: from: "%s", to: "%s", docrule: "%s", documents: "%s"' %
            (startkey[0], endkey[0], docrule_id, map(lambda doc: doc["id"], documents))
        )
    else:
        log.debug(
            'Search results by date range: from: "%s", to: "%s", docrule: "%s", documents: None' %
            (startkey[0], endkey[0], docrule_id)
        )
    return documents

def document_date_range_with_keys_search(cleaned_document_keys, docrule_id):
    log.debug('Date range search with additional keys specified')
    resp_set = []
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
                search_res = CouchDocument.view('dmscouch/search', startkey=startkey, endkey=endkey)
                resp_set.append(search_res)
    docs_list = convert_search_res_for_range(resp_set, cleaned_document_keys)
    raw_docs = CouchDocument.view('_all_docs', keys=docs_list, include_docs=True)
    docs_by_docrule_filter = filter_couch_docs_by_docrule_id(raw_docs, docrule_id)
    if docs_list == docs_by_docrule_filter:
        documents = raw_docs
    else:
        documents = CouchDocument.view('_all_docs', keys=docs_by_docrule_filter, include_docs=True)
    if documents:
        log.debug(
            'Search results by date range with additional keys: "%s", docrule: "%s", documents: "%s"' %
            (cleaned_document_keys, docrule_id, map(lambda doc: doc["id"], documents))
        )
    else:
        log.debug(
            'Search results by date range with additional keys: "%s", docrule: "%s", documents: None' %
            (cleaned_document_keys, docrule_id)
        )
    return documents

def filter_couch_docs_by_docrule_id(documents, docrule_id):
    """
    Helper for date range search primary to filter documents by given docrule
    """
    doc_ids_list = []
    for document in documents:
        if document['metadata_doc_type_rule_id'] == docrule_id:
            doc_ids_list.append(document.get_id)
    return doc_ids_list

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
    """
    Finding ranges in cleaned keys and converting them to tuple pairs
    """
    proceed = False
    keys_list = [key for key in cleaned_document_keys.iterkeys()]
    # TODO: implement this
    # Converting document date range to tuple fro consistency
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

def convert_search_res_for_range(resp_set, cleaned_document_keys):
    """
    Converts search results for set of keys CouchDB responses with optional date range
    from type ANY to type ALL (evey key exist in document)
    """
    set_list = []
    all_docs = {}
    # Extracting documents mentions ang grouping by set
    for set in resp_set:
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
        if value >= resp_set.__len__():
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
                        req_params = [key, value[0], docrule_id, str_date_to_couch(document_keys["date"])]
                    else:
                        req_params = [key, value[0], docrule_id]
                else:
                    if dd_range:
                        req_params = [key, value[1], docrule_id, str_date_to_couch(document_keys["end_date"])]
                    else:
                        req_params = [key, value[1], docrule_id]
    return req_params

def document_date_range_present_in_keys(keys):
    """
    Helper to recognise document date range in search keys
    """
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

def str_date_to_couch(from_date):
    """
    Converts date from form date widget generated format, like '2012-03-02'
    To CouchDocument stored date. E.g.: '2012-03-02T00:00:00Z'
    """
    couch_date = from_date + 'T00:00:00Z'
    return couch_date

