"""
Module: Metadata Template UI URLS
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
"""

from django.conf.urls import patterns, url
from django.views.generic import TemplateView
from views import MuiIndexingView

urlpatterns = patterns('mdtui.views',
    # Home
    url(r'^$', TemplateView.as_view(template_name='mdtui/home.html'), name='mdtui-home'),
    # Search
    url(r'^search/type$', 'search_type', {'step': 'type', }, name='mdtui-search'),
    url(r'^search/type', 'search_type', {'step': 'type', }, name='mdtui-search-type'),
    url(r'^search/options$', 'search_options', {'step': 'options'}, name='mdtui-search-options'),
    url(r'^search/results$', 'search_results', {'step': 'results'}, name='mdtui-search-results'),
    url(r'^search/export/$', 'search_results', {'step': 'export'}, name='mdtui-search-export'),
    # Indexing
    url(r'^indexing/type$', MuiIndexingView.as_view(), name='mdtui-index-type'),
    url(r'^indexing/details$', 'indexing_details', {'step': '2'}, name='mdtui-index-details'),
    url(r'^indexing/source$', 'indexing_source', {'step': '3'}, name='mdtui-index-source'),
    url(r'^indexing/finished$', 'indexing_finished', {'step': '4'}, name='mdtui-index-finished'),
    # Indexing Edit
    url(r'^edit/(?P<code>[\w_-]+)$', 'edit', {'step': 'edit'}, name='mdtui-edit'),
    url(r'^edit_type/(?P<code>[\w_-]+)$', 'edit_type', {'step': 'edit_type'}, name='mdtui-edit-type'),
    url(r'^edit_revisions/(?P<code>[\w_-]+)$', 'edit_file_revisions', name='mdtui-edit-revisions'),
    url(r'^edit_delete/(?P<code>[\w_-]+)$', 'edit_file_delete', name='mdtui-edit-delete'),
    url(r'^edit_finished$', 'edit_result', {'step': 'edit_finish'}, name='mdtui-edit-finished'),
    # Common
    url(r'^download/(?P<code>[\w_-]+)$', 'download_pdf', name='mdtui-download-pdf'),
    url(r'^view/(?P<code>[\w_-]+)$', 'view_object', {'step': 'view'}, name='mdtui-view-object'),
    # AJAX
    url(r'^parallel/$', 'mdt_parallel_keys', name='mdtui-parallel-keys'),
)

urlpatterns += patterns('mdtui.upload_handler_views',
    url(r'^upload_progress/$', 'upload_progress', name='mdtui-upload-progress'),
)