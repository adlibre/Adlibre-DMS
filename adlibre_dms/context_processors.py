"""
Module: DMS Project Wide Context Processors
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

import os

from django.conf import settings

def theme_template_base(context):
    """ Returns Global Theme Base Template """
    template_path = os.path.join(settings.THEME_NAME, 'theme.html')
    return {'THEME_TEMPLATE': template_path}

def theme_name(context):
    """ Returns Global Theme Name """
    return {'THEME_NAME': settings.THEME_NAME}

def demo(context):
    """ Returns Demo Mode Boolean Context Variable """
    return {'DEMO': settings.DEMO}

def product_version(context):
    """ Returns Context Variable Containing Product version """
    return {'PRODUCT_VERSION': settings.PRODUCT_VERSION}

def aui_url(context):
    """ Returns Context Variable Containing Product version """
    try:
        url = settings.AUI_URL
    except AttributeError:
        url = False
        pass
    return {'AUI_URL': url}

def date_format(context):
    """ Returns Context Variable Containing Date format currently used """
    return {'DATE_FORMAT': settings.DATE_FORMAT.replace('%', '')}

def datetime_format(context):
    """ Returns Context Variable Containing Datetime format currently used """
    return {'DATETIME_FORMAT': settings.DATETIME_FORMAT.replace('%', '')}

def stage_variable(context):
    """ Determine if we currently running on stage production """
    return {'STAGE': settings.STAGE_KEYWORD}


