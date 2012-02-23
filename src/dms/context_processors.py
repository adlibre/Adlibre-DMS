"""
Module: DMS Project Wide Context Processors
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

from django.conf import settings

def theme_template_base(context):
    """ Returns Global Theme Base Template """
    return {'THEME_TEMPLATE': settings.THEME_NAME+'_theme_base.html'}

def theme_name(context):
    """ Returns Global Theme Name """
    return {'THEME_NAME': settings.THEME_NAME}

def demo(context):
    """ Returns Demo Mode Boolean Context Variable """
    return {'DEMO': settings.DEMO}

def product_version(context):
    """ Returns Context Variable Containing Product version """
    return {'PRODUCT_VERSION': settings.PRODUCT_VERSION}