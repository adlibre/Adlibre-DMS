#! /usr/bin/python2.6

# Hack to correct couch data damaged by Bug 784. Copy correct values from an alternate couchdb schema

import httplib, json

from lib_couch import prettyPrint, Couch


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
