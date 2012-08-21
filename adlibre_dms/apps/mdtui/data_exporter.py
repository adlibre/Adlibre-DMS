"""
Module: MDTUI data exporting Moodule

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import csv
from django.http import HttpResponse
from doc_codes.models import DocumentTypeRuleManagerInstance
from adlibre.date_converter import date_standardized

import logging

log = logging.getLogger('dms.mdtui.data_exporter')

def export_to_csv(search_keys, sec_keys_names, documents):
    """Helper to produce proper CSV file for search results export"""
    # Cleaning Up documents
    docs = {}
    for document in documents:
        docs[document.id] = document._doc
    # Init response CSV file
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment; filename=search_results.csv'
    writer = csv.writer(response)
    # Writing table headers
    counter = ['File',] + ['Date'] + ['Description',] + sec_keys_names + ['Type',]
    writer.writerow(counter)
    # Writing each file's data into appropriate rows
    for name, doc in docs.iteritems():
        doc_sec_keys = []
        for sec_key in sec_keys_names:
            try:
                # Adding secondary key's value for doc
                doc_sec_keys.append(doc['mdt_indexes'][sec_key])
            except KeyError:
                # No value exists
                doc_sec_keys.append('Not given',)
        # Converting date to Y-m-d format
        # TODO: fix this and find a cause of it. What adds time to indexes? ( Refs #807 )
        try:
            cr_date = date_standardized(doc['metadata_created_date'].rstrip('T00:00:00Z'))
        except ValueError:
            cr_date = doc['metadata_created_date']
            log.error('Wrong date index in database!: doc._id: %s' % doc['_id'])
            pass
        # Catching Document's type rule to name it in export
        # This way should not produce SQL DB requests (Uses DocumentTypeRuleManagerInstance for this)
        docrule = DocumentTypeRuleManagerInstance.get_docrule_by_id(doc['metadata_doc_type_rule_id'])
        docrule_name = docrule.get_title()
        # Final row adding
        doc_row = [name,] + [cr_date,] + [doc['metadata_description']] + doc_sec_keys + [docrule_name,]
        writer.writerow(doc_row)

    # Appending search request parameters into CSV
    writer.writerow('\r\n')
    writer.writerow(['Search with Keys:'])
    writer.writerow(['Key','Value'])
    for item, value in search_keys.iteritems():
        if item == u'date':
            item = u'Creation Date'
        if item == u'end_date':
            item = u'Creation Date to'
        if item == u'description':
            item = u'Description'
        if item == u'docrule_id':
            item = u'Document Type'
            id = value
            docrule = DocumentTypeRuleManagerInstance.get_docrule_by_id(id)
            value = docrule.get_title()
        if not value.__class__.__name__ == 'tuple':
            writer.writerow([unicode(item), unicode(value)])
        else:
            writer.writerow(unicode(item) + u': (from: ' + unicode(value[0]) + u' to: ' + unicode(value[1]) + u')')
    return response
