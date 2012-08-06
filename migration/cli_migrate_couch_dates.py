#! /usr/bin/python2.6

import httplib, json, datetime

from lib_couch import prettyPrint, Couch


MIGRATION_DATE_PATTERN = '%Y-%m-%d' # <<< MIGRATE FROM THIS PATTERN

def unify_index_info_couch_dates_fmt(index_info):
    """
    Applies standardization to secondary keys 'date' type keys.
    """
    clean_info = {}
    index_keys = [key for key in index_info.iterkeys()]
    for index_key in index_keys:
        if not index_key=='date':
            try:
                value = index_info[index_key]
                index_date = datetime.datetime.strptime(value, MIGRATION_DATE_PATTERN)
                clean_info[index_key] = str_date_to_couch(value)
            except ValueError:
                clean_info[index_key] = index_info[index_key]
                pass
        else:
            clean_info[index_key] = index_info[index_key]
    return clean_info

def str_date_to_couch(from_date):
    """
    Converts date from form date widget generated format

    e.g.:
    date '2012-03-02' or whatever format specified in settings.py
    to CouchDocument stored date. E.g.: '2012-03-02T00:00:00Z'
    """
    # HACK: left here to debug improper date calls
    converted_date = ''
    try:
        couch_date = datetime.datetime.strptime(from_date, MIGRATION_DATE_PATTERN)
        converted_date = str(couch_date.strftime("%Y-%m-%dT00:00:00Z"))
    except ValueError:
        print 'adlibre.date_convertor time conversion error. String received: %s' % from_date
        pass
    return converted_date

def reformatDates():
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

        d['mdt_indexes'] = unify_index_info_couch_dates_fmt(d['mdt_indexes'])

        d_enc = json.dumps(d)
        print db.saveDoc(dbName, d_enc, docId=bar_code)

if __name__ == "__main__":
    reformatDates()
