import pickle

from django import forms
from django.template.loader import render_to_string


from fileshare.utils import ValidatorProvider


class FileTypeForm(forms.Form):
    name = forms.CharField(max_length=255)


    def __init__(self, *args, **kwargs):


        filetype_list = [
            ('pdf', 'application/pdf')
        ]

        super(FileTypeForm, self).__init__(*args, **kwargs)
        self.fields['mimetype'] = forms.ChoiceField(choices=filetype_list)




class FileType(ValidatorProvider):
    name = 'File Type'
    description = 'File Type Validator'
    active = True
    has_configuration = True
    available_type = []

    @staticmethod
    def perform(request):
        return True

    @staticmethod
    def get_form():
        return FileTypeForm

