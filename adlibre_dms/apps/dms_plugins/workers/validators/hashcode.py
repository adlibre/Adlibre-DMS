"""
Module: Hashcode Plugin
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
"""

import hashlib

from django import forms
from django.conf import settings

from dms_plugins.pluginpoints import BeforeRetrievalPluginPoint, BeforeStoragePluginPoint, BeforeUpdatePluginPoint
from dms_plugins.workers import Plugin, PluginError


class HashForm(forms.Form):
    """Form for configuration of those plugins options in DMS config"""
    OPTION = (
        ('md5', 'md5'),
        ('sha1', 'sha1'),
        ('sha224', 'sha224'),
        ('sha256', 'sha256'),
        ('sha384', 'sha384'),
        ('sha512', 'sha512'),
    )
    method = forms.ChoiceField(choices=OPTION)

    def __init__(self, options, *args, **kwargs):
        self.options = options
        super(HashForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        """Stores setting for a plugin
        @param commit: execute save()"""
        method = self.options[0]
        method.name = 'method'
        method.value = self.cleaned_data['method']
        if commit:
            method.save()
        return method


class HashCodeValidationOnStoragePlugin(Plugin, BeforeStoragePluginPoint):
    """Validates hash codes on storing a file for code"""
    title = 'Hash'
    description = 'Hash code calculation and saving on storage'
    plugin_type = "storage_processing"
    method = 'md5'
    has_configuration = True
    configurable_fields = ['method', ]
    form = HashForm

    def work(self, document):
        """Main plugin method
        @param document: DMS Document() instance"""
        method = self.get_option('method', document.get_docrule())
        return HashCodeWorker(self.method).work_store(document, method)


class HashCodeValidationOnUpdatePlugin(Plugin, BeforeUpdatePluginPoint):
    """Validates hash codes on updating a file for code"""
    title = 'Hash'
    description = 'Hash code calculation and saving on object update. (Usually on new revision upload)'
    plugin_type = "update_processing"
    method = 'md5'
    has_configuration = True
    configurable_fields = ['method', ]
    form = HashForm

    def work(self, document):
        """Main plugin method
        @param document: DMS Document() instance"""
        method = self.get_option('method', document.get_docrule())
        return HashCodeWorker(self.method).work_store(document, method)


class HashCodeValidationOnRetrievalPlugin(Plugin, BeforeRetrievalPluginPoint):
    """Validates hash codes on retrieving a file for code"""
    title = 'Hash'
    description = 'Hash code validation on retrieval'
    plugin_type = "retrieval_validation"
    method = 'md5'
    has_configuration = True
    configurable_fields = ['method', ]
    form = HashForm
    
    def work(self, document):
        """Main plugin method
        @param document: DMS Document() instance"""
        method = self.get_option('method', document.get_docrule())
        return HashCodeWorker(self.method).work_retrieve(document, method)


class HashCodeWorker(object):
    """Main Hash Codes plugin worker"""
    def __init__(self, method):
        self.method = method

    def get_hash(self, document, method, salt=settings.SECRET_KEY):
        """Retruns hash for a given document"""
        h = hashlib.new(method)
        h.update(document)
        h.update(salt)
        return h.hexdigest()

    def work_store(self, document, method):
        """Stores hash for given document"""
        new_hashcode = self.get_hash(document.get_file_obj().read(), method)
        document.set_hashcode(new_hashcode)
        document.save_hashcode(new_hashcode)
        return document

    def work_retrieve(self, document, method):
        """Reads hash for given document"""
        if document.get_file_obj():
            hashcode = document.get_hashcode()
            new_hashcode = self.get_hash(document.get_file_obj().read(), method)
            if hashcode and not (new_hashcode == hashcode):
                raise PluginError("Hashcode did not validate.", 500)
        return document
