"""
Module: DMS Browser Django URLs

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

from django.conf.urls import patterns, url
from django.views.generic import TemplateView

urlpatterns = patterns('browser.views',
    url(r'^$', TemplateView.as_view(template_name='browser/index.html'), name='home'),
    url(r'^settings/plugins$', 'plugins', name='plugins'),
    url(r'^upload/$', 'upload', name='upload'),
    url(r'^get/(?P<code>[\w_-]+)$', 'get_file', name='get_file'),
    url(r'^get/(?P<code>[\w_-]+)\.(?P<suggested_format>[\w_-]+)$', 'get_file', name='get_file'),
    url(r'^files/$', 'files_index', name='files_index'),
    url(r'^files/(?P<id_rule>\d+)/$', 'files_document', name='files_document'),
    url(r'^revision/(?P<document>.+)$', 'revision_document', name='revision_document'),
)
