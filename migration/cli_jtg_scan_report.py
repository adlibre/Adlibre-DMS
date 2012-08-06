#! /usr/bin/python2.6

import httplib, json, sys

from lib_couch import prettyPrint, Couch


def show_doc_report(parsable=False):
    """
    This is a custom report to facilitate scanning / indexing reconciliation for JTG
    """
    db = Couch('localhost', '5984')
    dbName = 'dmscouch'

    print "Special report of all document's in database '%s'. Excepts arguments ;) (-p or --parsable)" % dbName
    docs_js = db.listDoc(dbName)

    docs_decoded = json.loads(docs_js)

    for doc in docs_decoded['rows']:
        bar_code = doc['id']

        d_js = db.openDoc(dbName, bar_code)
        d = json.loads(d_js)
        revisions = d['revisions']
        mdt_indexes = d['mdt_indexes']

        try:
            employee = str(mdt_indexes['Employee Name'])
        except KeyError:
            employee = ""

        if revisions:
            revision_names = [rev_name for rev_name in revisions.iterkeys()]
        else:
            revision_names = []

        if parsable:
            print '"%s", "%s", "%s"' % (bar_code, revisions.__len__(), employee)
        else:
            print '%s, revision count: %s, names: %s, employee: %s' % (bar_code, revisions.__len__(), str(revision_names), employee)

if __name__ == "__main__":
    """
    To run this you can do:
    >> python script_name.py
    output will be:
    ADL-0001 revision count: 2 names: [u'1', u'2'], employee: JOHN DOE

    or to generate parsable output do:
    python script_name.py --parsable
    or
    python script_name.py --p
    ADL-0001 1
    """
    parsable = False
    if sys.argv.__len__() > 1:
        if '-p' or '--parsable' in sys.argv:
            parsable = True
    show_doc_report(parsable)
