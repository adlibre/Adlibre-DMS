"""
Module: Metadata Template UI Views
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

from dmscouch.models import CouchDocument
import logging

log = logging.getLogger('dms.mdtui.views')

"""
SEARCH TYPE VARIATIONS GENERAL SEARCH HELPERS
"""

def search_by_single_date(cleaned_document_keys, docrule_id):
    log.debug("Single exact date search")
    documents = CouchDocument.view(
                                'dmscouch/search_date',
                                key=[str_date_to_couch(cleaned_document_keys["date"]),
                                    docrule_id],
                                include_docs=True
                                )
    log.debug(
        'Search results by single date without keys: "%s", docrule: "%s", documents: "%s"' %
        (str_date_to_couch(cleaned_document_keys["date"]), docrule_id, map(lambda doc: doc["id"], documents))
    )
    return documents

def exact_date_with_keys_search(cleaned_document_keys, docrule_id):
    log.debug('Multiple keys with exact date search')
    documents = None
    couch_req_params = convert_to_search_keys_for_single_date(cleaned_document_keys, docrule_id)
    if couch_req_params:
        search_res = CouchDocument.view('dmscouch/search', keys=couch_req_params )
        # documents now returns ANY search type results.
        # we need to convert it to ALL
        docs_list = convert_search_res(search_res, couch_req_params.__len__())
        documents = CouchDocument.view('_all_docs', keys=docs_list, include_docs=True )
    log.debug(
        'Search results only by single date with keys set: "%s", docrule: "%s", documents: "%s"' %
        (couch_req_params, docrule_id, map(lambda doc: doc["id"], documents))
    )
    return documents

def date_range_only_search(cleaned_document_keys, docrule_id):
    log.debug('Date range search only')
    documents = None
    startkey = [str_date_to_couch(cleaned_document_keys["date"]), docrule_id]
    endkey = [str_date_to_couch(cleaned_document_keys["end_date"]), docrule_id]
    documents = CouchDocument.view('dmscouch/search_date', startkey=startkey, endkey=endkey, include_docs=True)
    log.debug(
        'Search results by date range: from: "%s", to: "%s", docrule: "%s", documents: "%s"' %
        (startkey[0], endkey[0], docrule_id, map(lambda doc: doc["id"], documents))
    )
    return documents

def date_range_with_keys_search(cleaned_document_keys, docrule_id):
    log.debug('Date range search with additional keys specified')
    resp_set = []
    documents = None
    # Getting list of date range filtered docs for each provided secondary key
    # Except for internal keys
    for key, value in cleaned_document_keys.iteritems():
        if not (key == 'date') and not (key == 'end_date'):
            startkey = convert_to_search_keys_for_date_range(cleaned_document_keys, key, docrule_id)
            endkey = convert_to_search_keys_for_date_range(cleaned_document_keys, key, docrule_id, end=True)
            if startkey and endkey:
                search_res = CouchDocument.view('dmscouch/search', startkey=startkey, endkey=endkey )
                if search_res:
                    resp_set.append(search_res)
    # resp_set now returns ANY search type results.
    # we need to convert it to ALL
    docs_list = convert_search_res_for_range(resp_set)
    documents = CouchDocument.view('_all_docs', keys=docs_list, include_docs=True )
    log.debug(
        'Search results by date range with additional keys: "%s", docrule: "%s", documents: "%s"' %
        (cleaned_document_keys, docrule_id, map(lambda doc: doc["id"], documents))
    )
    return documents

"""
ANOTHER GENERAL SEARCH HELPERS
"""

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

def convert_search_res(search_res, match_len):
    """
    Converts search results for multiple keys with single date request
    from type ANY to type ALL (keys exist in document)
    """
    docs_list = {}
    matched_docs = []
    for row in search_res:
        if row.get_id in docs_list.keys():
            docs_list[row.get_id] += 1
        else:
            docs_list[row.get_id] = 1
    for doc_id, mention_count in docs_list.iteritems():
        if mention_count >= match_len:
            matched_docs.append(doc_id)
    return matched_docs

def convert_search_res_for_range(resp_set):
    """
    Converts search results for multiple keys with date range
    from type ANY to type ALL (keys exist in document)
    """
    docs_ids_mentions = {}
    docs_ids_list = []
    # Each set
    for set in resp_set:
        # Each doc in set
        for doc in set:
            docname = doc.get_id
            if docname in docs_ids_mentions.iterkeys():
                docs_ids_mentions[docname] += 1
            else:
                docs_ids_mentions[docname] = 1
    # Comparing search mentions and adding to response if all keys match
    for key, value in docs_ids_mentions.iteritems():
        if value >= resp_set.__len__():
            docs_ids_list.append(key)
    return docs_ids_list

def convert_to_search_keys_for_single_date(document_keys, docrule_id):
    """
    Makes proper keys request set for 'dmscouch/search' CouchDB view.
    """
    req_params = []
    for key, value in document_keys.iteritems():
        if key != "date":
            if not "date" in document_keys.keys():
                req_params.append([key, value, docrule_id],)
            else:
                req_params.append([key, value, docrule_id, str_date_to_couch(document_keys["date"])],)
    return req_params

def convert_to_search_keys_for_date_range(document_keys, pkey, docrule_id, end=False):
    """
    Makes proper keys request set for 'dmscouch/search' CouchDB view.
    Takes date range into account.
    """
    req_params = []
    for key, value in document_keys.iteritems():
        if key == pkey:
            if not end:
                req_params = [key, value, docrule_id, str_date_to_couch(document_keys["date"])]
            else:
                req_params = [key, value, docrule_id, str_date_to_couch(document_keys["end_date"])]
    return req_params

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