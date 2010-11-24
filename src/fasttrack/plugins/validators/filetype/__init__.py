import pickle
import os
import magic

from django import forms
from django.template.loader import render_to_string
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse


from fileshare.utils import ValidatorProvider


path = os.path.abspath(os.path.split(__file__)[0])

class FileTypeForm(forms.Form):


    def __init__(self, instance, *args, **kwargs):
        self.instance = instance
        try:
            handler = open('%s/mimetypes.pickle' % path, "r")
            mimetypes = pickle.load(handler)
        except Exception, e:
            mimetypes = [
                ('pdf', 'application/pdf')
            ]

        super(FileTypeForm, self).__init__(*args, **kwargs)
        self.fields['mimetype'] = forms.ChoiceField(choices=mimetypes)


    def save(self):
        if not self.cleaned_data['mimetype'] in self.instance.available_type:
            self.instance.available_type.append(self.cleaned_data['mimetype'])
        return self.instance


def delete(request, rule, filetype, rule_id, plugin_type, plugin_index):
    index = request.GET.get("index")
    filetype.available_type.pop(int(index))
    plugins = rule.get_validators()
    plugins[int(plugin_index)] = filetype
    rule.validators = pickle.dumps(plugins)
    rule.save()
    return HttpResponseRedirect(reverse('plugin_setting', args=[rule_id, plugin_type, plugin_index]))


class FileTypeError(Exception):
    def __str__(self):
        return "FileTypeError - The file type is not allowed to be uploaded"


class FileType(ValidatorProvider):
    name = 'File Type'
    description = 'File Type Validator'
    has_configuration = True


    def __init__(self):
        self.is_storing_action = True
        self.is_retrieval_action = False
        self.active = True
        self.available_type = []

    def perform(self, request, document, filebuffer):
        mime = magic.Magic(mime=True)
        if not mime.from_buffer(filebuffer.read()) in self.available_type:
            raise FileTypeError
        return True

    @staticmethod
    def get_form():
        return FileTypeForm

    def render(self):
        return render_to_string('%s/list.html' % path, {'mimetype_list' :self.available_type })


    def action(self, action):
        if action == 'delete':
            return delete

