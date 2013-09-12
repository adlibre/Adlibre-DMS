"""
Module: DMS Core Search logic and base objects.

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
"""

import logging
import datetime

from operator import itemgetter

from django.conf import settings

from errors import DmsException
from dmscouch.models import CouchDocument
from adlibre.date_converter import str_date_to_couch

log = logging.getLogger('dms.core.search')

MUI_SEARCH_PAGINATE = getattr(settings, 'MUI_SEARCH_PAGINATE', 20)

SEARCH_ERROR_MESSAGES = {
    'wrong_date': 'Date range you have provided is wrong. FROM date should not be after TO date.',
    'wrong_indexing_date': 'Creation Date range wrong. FROM date should not be after TO date.',
}

class DMSSearchQuery(object):
    """
    Defined data to be queried from DMS Search Manager class

    it axepts those paramethers:

    @param docrules: must be an iterable of docrule.pk numbers that range search query.
        to search in several ids you must have e.g.:

        'docrules' == ['1', '2', '3', ...]

    @param document_keys: must be a dictionary of secondary keys + optional fixed keys.
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

    @param sorting_key: Can be either "mdt_indexes" key name, e.g. "Employee"
                    or one of "metadata_created_date", "metadata_description", "metadata_doc_type_rule_id"
    @param sorting_order: Must be string == "ascending" or "descending", indicates results order.
    more detailed about those methods can be looked in search_results_sorted method of DMSSearchManager
    """
    def __init__(self, *args):
        """Dynamicaly initialising set of properties"""
        kwargs_possible_params = [
            'document_keys',
            'docrules',
            'only_names',
            'sorting_key',
            'sorting_order'
        ]
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

    def get_sorting_key(self):
        return self.sorting_key

    def set_sorting_key(self, sorting_key):
        self.sorting_key = sorting_key

    def get_sorting_order(self):
        return self.sorting_order

    def set_sorting_order(self, sorting_order):
        self.sorting_order = sorting_order

