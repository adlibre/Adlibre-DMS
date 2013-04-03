"""
Module: Template rendering helpers for MDTUI

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def set_rev_item(context, rev):
    """returns a value for this dict element"""
    metadata = context['metadata']
    rev_dict = ''
    try:
        rev_dict = metadata[rev]
    except Exception, e:
        print e
        pass
    context['rev'] = rev_dict
    return ''