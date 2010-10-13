from django import forms

from fileshare.utils import SecurityProvider


class HashForm(forms.Form):
    salt = forms.CharField(max_length=255)
    method = forms.CharField(max_length=255)

    def __init__(self, instance, *args, **kwargs):
        self.instance = instance
        super(HashForm, self).__init__(*args, **kwargs)

    def save(self):
        pass


class MD5Hash(SecurityProvider):
    name = 'Hash'
    has_configuration = True


    def __init__(self):
        self.is_storing_action = False
        self.is_retrieval_action = True
        self.active = True

    @staticmethod
    def perform(request, document):
        return hashlib.md5(document).hexdigest()

    @staticmethod
    def get_form():
        return HashForm

    @staticmethod
    def available_method(self):
        return []

