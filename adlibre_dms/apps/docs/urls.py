"""
Module: DMS Base Documentation Django URLs
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

from django.conf.urls import patterns, url
from django.views.generic import TemplateView

urlpatterns = patterns('',
    url(
        r'^main/$',
        TemplateView.as_view(template_name='docs/documentation_index.html'),
        name='documentation_index'
    ),
    url(
        r'^about/$',
        TemplateView.as_view(template_name='docs/about_documentation.html'),
        name='about_documentation'
    ),
    url(
        r'^api/$',
        TemplateView.as_view(template_name='docs/api_documentation.html'),
        name='api_documentation'
    ),
    url(
        r'^technical/$',
        TemplateView.as_view(template_name='docs/technical_documentation.html'),
        name='technical_documentation'
    ),
)
