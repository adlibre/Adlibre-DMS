"""
Module: Permissions for templates rendering helpers for MDTUI

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

from django import template
from mdtui.security import SEC_GROUP_NAMES

register = template.Library()

@register.simple_tag(takes_context=True)
def check_search_permit(context):
    """
    Checks request.user for permission to SEARCH in MUI

    In fact he must be in search group in security.
    Set's up context variable 'search_permitted'
    it can be used farther in IF template compassion.
    """
    # Do nothing if context variable has already been set
    if 'search_permitted' in context:
        return ''
    user = context['request'].user
    permission = False
    if not user.is_superuser:
        groups = user.groups.all()
        for group in groups:
            if group.name == SEC_GROUP_NAMES['search']:
                permission = True
    else:
        permission = True
    context['search_permitted'] = permission
    return ''

@register.simple_tag(takes_context=True)
def check_index_permit(context):
    """
    Checks request.user for permission to INDEX in MUI

    In fact he must be in search group in security.
    Set's up context variable 'index_permitted'
    it can be used farther in IF template compassion.
    """
    # Do nothing if context variable has already been set
    if 'index_permitted' in context:
        return ''
    user = context['request'].user
    permission = False
    if not user.is_superuser:
        groups = user.groups.all()
        for group in groups:
            if group.name == SEC_GROUP_NAMES['index']:
                permission = True
    else:
        permission = True
    context['index_permitted'] = permission
    return ''
