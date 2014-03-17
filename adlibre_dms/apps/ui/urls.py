"""
Module: DMS UI Django URLs
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

from django.conf.urls import patterns, url

urlpatterns = patterns('ui.views',
    url(r'^upload-document/$', 'upload_document', name='ui_upload_document'),
    url(r'^rule-(?P<id_rule>\d+)/$', 'document_list', name='ui_document_list'),
    url(r'^document-(?P<document_name>.+)/$', 'document', name='ui_document'),
    url(r'', 'rule_list', name='ui_rule_list'),
)
