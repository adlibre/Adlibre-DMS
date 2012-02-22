"""
Module: DMS Metadata Template Manager
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
"""

from django.conf import settings
from mdtcouch.models import MetaDataTemplate

class MetaDataTemplateManager(object):
    """
    Main DMS manager for operating with Metadata Templates.

    Uses only couchDB storage implemntationfor now.
    """
    def __init__(self):
        self.mdt = {}
        self.docrule_id = None
        self.delete = False

    def get_mdts_for_docrule(self, docrule_id):
        """
        Method to construct response with MDT's for docrule provided.
        Manager must have docrule assigned ( MetaDataTemplateManager.docrule_id = 1 )
        in order for manager to work properly.

        returns dict of MDT's for docrule_id provided/or error message.
        """
        mdts_list = {}
        # validating
        if self.mdt_read_call_valid(docrule_id):
            try:

                # getting MDT's from DB
                mdts_view = MetaDataTemplate.view('mdtcouch/docrule', key=docrule_id)
                # constructing MDT's response dict
                id = 1
                for row in mdts_view:
                    mdts_list[str(id)] = row._doc
                    # cleaning up _id and _rev from response to unify response
                    mdts_list[str(id)]["mdt_id"] = mdts_list[str(id)]['_id']
                    del mdts_list[str(id)]['_id']
                    del mdts_list[str(id)]['_rev']
                    id+=1
            except:
                pass
        # something not valid response:
        if not mdts_list:
            mdts_list = 'error'
        return mdts_list

    def store(self, mdt_data):
        """
        Method to store MDT into DB. Uses JSON provided.
        Example MDT:
        {
            "docrule_id": "1",
            "description": "description of this metadata template",
            "fields": {
               "1": {
                   "type": "integer",
                   "field_name": "Employee ID",
                   "description": "Unique (Staff) ID of the person associated with the document"
               },
               "2": {
                   "type": "string",
                   "length": 60,
                   "field_name": "Employee Name",
                   "description": "Name of the person associated with the document"
               },
            },
            "parallel": {
               "1": [ "1", "2"],
            }
        }

        """
        mdt = MetaDataTemplate()
        if self.validate_mdt(mdt_data):
            try:
                mdt.populate_from_DMS(mdt_data)
                mdt.save()
                return {"status": "ok", "mdt_id": "%s" %mdt._doc._id}
            except Exception, e:
                if settings.DEBUG:
                    print "Exception: ", e
                    raise
                else:
                    pass
        else:
            return 'error'


    def delete_mdt(self, mdt):
        #print 'Deleting mdt: %s' %mdt
        try:
            mdt = MetaDataTemplate.get(docid=mdt)
            mdt.delete()
        except:
            return "error"
        return 'done'

    def validate_mdt(self, mdt):
        # todo: MDT validation sequence here
        return True

    def mdt_read_call_valid(self, docrule_id):
        """
        Simple type validation of docrule_id provided.
        """
        if not self.docrule_id:
            return False
        try:
            int(self.docrule_id)
            str(self.docrule_id)
            return True
        except:
            return False
