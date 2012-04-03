"""
Module: MDTUI forms
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
Author: Iurii Garmash

Dynamic form that allows the user to change and then verify the data that was parsed
Built based on code of Django Snippet: Dynamic Django form.
http://djangosnippets.org/snippets/714/
"""

from django import forms
import datetime

from dms_plugins.models import DOCRULE_CHOICES
from django.core.exceptions import ValidationError
from forms_representator import setFormFields
from forms_representator import setFormData

CUSTOM_ERRORS = {
    0: 'Must be Number. (example "123456")',
    1: 'Must be in valid Date format. (example "2012-12-31")'
}

class DocumentTypeSelectForm(forms.Form):
    docrule = forms.ChoiceField(choices = DOCRULE_CHOICES, label="Document Type")

class DocumentUploadForm(forms.Form):
    file = forms.FileField()

class DocumentIndexForm(forms.Form):
    """
    Form for posting document indexes.
    Has dynamic initialization abilities.
    """
    date = forms.DateField(initial=datetime.datetime.now(), label="Creation Date", help_text="Date of the document added")
    description = forms.CharField(max_length=100, label="Description", help_text="Brief Document Description")

    def __init__(self, *args, **kwargs):
        super(DocumentIndexForm, self).__init__(*args, **kwargs)

    def setFields(self, kwds):
        setFormFields(self, kwds)

    def setData(self, kwds):
        setFormData(self, kwds)

    def validation_ok(self):
        """
        Form validation sequence overridden here.
        Does check if field is entered (basic fields validation)
        Does Type validation for the proper data entry.
        E.g. if user enters ABC instead of 123 or date in wrong format.
        Char fields are only checked if entered at all.
        """
        # TODO: refactor this part to be used only for indexing
        for field in self.fields:
            cur_field = self.fields[field]
            # Simple if field entered validation
            try:
                # Validate only if those keys exist e.g in search usage there is no description field
                try:
                    cur_field.validate(self.data[unicode(field)])
                except ValidationError, e:
                    # appending error to form errors
                    self.errors[field] = e
                    self._errors[field] = e
            except KeyError:
                pass

            # Wrong type validation
            try:
                # Validate only if those keys exist
                if cur_field.__class__.__name__ == "IntegerField":
                    try:
                        int(self.data[unicode(field)])
                    except ValueError:
                        # appending error to form errors
                        if self.data[unicode(field)]:
                            # Wrong data entered adding type error
                            e = ValidationError(CUSTOM_ERRORS[0])
                            self.errors[field] = e
                            self._errors[field] = e
                        pass
                if cur_field.__class__.__name__ == "DateField":
                    try:
                        datetime.datetime.strptime(self.data[unicode(field)], "%Y-%m-%d")
                    except ValueError:
                        # appending error to form errors
                        if self.data[unicode(field)]:
                            # Wrong data entered adding type error
                            e = ValidationError(CUSTOM_ERRORS[1])
                            self.errors[field] = e
                            self._errors[field] = e
                        pass
            except KeyError:
                pass
        if self.errors:
            return False
        return True

class DocumentSearchOptionsForm(forms.Form):
    """
    Form for searching documents by indexes.
    Has dynamic initialization abilities.
    """
    date = forms.DateField(label="Creation Date From", help_text="Date of the document added")
    end_date = forms.DateField(required=False, label="To", help_text="Final possible document date")

    def __init__(self, *args, **kwargs):
        super(DocumentSearchOptionsForm, self).__init__(*args, **kwargs)

    def setFields(self, kwds):
        setFormFields(self, kwds)

    def setData(self, kwds):
        setFormData(self, kwds)

    def validation_ok(self):
        # TODO: add validation. e.g. only end_date provided.
        # TODO: add type validation
        return True

