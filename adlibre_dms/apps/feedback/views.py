"""
Module: Feedback views for sending emails

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
Author: Iurii Garmash
"""
from django.core.urlresolvers import reverse
from django.views.generic import TemplateView, FormView

from feedback.forms import FeedbackForm


class FeedbackFormMixin(object):
    """
    Form view that sends email when form is valid. You'll need
    to define your own form_class and template_name.
    """
    def form_valid(self, form):
        form.send_email(self.request)
        return super(FeedbackFormMixin, self).form_valid(form)

    def get_success_url(self):
        return reverse("feedback_sent")


class FeedbackFormView(FeedbackFormMixin, FormView):
    template_name = "feedback_form/form.html"
    form_class = FeedbackForm


class FeedbackLeft(TemplateView):
    template_name = "feedback_form/feedback_sent.html"
