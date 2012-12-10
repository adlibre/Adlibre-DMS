"""
Module: SEARCH TYPE VARIATIONS GENERAL SEARCH HELPERS

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import logging

from forms_representator import SEARCH_STRING_REPR
from forms_representator import get_mdts_for_docrule

from parallel_keys import ParallelKeysManager
from mdt_manager import MetaDataTemplateManager
from dmscouch.models import CouchDocument
from adlibre.date_converter import date_standardized

log = logging.getLogger('dms.mdtui.views')

DATE_RANGE_CONSTANTS = {
    'min': unicode(date_standardized('1960-01-01')),
    'max': unicode(date_standardized('2100-01-01')),
    }

def cleanup_document_keys(document_keys):
    """
    Cleaning up key/value pairs that have empty values from CouchDB search request
    """
    if document_keys:
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
    if cleaned_document_keys:
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
    if cleaned_document_keys:
        keys_list = [key for key in cleaned_document_keys.iterkeys()]
    else:
        keys_list = []
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
                                                key=[docrule_id, pkey, pvalue],
                                                reduce=False)
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

def check_for_forbidden_new_keys_created(document_indexes, docrule, user):
    """Checks for user ability to add new key's value

    @param document_indexes is a set of user entered indexing data of specific document
    @param docrule is current docrule id
    @param user is a current request.user"""
    user_locked_keys = []
    mdts = get_mdts_for_docrule(docrule)
    manager = MetaDataTemplateManager()
    # Parsing MDT's
    admin_restricted_keys, locked_keys = manager.get_restricted_keys_names(mdts)
    # doing nothig for admincreate keys if user is staff or superuser
    if user.is_staff or user.is_superuser:
        admin_restricted_keys = []
        # Checking all keys locked for editing to staff or superuser only
    for key in admin_restricted_keys:
        value = document_indexes[key]
        exists = check_docs_for_existence(key, value, docrule)
        if not exists:
            user_locked_keys.append((key, 'adminlock'))
            # Checking all the keys that are marked locked
    for key in locked_keys:
        value = document_indexes[key]
        exists = check_docs_for_existence(key, value, docrule)
        if not exists:
            user_locked_keys.append((key, 'locked'))
    return user_locked_keys

def check_docs_for_existence(key, value, docrule):
    """Check if at least one document with specified docrule, key and value exist"""
    documents = CouchDocument.view('dmscouch/search_autocomplete', key=[docrule, key, value], reduce=False)
    if documents.__len__() > 0:
        # There is at least one this type document...
        return True
    else:
        # No such documents
        return False