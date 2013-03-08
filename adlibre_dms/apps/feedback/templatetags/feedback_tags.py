"""
Module: Feedback form inclusion tag

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
Author: Iurii Garmash
"""

from django import template
from django.conf import settings

from feedback import forms

register = template.Library()

@register.inclusion_tag("feedback_form/form.html")
def feedback():
    """
    Sets context variable field given as a parameter to tag.
    """
    form = forms.FeedbackForm()
    return {
        'feedback_form': form,
        'STATIC_URL': settings.STATIC_URL
    }