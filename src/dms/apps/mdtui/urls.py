"""
Module: Metadata Template UI URLS
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('mdtui.views',
    url(r'^$', direct_to_template, {'template': 'mdtui/home.html'}, name='mdtui-home'),

    url(r'^search/$', 'search_type', {'step':'type',}, name='mdtui-search'),
    url(r'^search/type', 'search_type', {'step':'type',}, name='mdtui-search-type'),
    url(r'^search/options$', 'search_options', {'step':'options',}, name='mdtui-search-options'),
    url(r'^search/results$', 'search_results', {'step':'results',}, name='mdtui-search-results'),
    url(r'^search/view/(?P<code>[\w-]+)$', 'search_viewer', {'step':'view',}, name='mdtui-search-view'),

    url(r'^indexing/$', 'indexing_select_type', {'step':'1',}, name='mdtui-index'),
    url(r'^indexing/1$', 'indexing_select_type', {'step':'1',}, name='mdtui-index-1'),
    url(r'^indexing/2$', 'indexing_details', {'step':'2',}, name='mdtui-index-2'),
    url(r'^indexing/3$', 'indexing_uploading', {'step':'3',}, name='mdtui-index-3'),
    url(r'^indexing/4$', 'indexing_finished', {'step':'4',}, name='mdtui-index-finished'),
    url(r'^indexing/5$', 'indexing_barcode', {'step':'5',}, name='mdtui-index-5'),

    url(r'^parallel/$', 'mdt_parallel_keys', name='mdtui-parallel-keys'),
)