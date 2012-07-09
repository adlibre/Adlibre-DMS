#! /usr/bin/python2.6

# Hack to correct couch data damaged by Bug 784. Copy correct values from an alternate couchdb schema

import httplib, json

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


def fix784():
    """
    This will copy the created_data and user_name from a source database schema
    Used for JTG to fix bug #784 20120709
    """
    db_target = Couch('localhost', '5985') # Production / Target
    db_source = Couch('localhost', '5986') # Stage / Source
    dbName = 'dmscouch'

    # for bar_code in bar_codes in the file
    f = open('cli_fix_metadata_784.txt', 'rU')
    for line in f.readlines():

        bar_code = str(line[:-1])

        print "Updating bar_code: %s" % bar_code

        d_s_js = db_source.openDoc(dbName, bar_code)
        d_s = json.loads(d_s_js)

        d_t_js = db_target.openDoc(dbName, bar_code)
        d_t = json.loads(d_t_js)

        # set target values from source
        d_t['metadata_created_date'] = d_s['metadata_created_date']
        d_t['metadata_user_name'] = d_s['metadata_user_name']

        d_t_enc = json.dumps(d_t)
        print db_target.saveDoc(dbName, d_t_enc, docId=bar_code)

if __name__ == "__main__":
    fix784()
