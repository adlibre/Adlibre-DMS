"""
Module: DMS Parallell Keys manager
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

from django.conf import settings
from mdtcouch.models import MetaDataTemplate
from mdt_manager import MetaDataTemplateManager

class ParallelKeysManager(object):

    def __init__(self):
        self.mdts = {}
        self.docrule_id = None
        self.keys = {}

    def get_keys_for_docrule(self, docrule_id):
        mdts, pkeys = {}, {}
        mdt_manager = MetaDataTemplateManager()
        mdt_manager.docrule_id = docrule_id
        # valid Mdt id...
        if mdt_manager.mdt_read_call_valid(docrule_id):
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

    def get_parallel_keys_for_key(self, pkeys_list, key):
        """
        Retrieves parallel keys for given key
        """
        for pkeys in pkeys_list:
            for db_field in pkeys:
                if db_field[u'field_name'] == unicode(key):
                    return pkeys
        return None
