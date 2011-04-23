import os

from django import forms
from django.template.loader import render_to_string

from newplugins.transfer import TransferPluginPoint


class GzipForm(forms.Form):
    OPTION = (
        ('Fast','1'),
        ('Best','9'),
        ('Medium','5'),
    )
    method = forms.ChoiceField(choices=OPTION)

    def __init__(self, instance, *args, **kwargs):
        self.instance = instance
        super(GzipForm, self).__init__(*args, **kwargs)

    def save(self):
        self.instance.method = self.cleaned_data['method']
        return self.instance


class GzipPlugin(TransferPluginPoint):
    title = 'Gzip Plugin'

    active = True
    has_configuration = True

    methods = ( 'RETRIEVAL', 'STORAGE', ) # acts on the following: retrieval, storage

    @staticmethod
    def work(file_obj, method):

        import zlib
        import tempfile

        file_obj.seek(0)
        content = file_obj.read()
        tmp_file_obj = tempfile.TemporaryFile()

        if method == 'STORAGE':
            tmp_file_obj.write(zlib.compress(content))
        elif method == 'RETRIEVAL':
            tmp_file_obj.write(zlib.decompress(content))
        return tmp_file_obj

    @staticmethod
    def get_form():
        return GzipForm

    def render(self):
        path = os.path.abspath(os.path.split(__file__)[0])
        return render_to_string('%s/gzip.html' % path, {'method' :self.method })