"""
Module: MDTUI forms
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash
"""

from django import forms
import datetime

from dms_plugins.models import DOCRULE_CHOICES
from django.core.exceptions import ValidationError

class DocumentTypeSelectForm(forms.Form):
    docrule = forms.ChoiceField(choices = DOCRULE_CHOICES, label="Document Type")

class DocumentUploadForm(forms.Form):
    file = forms.FileField()

class DocumentIndexForm(forms.Form):
    """
    Dynamic form that allows the user to change and then verify the data that was parsed

    Built based on code of Django Snippet: Dynamic Django form.
    http://djangosnippets.org/snippets/714/

    form usage:

    """
    date = forms.DateField(initial=datetime.datetime.now(), label="Creation Date", help_text="Date of the document added")
    description = forms.CharField(max_length=255, label="Description", help_text="Brief Document Description")

    def __init__(self, *args, **kwargs):
        super(DocumentIndexForm, self).__init__(*args, **kwargs)

    def setFields(self, kwds):
        """
        Set the fields in the form
        """
        keys = kwds.keys()
        keys.sort()
        for k in keys:
            self.fields[k] = kwds[k]

    def setData(self, kwds):
        """
        Set the data to include in the form
        """
        keys = kwds.keys()
        keys.sort()

        self.is_valid()
        for k in keys:
            self.data[k] = kwds[k]
            try:
                self.initial[k] = int(kwds[k])
            except ValueError:
                try:
                    # TODO: test/debug this DATE type fields are yet not tested
                    self.fields[k].initial = datetime.datetime.strptime(kwds[k], "%Y-%m-%d")
                except ValueError:
                    try:
                        self.initial[k] = kwds[k]
                    except ValueError:
                        pass

    def validation_ok(self):
        """
        Form validation sequence overridden here.
        """
        for field in self.fields:
            cur_field = self.fields[field]
            #print cur_field
            try:
                cleaned_value = cur_field.validate(self.data[unicode(field)])
            except Exception, e:
                #print e
                # appending error to form errors
                self.errors[field] = e
                self._errors[field] = e

            # TODO: dynamic data (type based validation here)
        if self.errors:
            return False
        return True
