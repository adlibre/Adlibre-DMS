from django import forms

from dms_plugins import models

class MappingForm(forms.ModelForm):
    class Meta:
        model = models.DoccodePluginMapping