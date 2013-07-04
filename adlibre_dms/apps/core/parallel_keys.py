"""
Module: DMS Parallel Keys manager
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
Author: Iurii Garmash
"""

import logging
import json
log = logging.getLogger('core.parallel_keys')

from mdt_manager import MetaDataTemplateManager
from dmscouch.models import CouchDocument


class ParallelKeysManager(object):
    """Helper to work with parallel keys"""
    #
    # def __init__(self):
    #     self.mdts = {}
    #     self.docrule_id = None
    #     self.keys = {}

    def get_keys_for_docrule(self, docrule_id, mdts = None):
        pkeys = {}
        mdt_manager = MetaDataTemplateManager()
        mdt_manager.docrule_id = docrule_id
        # valid Mdt id...
        if mdt_manager.mdt_read_call_valid():
            if not mdts:
                mdts = mdt_manager.get_mdts_for_docrule(docrule_id)
            pkeys = self.get_parallel_keys_for_mdts(mdts)
        return pkeys

    def get_parallel_keys_for_mdts(self, mdts_list):
        """
        Extracts Parallel keys from mdts list for use in autocomplete call.
        """
        pkeys = []
        temp_list = []
        if mdts_list:
            for mdt in mdts_list.itervalues():
                if mdt["parallel_keys"]:
                    for key, value in mdt["parallel_keys"].iteritems():
                        for pkey in value:
                            temp_list.append(mdt["fields"][pkey])
                        pkeys.append(temp_list)
                        temp_list = []
        return pkeys

    def get_parallel_keys_for_key(self, pkeys_list, key_name):
        """
        Retrieves parallel keys for given key
        """
        for pkeys in pkeys_list:
            for db_field in pkeys:
                if db_field[u'field_name'] == unicode(key_name):
                    return pkeys
        return None

    def get_parallel_keys_for_pkeys(self, pkeys, secondary_keys):
        """
        Extracts only parallel keys/values pairs for parallel keys in keys/values list provided.

        returns list of tuples of parallel keys. E.g.:
        [('name': 'mike'), ('surname': 'kernel')]
        """
        pkeys_list = []
        if pkeys:
            for pkey in pkeys:
                pkeys_list.append((pkey[u'field_name'], secondary_keys[pkey[u'field_name']]))
        return pkeys_list


def process_pkeys_request(docrule_id, key_name, autocomplete_req, doc_mdts, letters_limit=2, suggestions_limit=8):
    """
    Helper method to process MDT's for special user.

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
    # TODO: Can be optimised for huge document's amounts in future (Step: Scalability testing)
    resp = []
    view_name = 'dmscouch/search_autocomplete'
    manager = ParallelKeysManager()
    for mdt in doc_mdts.itervalues():
        mdt_keys = [mdt[u'fields'][mdt_key][u'field_name'] for mdt_key in mdt[u'fields']]
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
                            view_name,
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
                        view_name,
                        startkey=[docrule, key_name, autocomplete_req],
                        endkey=[docrule, key_name, unicode(autocomplete_req)+u'\ufff0'],
                        group=True,
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
    return resp