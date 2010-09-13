import os

from django import forms

from fileshare.models import (FileShare,
    available_splitters, available_validators, available_storages,
    get_validator)

class UploadForm(forms.Form):
    file  = forms.FileField()

    def clean_file(self):
        file = self.files['file']
        filename = self.files['file'].name
        validator = get_validator()
        if not validator.validate(os.path.splitext(filename)[0]):
            raise forms.ValidationError("Your document code is not valid")
        return file

def splitter_choices():
    splitters = []
    for splitter in available_splitters():
        splitters.append([splitter, splitter])
    return splitters


def validator_choices():
    validators = []
    for validator in available_validators().keys():
        validators.append([validator, validator])
    return validators


def storage_choices():
    storages = []
    for storage in available_storages():
        storages.append([storage, storage])
    return storages


class SettingForm(forms.Form):
    splitter = forms.ChoiceField(label="Split Method",
        widget=forms.RadioSelect, choices=splitter_choices())
    validator = forms.ChoiceField(label="Validator",
        widget=forms.RadioSelect, choices=validator_choices())
    storage = forms.ChoiceField(label="Storage",
        widget=forms.RadioSelect, choices=storage_choices())

