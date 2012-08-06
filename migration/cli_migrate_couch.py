#! /usr/bin/python2.6

import httplib, json

from lib_couch import prettyPrint, Couch


def incrementRuleID():
    """
    This will increment the doc_type_rule_id by 1.
    Used for JTG migration 20120613
    """
    db = Couch('localhost', '5984')
    dbName = 'dmscouch'

    print "\nList all documents in database %s updated" % dbName
    docs_js = db.listDoc(dbName)

    docs_decoded = json.loads(docs_js)

    for doc in docs_decoded['rows']:
        bar_code = doc['id']

        d_js = db.openDoc(dbName, bar_code)
        d = json.loads(d_js)

        d['metadata_doc_type_rule_id'] = str(int(d['metadata_doc_type_rule_id']) + 1)
        d_enc = json.dumps(d)
        #print d['metadata_doc_type_rule_id']
        print db.saveDoc(dbName, d_enc, docId=bar_code)

if __name__ == "__main__":
    incrementRuleID()
