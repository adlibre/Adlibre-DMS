"""
Module: Feedback form URL's

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
Author: Iurii Garmash
"""
from django.contrib.auth.decorators import login_required
from django.conf.urls import url, patterns

from views import FeedbackLeft, FeedbackFormView

urlpatterns = patterns('',
                       url(r'^$', login_required(FeedbackFormView.as_view()), name="feedback"),
                       url(r'^completed/$', login_required(FeedbackLeft.as_view()), name="feedback_sent"),
)