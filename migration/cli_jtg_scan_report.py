#! /usr/bin/python2.6

"""
A simple report to show all the documents in our DMS
- Number of revisions
- MD5 sum of the latest revision (find duplicates / holding images)
"""

import json, sys, urllib2
import hashlib
import datetime

from lib_couch import prettyPrint, Couch

# DMS API parameters
host = 'https://jtg.dms.adlibre.net/'
api_url = 'api/file/'
username = 'admin'
password = 'admin'
user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT) DMS Client'

def get_api_file(filename, parsable, revision=None):
    """
    Retrieves file from DMS API, using DMS simple auth.
    requires (variables and their example value):

        host = 'http://127.0.0.1:8000/'
        api_url = 'api/file/'
        username = 'admin'
        password = 'admin'
        user_agent = 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT) DMS Client'
    """
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, host, username, password)
    handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener = urllib2.build_opener(handler)
    urllib2.install_opener(opener)

    if revision:
        request = urllib2.Request(host+api_url+filename+'?revision='+revision)
    else:
        request = urllib2.Request(host+api_url+filename)
    request.add_header('User-agent', user_agent)
    response = None
    try:
        response = opener.open(request)
    except urllib2.HTTPError, e:
        if not parsable:
            print e
        pass
    return response.read()

def show_doc_report(parsable=False):
    """
    This is a custom report to facilitate scanning / indexing reconciliation for JTG
    """
    db = Couch('localhost', '5984')
    dbName = 'dmscouch'

    if not parsable:
        print "Special report of all document's in database '%s'. Excepts arguments ;) (-p or --parsable)" % dbName
    docs_js = db.listDoc(dbName)

    docs_decoded = json.loads(docs_js)

    for doc in docs_decoded['rows']:
        bar_code = doc['id']

        # Load document
        d_js = db.openDoc(dbName, bar_code)
        d = json.loads(d_js)
        revisions = d['revisions']
        mdt_indexes = d['mdt_indexes']
        metadata_created_date = str(d['metadata_created_date'])

        # Get employee Name (JTG Specific index)
        try:
            employee = str(mdt_indexes['Employee Name'])
        except KeyError:
            employee = ""

        # Get revisions
        if revisions:
            revision_names = [rev_name for rev_name in revisions.iterkeys()]
            revision_names.sort()
        else:
            revision_names = []

        latest_revision = ''
        if revision_names:
            latest_revision = revision_names[revision_names.__len__() - 1]

	if revisions is not None:
	    revisions_count = revisions.__len__()
	else:
	    revisions_count = 0

        # Get MD5 sum of the latest document revision
        h_code=''
        if latest_revision:
            api_file = get_api_file(bar_code, parsable, latest_revision)

            h = hashlib.new('md5')
            h.update(api_file)
            h_code = h.hexdigest()

        # Format the output
        if parsable:
            print '"%s", "%s", "%s", "%s", "%s"' % (bar_code, revisions_count, employee, h_code, metadata_created_date)
        else:
            print '%s, revision count: %s, names: %s, employee: %s, hashcode: %s, date: %s' % (bar_code, revisions_count, str(revision_names), employee, h_code, metadata_created_date)

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
    t1 = datetime.datetime.now()
    show_doc_report(parsable)
    t2 = datetime.datetime.now()
    if not parsable:
        print 'Execution time: %s' % (t2-t1)
