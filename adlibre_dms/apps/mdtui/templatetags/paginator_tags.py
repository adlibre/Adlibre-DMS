"""
Module: Paginator template rendering helpers for MDTUI

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

from django import template
from django.conf import settings

SEP = getattr(settings, 'MUI_SEARCH_PAGINATOR_PAGE_SEPARATOR', '...')
register = template.Library()

@register.simple_tag(takes_context=True)
def pages_sequence(context, paginated):
    """
    Generates pages sequence for rendering paginator pages list

    Note!: Assuming we have more then 10 pages
    """
    if paginated.paginator.num_pages > 9:
        context['rebuild_paginated'] = rebuild_sequence_digg(paginated)
    return ''

def rebuild_sequence_digg(paginated):
    """
    Rebuilding pages range into sequence of digg like paginator.

    e.g.:
    |1|2|...|4|_5_|6|...|20|21|
    here page 5 is current
    So you can iterate through that
    and render paginator pages in template simply with "for" loop

    Assuming pages range is more, or equal 10 pages
    """
    sep = str(SEP)
    output_range = []
    current_page = paginated.number
    prev_to_current_page = current_page - 1
    next_to_current_page = current_page + 1
    last_page = paginated.paginator.num_pages
    prev_to_last_page = last_page - 1
    prev_to_prev_last_page = last_page - 2
    first_end_page = last_page - 3
    if current_page == 1:
        output_range = [1, 2, sep, prev_to_last_page, last_page]
    elif current_page == 2:
        output_range = [1, 2, 3, sep, prev_to_last_page, last_page]
    elif current_page == 3:
        output_range = [1, 2, 3, 4, sep, prev_to_last_page, last_page]
    elif current_page == 4:
        output_range = [1, 2, 3, 4, 5, sep, prev_to_last_page, last_page]
    elif current_page == first_end_page:
        output_range = [1, 2, sep, prev_to_current_page, current_page, next_to_current_page, prev_to_last_page, last_page]
    elif current_page == prev_to_prev_last_page:
        output_range = [1, 2, sep, prev_to_current_page, current_page, prev_to_last_page, last_page]
    elif current_page == prev_to_last_page:
        output_range = [1, 2, sep, prev_to_current_page, current_page, last_page]
    elif current_page == last_page:
        output_range = [1, 2, sep, prev_to_last_page, last_page]
    elif current_page < first_end_page > 4:
        output_range = [1, 2, sep, prev_to_current_page, current_page, next_to_current_page, sep, prev_to_last_page, last_page]
    return output_range
