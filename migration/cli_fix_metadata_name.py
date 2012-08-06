#! /usr/bin/python2.6

import httplib, json, sys

from lib_couch import prettyPrint, Couch


def fixName(id, name):
    """
    This will perform a global name change for an employee id
    Used by JTG
    """
    db = Couch('localhost', '5984')
    dbName = 'dmscouch'

    docs_js = db.listDoc(dbName)

    docs_decoded = json.loads(docs_js)

    for doc in docs_decoded['rows']:
        bar_code = doc['id']

        d_js = db.openDoc(dbName, bar_code)
        d = json.loads(d_js)
        mdt_indexes = d['mdt_indexes']

        try:
            employee_id = int(mdt_indexes['Employee ID'])
        except KeyError:
            employee_id = None

        if employee_id == int(id):
            mdt_indexes['Employee Name'] = name

            # save
            d['mdt_indexes'] = mdt_indexes
            d_enc = json.dumps(d)
            print db.saveDoc(dbName, d_enc, docId=bar_code)

if __name__ == "__main__":
    fixName(sys.argv[1], sys.argv[2])
