"""
Module: General Date conversion modules

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import datetime
import logging

from django.conf import settings

log = logging.getLogger('dms')


def date_standardized(date_string):
    """Converts date from format %Y-%m-%d into proper DMS global date format"""
    new_date_str = datetime.datetime.strptime(date_string, '%Y-%m-%d').strftime(settings.DATE_FORMAT)
    return new_date_str


def str_date_to_couch(from_date):
    """
    Converts date from form date widget generated format

    e.g.:
    date '2012-03-02' or whatever format specified in settings.py
    to CouchDocument stored date. E.g.: '2012-03-02T00:00:00Z'
    """
    # HACK: left here to debug improper date conversion calls
    converted_date = ''
    try:
        couch_date = datetime.datetime.strptime(from_date, settings.DATE_FORMAT)
        converted_date = str(couch_date.strftime(settings.DATE_COUCHDB_FORMAT))
    except ValueError:
        log.error('adlibre.date_convertor time conversion error. String received: %s' % from_date)
        pass
    return converted_date