"""
Module: Forms specific Tags module.

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def context_set_filed(context, filed_name):
    """
    Sets context variable field given as a parameter to tag.
    """
    if not 'form' in context:
        return ''
    form = context['form']
    for field in form:
        if field.name == filed_name:
            context['field'] = field
    return ''