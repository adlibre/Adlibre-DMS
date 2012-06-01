"""
Module: DMS Browser Django Forms

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

from django import forms


class UploadForm(forms.Form):
    file  = forms.FileField(widget=forms.FileInput(attrs={'size':40}))
