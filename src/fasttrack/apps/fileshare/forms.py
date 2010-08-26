from django import forms

from fileshare.models import FileShare

class UploadForm(forms.ModelForm):
    class Meta:
        model = FileShare
