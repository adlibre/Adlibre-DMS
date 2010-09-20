import os

from django import forms

from fileshare.models import (available_splitters, available_validators,
    available_hash, available_storages, Rule)

class UploadForm(forms.Form):
    file  = forms.FileField()


def splitter_choices():
    splitters = []
    for splitter in available_splitters():
        splitters.append([splitter, splitter])
    return splitters


def validator_choices():
    validators = []
    for validator, plugin in available_validators().items():
        validators.append([validator, '%s - %s' % (validator, plugin.description)])
    return validators


def storage_choices():
    storages = []
    for storage in available_storages():
        storages.append([storage, storage])
    return storages


def hash_choices():
    hashcodes = []
    for hashcode in available_hash():
        hashcodes.append([hashcode, hashcode])
    return hashcodes


class SettingForm(forms.ModelForm):
    validator = forms.ChoiceField(label="DocCode",
        choices=validator_choices())
    storage = forms.ChoiceField(label="Storage",
        choices=storage_choices())
    splitter = forms.ChoiceField(label="Split Method",
        choices=splitter_choices())
    hashcode = forms.ChoiceField(label="HashCode",
        choices=hash_choices())

    class Meta:
        model = Rule

