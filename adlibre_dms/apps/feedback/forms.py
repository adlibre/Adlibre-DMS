"""
Module: Feedback form for DMS MUI

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
Author: Iurii Garmash
"""

from django import forms
from django.conf import settings
from django.core.mail.message import EmailMessage
from django.template import loader
from django.utils.translation import ugettext_lazy as _


class EmailFormMixin(object):
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [email for _, email in settings.MANAGERS]

    subject_template_name = 'feedback_form/email_subject.txt'
    message_template_name = 'feedback_form/email_template.txt'

    def get_message(self):
        return loader.render_to_string(self.message_template_name, self.get_context())

    def get_subject(self):
        subject = loader.render_to_string(self.subject_template_name, self.get_context())
        return ''.join(subject.splitlines())

    def get_context(self):
        """
        Context sent to templates for rendering include the form's cleaned
        data and also the current Request object.
        """
        if not self.is_valid():
            raise ValueError("Cannot generate Context when form is invalid.")
        # Creating user data
        data = {
            'referer': self.request.META.get('HTTP_REFERER', ''),
            'user_ip': self.request.META.get('REMOTE_ADDR', ''),
            'user_agent': self.request.META.get('HTTP_USER_AGENT', '')
        }
        # Appending form data
        for key, value in self.cleaned_data.iteritems():
            data[key] = value
        return dict(request=self.request, **data)

    def get_email_headers(self):
        """
        Subclasses can replace this method to define additional settings like
        a reply_to value.
        """
        return None

    def get_message_dict(self):
        message_dict = {
                "from_email": self.from_email,
                "to": self.recipient_list,
                "subject": self.get_subject(),
                "body": self.get_message(),
            }
        headers = self.get_email_headers()
        if headers is not None:
            message_dict['headers'] = headers
        else:
            message_dict['headers'] = {'Reply-To': self.from_email}
        return message_dict

    def send_email(self, request, fail_silently=False):
        self.request = request
        return EmailMessage(**self.get_message_dict()).send(fail_silently=fail_silently)


class FeedbackForm(forms.Form, EmailFormMixin):
    feedback_body = forms.CharField(label=_(u'Message'), widget=forms.Textarea())