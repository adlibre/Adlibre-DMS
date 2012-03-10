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

    url(r'^indexing/$', 'indexing', {'step':'1',}, name='mdtui-index'),
    url(r'^indexing/1$', 'indexing', {'step':'1',}, name='mdtui-index-1'),
    url(r'^indexing/2$', 'indexing', {'step':'2',}, name='mdtui-index-2'),
    url(r'^indexing/3$', 'uploading', {'step':'3',}, name='mdtui-index-3'),
    url(r'^indexing/4$', 'uploading', {'step':'4',}, name='mdtui-index-4'),
    url(r'^indexing/5$', 'barcode', {'step':'5',}, name='mdtui-index-5'),

    url(r'^parallel/$', 'parallel_keys', name='parallell'),
)