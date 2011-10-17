from django import forms

from dms_plugins import models

from django.core.exceptions import ValidationError

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
  
#    def validate(self, post):
#        """
#        Validate the contents of the form
#        """
#        
#        
#        for name,field in self.fields.items():
#            try:
#                field.clean(post[name])
#            except ValidationError, e:
#                self.errors[name] = e.messages
    
    def is_valid(self):
        """
        Form validation sequence overridden here.
        validates only one field as far as it is critical for now.
        Doccode checks if it is selected.
        """
        # TODO: add error to the existing form to be able to return form with faulty field and all data.
        if not self.data['doccode'] == u'':
            return True
        else: return False

    class Meta:
        model = models.DoccodePluginMapping
        exclude = ('before_storage_plugins', 
                   'storage_plugins', 
                   'before_retrieval_plugins', 
                   'before_removal_plugins',
                   'before_update_plugins')



