from django import forms
from django.contrib.admin import widgets as admin_widgets


class CalendarForm(forms.Form):
    date = forms.DateField(widget = admin_widgets.AdminDateWidget)