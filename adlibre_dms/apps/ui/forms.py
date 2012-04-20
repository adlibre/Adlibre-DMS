"""
Module: DMS UI Django Forms
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

from django import forms
from django.contrib.admin import widgets as admin_widgets


class CalendarForm(forms.Form):
    date = forms.DateField(widget = admin_widgets.AdminDateWidget)
