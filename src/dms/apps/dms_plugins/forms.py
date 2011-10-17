from django import forms

from dms_plugins import models

#from django.core.exceptions import ValidationError

class MappingForm(forms.ModelForm):
    class Meta:
        model = models.DoccodePluginMapping

class PluginSelectorForm(forms.ModelForm):
    """
    Dynamic form that allows the user to change and then verify the data that was parsed
    
    Built based on code of Django Snippet: Dynamic Django form.
    http://djangosnippets.org/snippets/714/
    """
    
    def __init__(self, *args, **kwargs):
        super(PluginSelectorForm, self).__init__(*args, **kwargs)
    
    def setFields(self, kwds):
        """
        Set the fields in the form
        """
        keys = kwds.keys()
        keys.sort()
        for k in keys:
            self.fields[k] = kwds[k]

    def setData(self, kwds):
        """
        Set the data to include in the form
        """
        keys = kwds.keys()
        keys.sort()
        for k in keys:
            self.data[k] = kwds[k]

    def validation_ok(self):
        """
        Form validation sequence overridden here.
        validates only one field as far as it is critical for now.
        Doccode checks if it is selected or None.
        """
        
        if not self.data['doccode'] == u'':
            return True
        else: 
            msg = u"You have forgotten to select Doccode in order to set a mapping"
            
            if not self._errors: self._errors = {}
            self._errors["doccode"] = self.error_class([msg])
            return False

    class Meta:
        model = models.DoccodePluginMapping
        exclude = ('before_storage_plugins', 
                   'storage_plugins', 
                   'before_retrieval_plugins', 
                   'before_removal_plugins',
                   'before_update_plugins')



