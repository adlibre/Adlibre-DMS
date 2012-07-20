#! /usr/bin/python2.6

# originally from http://wiki.apache.org/couchdb/Getting_started_with_Python

# Modified heavily to support custom couchdb migration for Adlibre DMS

# This is used when we need to do some hacky migrations or raw manipulations to the couchdb schema

import httplib, json, sys

def prettyPrint(s):
    """Prettyprints the json response of an HTTPResponse object"""

    # HTTPResponse instance -> Python object -> str
    return json.dumps(json.loads(s.read()), sort_keys=True, indent=4)

class Couch:
    """Basic wrapper class for operations on a couchDB"""

    def __init__(self, host, port=5984, options=None):
        self.host = host
        self.port = port

    def connect(self):
        return httplib.HTTPConnection(self.host, self.port) # No close()

    # Database operations

    def createDb(self, dbName):
        """Creates a new database on the server"""

        r = self.put(''.join(['/',dbName,'/']), "")
        prettyPrint(r)

    def deleteDb(self, dbName):
        """Deletes the database on the server"""

        r = self.delete(''.join(['/',dbName,'/']))
        prettyPrint(r)

    def listDb(self):
        """List the databases on the server"""

        prettyPrint(self.get('/_all_dbs'))

    def infoDb(self, dbName):
        """Returns info about the couchDB"""
        r = self.get(''.join(['/', dbName, '/']))
        prettyPrint(r)

    # Document operations

    def listDoc(self, dbName):
        """List all documents in a given database"""

        r = self.get(''.join(['/', dbName, '/_design/', dbName, '/_view/all']))
        return prettyPrint(r)

    def openDoc(self, dbName, docId):
        """Open a document in a given database"""
        r = self.get(''.join(['/', dbName, '/', docId,]))
        return prettyPrint(r)

    def saveDoc(self, dbName, body, docId=None):
        """Save/create a document to/in a given database"""
        if docId:
            r = self.put(''.join(['/', dbName, '/', docId]), body)
        else:
            r = self.post(''.join(['/', dbName, '/']), body)
        return prettyPrint(r)

    def deleteDoc(self, dbName, docId):
        # XXX Crashed if resource is non-existent; not so for DELETE on db. Bug?
        # XXX Does not work any more, on has to specify an revid
        #     Either do html head to get the recten revid or provide it as parameter
        r = self.delete(''.join(['/', dbName, '/', docId, '?revid=', rev_id]))
        prettyPrint(r)

    # Basic http methods

    def get(self, uri):
        c = self.connect()
        headers = {"Accept": "application/json"}
        c.request("GET", uri, None, headers)
        return c.getresponse()

    def post(self, uri, body):
        c = self.connect()
        headers = {"Content-type": "application/json"}
        c.request('POST', uri, body, headers)
        return c.getresponse()

    def put(self, uri, body):
        c = self.connect()
        if len(body) > 0:
            headers = {"Content-type": "application/json"}
            c.request("PUT", uri, body, headers)
        else:
            c.request("PUT", uri, body)
        return c.getresponse()

    def delete(self, uri):
        c = self.connect()
        c.request("DELETE", uri)
        return c.getresponse()


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
