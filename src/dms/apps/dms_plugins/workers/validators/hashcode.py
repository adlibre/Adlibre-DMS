import hashlib

from django import forms
from django.conf import settings

from dms_plugins.pluginpoints import BeforeRetrievalPluginPoint, BeforeStoragePluginPoint
from dms_plugins.workers import Plugin, PluginError

class HashForm(forms.Form):
    OPTION = (
        ('md5','md5'),
        ('sha1','sha1'),
        ('sha224','sha224'),
        ('sha256','sha256'),
        ('sha384','sha384'),
        ('sha512','sha512'),
    )
    method = forms.ChoiceField(choices=OPTION)

    def __init__(self, options, *args, **kwargs):
        self.options = options
        super(HashForm, self).__init__(*args, **kwargs)

    def save(self, commit = True):
        method = self.options[0]
        method.name = 'method'
        method.value = self.cleaned_data['method']
        if commit:
            method.save()
        return method

class HashCodeValidationOnStoragePlugin(Plugin, BeforeStoragePluginPoint):
    title = 'Hash'
    description = 'Hash code calculation and saving on storage'
    plugin_type = "storage_processing"
    method = 'md5'
    has_configuration = True
    configurable_fields = ['method',]
    form = HashForm

    def work(self, request, document):
        method = self.get_option('method', document.get_doccode())
        return HashCodeWorker(self.method).work_store(request, document, method)

class HashCodeValidationOnRetrievalPlugin(Plugin, BeforeRetrievalPluginPoint):
    title = 'Hash'
    description = 'Hash code validation on retrieval'
    plugin_type = "retrieval_validation"
    method = 'md5'
    has_configuration = True
    configurable_fields = ['method',]
    form = HashForm
    
    def work(self, request, document):
        method = self.get_option('method', document.get_doccode())
        return HashCodeWorker(self.method).work_retrieve(request, document, method)

class HashCodeWorker(object):
    def __init__(self, method):
        self.method = method

    def get_hash(self, document, method, salt = settings.SECRET_KEY):
        h = hashlib.new(method)
        h.update(document)
        h.update(salt)
        return h.hexdigest()

    def work_store(self, request, document, method):
        new_hashcode = self.get_hash(document.get_file_obj().read(), method)
        document.set_hashcode(new_hashcode)
        document.save_hashcode(new_hashcode)
        return document

    def work_retrieve(self, request, document, method):
        hashcode = document.get_hashcode()
        new_hashcode = self.get_hash(document.get_file_obj().read(), method)
        #print "hadhcode = %s, new hashcode = %s" % (hashcode, new_hashcode)
        if hashcode and not (new_hashcode == hashcode):
            raise PluginError("Hashcode did not validate.", 500)
        #document.set_hashcode(new_hashcode) # should do this but it is meaningless :)
        return document
