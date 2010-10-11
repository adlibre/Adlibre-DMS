from django import forms

from fileshare.utils import SecurityProvider


class HashForm(forms.Form):
    salt = forms.CharField(max_length=255)
    method = forms.CharField(max_length=255)


class MD5Hash(SecurityProvider):
    name = 'Hash'
    active = True
    has_configuration = True

    @staticmethod
    def perform(document):
        return hashlib.md5(document).hexdigest()

    @staticmethod
    def get_form():
        return HashForm

