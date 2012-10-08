"""
Module: DMS Core Search logic and base objects.

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
"""

import logging

from operator import itemgetter

from errors import DmsException
from dmscouch.models import CouchDocument
from adlibre.date_converter import str_date_to_couch

log = logging.getLogger('dms.core.search')

class DMSSearchQuery(object):
    """
    Defined data to be queried from DMS Search Manager class

    it axepts those paramethers:

    - docrule_ids must be an iterable of docrule.pk numbers that range search query.
        to search in several ids you must have e.g.:

        'docrule_ids' == ['1', '2', '3', ...]

    - document_keys must be a dictionary of secondary keys + optional fixed keys.
        e.g. to search with document's creation date and some keys document_keys must be like:

        'document_keys' == {
            u'date': u'02/10/2012',
            u'end_date': u'01/01/2100',
            u'Reporting Entity': u'JTG'
            u'Report Date': (u'08/10/2012', u'16/10/2012')
        }

    This example will result to 1 search query for documents with key JTG and 1 query for range of dates called
    'Report Date' with using of 'Creation Date' Specified.
    Each additional key will add 1 more search query.
    Search results will be a mixed set of those documents matching query.
    """
    def __init__(self, *args):
        """Dynamicaly initialising set of properties"""
        kwargs_possible_params = ['document_keys', 'docrules']
        for param in kwargs_possible_params:
            if param in args[0]:
                self.add_property(param, args[0][param])
            else:
                self.add_property(param, {})

    def add_property(self, name, value):
         self.__dict__[name] = value

    def get_document_keys(self):
        return self.document_keys

    def set_document_keys(self, keys):
        self.document_keys = keys

    def get_docrules(self):
        return self.docrules

    def set_docrules(self, rule_ids_list):
        self.docrules = rule_ids_list

class DMSSearchResponse(object):
    """Defines data to be ruturned by DMS Search Manager class"""
    def __init__(self, documents=None):
        self.documents = documents

    def get_documents(self):
        return self.documents

    def set_documents(self, documents):
        self.documents = documents

class DMSSearchManager(object):
    """
    Manager to handle DMS Search Logic
    """
    ############################## External interaction Methods ###############################
    def search_dms(self, dms_search_query):
        """
        Main DMS search method.

        Works with DMSSearchQuery and DMSSearchResponse
        """
        documents = []
        try:
            cleaned_document_keys = dms_search_query.get_document_keys()
            docrule_ids = dms_search_query.get_docrules()
        except Exception, e:
            error_message = 'DMS Search error, Insufficient search query data: %s' % e
            log.error(error_message)
            raise DmsException(error_message, 400)
        if cleaned_document_keys:
            keys = [key for key in cleaned_document_keys.iterkeys()]
            dd_range_keys = self.document_date_range_present_in_keys(keys)
            keys_cnt = cleaned_document_keys.__len__()
            # Selecting appropriate search method
            if dd_range_keys and keys_cnt == 2:
                documents = self.document_date_range_only_search(cleaned_document_keys, docrule_ids)
            else:
                documents = self.document_date_range_with_keys_search(cleaned_document_keys, docrule_ids)
        # Not passing CouchDB search results object to template system to avoid bugs, in case it contains no documents
        if not documents:
            documents = []
        # Default Sorting using date (In future we might use variable sort method here)
        if documents:
            documents = self.search_results_by_date(documents)
        return DMSSearchResponse(documents)

    ########################################## Internal Methods ###############################
    def document_date_range_present_in_keys(self, keys):
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

    def convert_search_res_for_range(self, resp_set, cleaned_document_keys, docrule_id):
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

    def convert_to_search_keys_for_date_range(self, document_keys, pkey, docrule_id, end=False, date_range=False):
        """
        Makes proper keys request set for 'dmscouch/search' CouchDB view.

        Takes date range into account.
        """
        req_params = []
        manager = DMSSearchManager()
        dd_range = manager.document_date_range_present_in_keys(document_keys)
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

    def search_results_by_date(self, documents):
        """Sorts search results into list by CouchDB document's 'created date'."""
        newlist = sorted(documents, key=itemgetter('metadata_created_date'))
        return newlist

    ##################################### Search Methods ######################################
    def document_date_range_with_keys_search(self, cleaned_document_keys, docrule_ids):
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
                        startkey = self.convert_to_search_keys_for_date_range(cleaned_document_keys, key, docrule_id)
                        endkey = self.convert_to_search_keys_for_date_range(cleaned_document_keys, key, docrule_id, end=True)
                    else:
                        # Got date range key
                        startkey = self.convert_to_search_keys_for_date_range(cleaned_document_keys, key, docrule_id, date_range=True)
                        endkey = self.convert_to_search_keys_for_date_range(cleaned_document_keys, key, docrule_id, end=True, date_range=True)
                    if startkey and endkey:
                        # Appending results list to mixed set of results.
                        search_res = CouchDocument.view('dmscouch/search', startkey=startkey, endkey=endkey)
                        if docrule_id in resp_set.iterkeys():
                            resp_set[docrule_id].append(search_res)
                        else:
                            resp_set[docrule_id] = [search_res]
                            # Extracting documents for each CouchDB response set.
            docs_list[docrule_id] = self.convert_search_res_for_range(resp_set, cleaned_document_keys, docrule_id)
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

    def document_date_range_only_search(self, cleaned_document_keys, docrule_ids):
        log.debug('Date range search only')
        resp_list = []
        startkey = [None,]
        endkey = [None,]
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