class DMSSearchResponse(object):
    """Defines data to be ruturned by DMS Search Manager class"""
    def __init__(self, *args):
        """Dynamicaly initialising set of properties"""
        kwargs_possible_params = ['documents', 'document_names', 'errors']
        for param in kwargs_possible_params:
            if param in args[0]:
                self.add_property(param, args[0][param])
            else:
                self.add_property(param, None)

    def add_property(self, name, value):
        self.__dict__[name] = value

    def get_documents(self):
        return self.__dict__['documents']

    def get_document_names(self):
        return self.__dict__['document_names']

    def set_documents(self, documents):
        self.documents = documents

    def get_errors(self):
        return self.__dict__['errors']

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
        document_names = []
        try:
            keys_set = dms_search_query.get_document_keys()
            docrule_ids = dms_search_query.get_docrules()
            sorting_key = dms_search_query.get_sorting_key()
            sorting_order = dms_search_query.get_sorting_order()
        except Exception, e:
            error_message = 'DMS Search error, Insufficient search query data: %s' % e
            log.error(error_message)
            raise DmsException(error_message, 400)
        cleaned_document_keys, errors = self.validate_search_dates(keys_set)
        if errors:
            return DMSSearchResponse({'document_names': [], 'errors':errors})
        if cleaned_document_keys:
            keys = [key for key in cleaned_document_keys.iterkeys()]
            dd_range_keys = self.document_date_range_present_in_keys(keys)
            keys_cnt = cleaned_document_keys.__len__()
            # Selecting appropriate search method
            if dd_range_keys and keys_cnt == 2:
                document_names = self.document_date_range_only_search(cleaned_document_keys, docrule_ids)
            else:
                document_names = self.document_date_range_with_keys_search(cleaned_document_keys, docrule_ids)
        # Search request finished if we need only names
        if dms_search_query.only_names:
            if sorting_key:
                reverse = False
                if sorting_order == "ascending":
                    reverse = True
                document_names = self.search_results_sorted(sorting_key, document_names, reverse=reverse)
            return DMSSearchResponse({'document_names': document_names})
        # TODO: test if we use this part, and delete if not (maybe leave for other method calls, e.g. future api)
        # Actually retrieving documents
        documents = self.get_found_documents(document_names)
        # Not passing CouchDB search results object to template system to avoid bugs, in case it contains no documents
        if not documents:
            documents = []
        # Default Sorting using date (In future we might use variable sort method here)
        if documents:
            documents = self.search_results_by_date(documents)
        return DMSSearchResponse({'documents':documents})

    ########################################## Internal Methods ###############################
    def validate_search_dates(self, query_keys_dict):
        """Method to validate search query logic. E.g. date ranges."""
        errors = []
        # Validating Indexing date.
        if 'date' in query_keys_dict:
            range_ok = self.validation_compare_dates_in_range(query_keys_dict['date'], query_keys_dict['end_date'])
            if not range_ok:
                errors.append(SEARCH_ERROR_MESSAGES['wrong_indexing_date'])
        # Validating keys type of date.
        for key, value in query_keys_dict.iteritems():
            if value.__class__.__name__ == 'tuple':
                range_ok = self.validation_compare_dates_in_range(value[0], value[1])
                if not range_ok:
                    errors.append(key + ' ' + SEARCH_ERROR_MESSAGES['wrong_date'])
        return query_keys_dict, errors

    def validation_compare_dates_in_range(self, date1, date2):
        """Validates if date1 < date2, using DMS settings date format"""
        try:
            end_date = datetime.datetime.strptime(date2, settings.DATE_FORMAT)
            date = datetime.datetime.strptime(date1, settings.DATE_FORMAT)
            delta = end_date - date
            if delta > datetime.timedelta(0):
                return True
        except Exception, e:
            # Not datetime or improper datetime values given. Rising no exception.
            log.error('Search validation exception: %s' % e)
            pass
        return False

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
        for view_set in resp_set[docrule_id]:
            docs_ids_mentions = []
            for doc in view_set:
                docname = doc.get_id
                # Filtering documents with those keys
                if doc['metadata_doc_type_rule_id'] == docrule_id:
                    docs_ids_mentions.append(docname)
                all_docs[docname] = 0
            set_list.append(docs_ids_mentions)
        # Counting docs mentioned in all sets
        for doc in all_docs:
            for set_view in set_list:
                if doc in set_view:
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
        dd_range = self.document_date_range_present_in_keys(document_keys)
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
                            end_date = self.alter_end_date(document_keys["end_date"])
                            req_params = [key, value, docrule_id, str_date_to_couch(end_date)]
                else:
                    # Assuming date range is our date tuple
                    # Creating DB request for document dates (or without document dates) range
                    # Adding 1 day to date range finish to complu CouchDB search conditions and include finish date results.
                    if not end:
                        if dd_range:
                            req_params = [key, str_date_to_couch(value[0]), docrule_id, str_date_to_couch(document_keys["date"])]
                        else:
                            req_params = [key, str_date_to_couch(value[0]), docrule_id]
                    else:
                        end_key_date = self.alter_end_date(value[1])
                        if dd_range:
                            end_date = self.alter_end_date(document_keys["end_date"])
                            req_params = [key, str_date_to_couch(end_key_date), docrule_id, str_date_to_couch(end_date)]
                        else:
                            req_params = [key, str_date_to_couch(end_key_date), docrule_id]
        return req_params

    def alter_end_date(self, date_str):
        """Method to override default Couchdb search capabilities about dates, not to include last range result"""
        date = datetime.datetime.strptime(date_str, settings.DATE_FORMAT)
        timedelta = datetime.timedelta(days=1)
        new_date = date + timedelta
        new_str_date = datetime.datetime.strftime(new_date, settings.DATE_FORMAT)
        return new_str_date

    ################################# Search Sorting Methods ##################################
    def search_results_by_date(self, documents):
        """Sorts search results into list by CouchDB document's 'created date'."""
        newlist = sorted(documents, key=itemgetter('metadata_created_date'))
        return newlist

    def search_results_sorted(self, key, document_list, reverse=False):
        """
        Sorting method of DMS search.

        Sorts documents making query of required data by itself from CouchDB.
        Appends documents that have no key to the end of the list in uncontrolled order.
        e.g. order they appear in iteration.

        @param key: Can be either "mdt_indexes" key name, e.g. "Employee"
                    or one of "metadata_created_date", "metadata_description", "metadata_doc_type_rule_id"
        @param document_list: List of document names to sort. e.g.: ['ADL-0001', 'CCC-0001', ... ]
        @param reverse: Direction of sorting (True/False)

        @return: Sorted list of document names using given @param key e.g.: ['CCC-0001', 'ADL-0001', ... ]
        """
        if document_list:
            values_list = []
            empty_values_list = []
            documents = self.get_sorting_docs_indexes(document_list)
            # Selecting proper sorting couch query params
            if key in ["metadata_created_date", "metadata_description", "metadata_doc_type_rule_id"]:
                doc_field = key
            else:
                doc_field = 'mdt_indexes'
            # Creating special, sorting capable list of tuples (Docname, Sorting field value)
            for doc in documents:
                if doc_field == 'mdt_indexes':
                    if key in doc[doc_field]:
                        value = doc[doc_field][key]
                    else:
                        value = ''
                else:
                    value = doc[key]
                if value:
                    values_list.append((doc.get_id, value))
                else:
                    empty_values_list.append(doc.get_id)
            try:
                document_list = sorted(values_list, key=itemgetter(1), reverse=reverse)
                document_list = map(lambda doc: doc[0],  document_list)
                document_list = document_list + empty_values_list
            except TypeError, e:
                log.error('sorting TypeError error in indexes: %s, in documents_list: %s' % (e, document_list))
                pass
        return document_list

    def get_sorting_docs_indexes(self, document_list):
        """
        Retrieves main document indexes from CouchDB view.

        @param document_list: list of document names, e.g. ['ADL-0001', 'CCC-0001', ... ]
        @return: CouchDB documents "view results" Object.
                 each document contains:
                     "mdt_indexes"
                     "metadata_created_date"
                     "metadata_description"
                     "metadata_doc_type_rule_id"
        """
        documents = CouchDocument.view('dmscouch/search_main_indexes', keys=document_list)
        return documents

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
        log.debug(
            'Search results by date range with additional keys: "%s", docrule: "%s", documents: "%s"' %
            (cleaned_document_keys, docrule_ids, map(lambda doc: doc, retrieve_docs))
        )
        return retrieve_docs

    def document_date_range_only_search(self, cleaned_document_keys, docrule_ids):
        log.debug('Date range search only')
        resp_list = []
        startkey = [None,]
        endkey = [None,]
        for docrule_id in docrule_ids:
            startkey = [docrule_id, str_date_to_couch(cleaned_document_keys["date"])]
            endkey = [docrule_id, str_date_to_couch(cleaned_document_keys["end_date"])]
            # Getting all documents withing this date range
            all_docs = CouchDocument.view('dmscouch/search_date', startkey=startkey, endkey=endkey)
            # Appending to fetch docs list if not already there
            for doc in all_docs:
                doc_name = doc.get_id
                if not doc_name in resp_list:
                    resp_list.append(doc_name)
        if resp_list:
            log_data = resp_list.__len__()
        else:
            log_data = None
        log.debug(
            'Search results by date range: from: "%s", to: "%s", docrules: "%s", documents: "%s"' %
            (startkey[0], endkey[0], docrule_ids, log_data)
        )
        return resp_list

    def get_found_documents(self, document_names_list):
        """
        Method to retrieve documents index data by document names list.

        @param document_names_list: list of document id's, e.g. ['DOC0001', 'MAS0001', '...' ]
        @return: CouchDB documents list.
        """
        documents = CouchDocument.view('dmscouch/all', keys=document_names_list, include_docs=True)
        return documents
