"""
Module: DMS Metadata Template Manager
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
"""

from mdtcouch.mdts_manager import MetaDataTemplate
import json

class MetaDataTemplateManager(object):
    """
    Main DMS manager for operating with Metadata Templates.

    Uses only couchDB storage implemntationfor now.
    """
    def __init__(self):
        self.mdt = {}
        self.docrule_id = None

    def get_mdts_for_docrule(self):
        if not self.docrule_id:
            return None
        mdts = MetaDataTemplate.get(docid=self.docrule_id)
        mdts_dict = json.dumps(mdts._doc)
        return mdts_dict

    def store(self, mdt_data):
        if not self.validate_mdt(mdt_data):
            return {"status": "Wrong MDT received. Document did not validate."}
        mdt = MetaDataTemplate()
        try:
            mdt.populate_from_DMS(mdt_data)
            mdt.save()
            return {"status": "ok"}
        except:
            return {"status": "Error storing MDT into DB"}

    def validate_mdt(self, mdt):
        # todo: MDT validation sequence here
        return True

