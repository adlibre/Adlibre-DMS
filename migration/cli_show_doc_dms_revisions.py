#! /usr/bin/python2.6

"""
A simple report to show all the documents in our DMS
- Number of revisions
"""

import json, sys

from lib_couch import prettyPrint, Couch


def show_doc_revisions(extended):
    db = Couch('localhost', '5984')
    dbName = 'dmscouch'

    print "Report of all document's in database '%s' revisions count. Excepts arguments ;) (-s or --short)" % dbName
    docs_js = db.listDoc(dbName)

    docs_decoded = json.loads(docs_js)

    for doc in docs_decoded['rows']:
        bar_code = doc['id']

        d_js = db.openDoc(dbName, bar_code)
        d = json.loads(d_js)
        revisions = d['revisions']
        if revisions:
            revision_names = [rev_name for rev_name in revisions.iterkeys()]
        else:
            revision_names = []
        if extended:
            print bar_code + ' revisions count: ' + str(revisions.__len__()) + ' names: ' + str(revision_names)
        else:
            print bar_code + ' ' + str(revisions.__len__())

if __name__ == "__main__":
    """
    To run this you can do:
    >> python script_name.py
    output will be:
    ADL-0001 revisions count: 2 names: [u'1', u'2']

    or to see short do:
    python script_name.py --short
    or
    python script_name.py --s
    ADL-0001 1
    """
    extended = True
    if sys.argv.__len__() > 1:
        if '-s' or '--short' in sys.argv:
            extended = False
    show_doc_revisions(extended)
