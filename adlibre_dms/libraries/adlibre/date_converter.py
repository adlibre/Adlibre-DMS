"""
Module: General Date conversion modules

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

import datetime

from django.conf import settings


def date_standardized(date_string):
    """Converts date from format %Y-%m-%d into proper DMS global date format"""
    new_date_str = datetime.datetime.strptime(date_string, '%Y-%m-%d').strftime(settings.DATE_FORMAT)
    return new_date_str