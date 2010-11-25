import os
import hashlib

from django import forms
from django.template.loader import render_to_string

from fileshare.utils import SecurityProvider

path = os.path.abspath(os.path.split(__file__)[0])


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

    def __init__(self, instance, *args, **kwargs):
        self.instance = instance
        super(HashForm, self).__init__(*args, **kwargs)

    def save(self):
        self.instance.method = self.cleaned_data['method']
        return self.instance


class HashCode(SecurityProvider):
    name = 'Hash'
    description = 'Hash code security of file'
    has_configuration = True


    def __init__(self):
        self.is_storing_action = False
        self.is_retrieval_action = False
        self.active = True
        self.method = 'md5'

    def perform(self, document):
        h = hashlib.new(self.method)
        h.update(document)
        return h.hexdigest()


    @staticmethod
    def get_form():
        return HashForm


    def render(self):
        return render_to_string('%s/render.html' % path, {'method' :self.method })

