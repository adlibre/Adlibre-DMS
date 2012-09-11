#! /usr/bin/python2.6

"""
Fixing BUG #829 Script.
Should cleanup keys:
- metadata_user_name
- metadata_user_id
from all the DMS documents "mdt_indexes" dictionary.
"""

import json, sys, urllib2
import datetime

from lib_couch import  Couch

# DMS API parameters
host = 'http://127.0.0.1:8000/'
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
        mdt_u_id = 'N'
        mdt_u_name = 'N'

        # Load document
        d_js = db.openDoc(dbName, bar_code)
        d = json.loads(d_js)
        mdt_indexes = d['mdt_indexes']
        d_keys = [key for key in mdt_indexes.iterkeys()]
        if ('metadata_user_id' in d_keys) or ('metadata_user_name' in d_keys):
            try:
                del d['mdt_indexes']['metadata_user_id']
                mdt_u_id = 'Y'
            except: pass
            try:
                del d['mdt_indexes']['metadata_user_name']
                mdt_u_name = 'Y'
            except: pass
            if parsable:
                print '%s, %s, %s' % (bar_code, mdt_u_id, mdt_u_name)
            else:
                print "document: %s, metadata_user_id: %s, metadata_user_name: %s" % (bar_code, mdt_u_id, mdt_u_name)
            if mdt_u_name=="Y" or mdt_u_id=="Y":
                d_enc = json.dumps(d)
                db.saveDoc(dbName, d_enc, docId=bar_code)

if __name__ == "__main__":
    """
    To run this you can do:
    >> python script_name.py
    output will be:
    document:ADL-0001, metadata_user_id: Y, metadata_user_name: N

    or to generate parsable output do:
    python script_name.py --parsable
    or
    python script_name.py --p
    output in this case:
    ADL-0001, Y, N
    """
    parsable = False
    if sys.argv.__len__() > 1:
        if '-p' or '--parsable' in sys.argv:
            parsable = True
    t1 = datetime.datetime.now()
    show_doc_report(parsable)
    t2 = datetime.datetime.now()
    print 'Execution time: %s' % (t2-t1)
