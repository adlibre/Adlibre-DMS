"""
Module: MDTUI data exporting Moodule

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import csv
import re
import logging

from django.http import HttpResponse

from core.models import DocumentTypeRuleManager
from adlibre.date_converter import date_standardized

log = logging.getLogger('dms.mdtui.data_exporter')


def export_to_csv(search_keys, sec_keys_names, documents):
    """Helper to produce proper CSV file for search results export"""
    dman = DocumentTypeRuleManager()
    # Cleaning Up documents
    docs = {}
    for document in documents:
        docs[document.id] = document._doc
    # Init response CSV file
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=search_results.csv'
    writer = csv.writer(response)
    # Writing table headers
    counter = ['File', ] + ['Date'] + ['Username'] + ['Description', ] + sec_keys_names + ['Type', ]
    writer.writerow(counter)
    # Writing each file's data into appropriate rows
    for name, doc in docs.iteritems():
        doc_sec_keys = []
        for sec_key in sec_keys_names:
            try:
                # Adding secondary key's value for doc
                doc_sec_keys.append(unicode(doc['mdt_indexes'][sec_key]).encode('utf8'))
            except KeyError:
                # No value exists
                doc_sec_keys.append('Not given',)
        # Converting date to Y-m-d format
        cr_date = date_standardized(re.sub("T\d{2}:\d{2}:\d{2}Z", "", doc['metadata_created_date']))
        # Catching Document's type rule to name it in export
        # This way should not produce SQL DB requests (Uses DocumentTypeRuleManagerInstance for this)
        docrule = dman.get_docrule_by_id(doc['metadata_doc_type_rule_id'])
        docrule_name = docrule.get_title()
        # Final row adding
        doc_row = [unicode(name).encode('utf8'), ] + [cr_date, ] + [unicode(doc['metadata_user_name']).encode('utf8'), ]+ [unicode(doc['metadata_description']).encode('utf8')] + doc_sec_keys + [unicode(docrule_name).encode('utf8'),]
        writer.writerow(doc_row)

    # Appending search request parameters into CSV
    writer.writerow('\r\n')
    writer.writerow(['Search with Keys:'])
    writer.writerow(['Key','Value'])
    for item, value in search_keys.iteritems():
        if item == u'date':
            item = u'Indexing Date'
        if item == u'end_date':
            item = u'Indexing Date to'
        if item == u'description':
            item = u'Description'
        if item == u'docrule_id':
            item = u'Document Type'
            id = value
            docrule = dman.get_docrule_by_id(id)
            value = docrule.get_title()
        if not value.__class__.__name__ == 'tuple':
            writer.writerow([unicode(item).encode('utf8'), unicode(value).encode('utf8')])
        else:
            writer.writerow(unicode(item).encode('utf8') + u': (from: ' + unicode(value[0]).encode('utf8') + u' to: ' + unicode(value[1]).encode('utf8') + u')')
    return response
