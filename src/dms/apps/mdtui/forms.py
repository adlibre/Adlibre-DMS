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

class DocumentTypeSelectForm(forms.Form):
    docrule = forms.ChoiceField(choices = DOCRULE_CHOICES, label="Document Type")

class DocumentIndexForm(forms.Form):
    """
    Dynamic form that allows the user to change and then verify the data that was parsed

    Built based on code of Django Snippet: Dynamic Django form.
    http://djangosnippets.org/snippets/714/

    form usage:

    """
    date = forms.DateField(initial=datetime.datetime.now(), label = "Creation Date", help_text = "Date of the document added")
    description = forms.CharField(max_length=255, label = "Description", help_text="Brief Document Description")

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
        for k in keys:
            self.data[k] = kwds[k]

    def validation_ok(self):
        """
        Form validation sequence overridden here.
        validates only one field as far as it is critical for now.
        """

#        if not self.data['docrule'] == u'':
        return True
#        else:
#            msg = u"You have forgotten to select Docrule in order to set a mapping"
#
#            if not self._errors: self._errors = {}
#            self._errors["doccode"] = self.error_class([msg])
#            return False