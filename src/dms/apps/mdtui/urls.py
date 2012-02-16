"""
Module: MDT UI URLS
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.views.generic.simple import redirect_to

import mdtui.views

urlpatterns = patterns('mdtui.views',
    url(r'^$', direct_to_template, {'template': 'home.html'}, name='mdtui-home'),

    url(r'^search/$', 'search', {'step':'1',}, name='mdtui-search'),
    url(r'^search/options$', 'search', {'step':'1',}, name='mdtui-search-1'),
    url(r'^search/results$', 'search', {'step':'2',},name='mdtui-search-2'),

    url(r'^indexing/$', 'indexing', {'step':'1',}, name='mdtui-index'),
    url(r'^indexing/1$', 'indexing', {'step':'1',}, name='mdtui-index-1'),
    url(r'^indexing/2$', 'indexing', {'step':'2',}, name='mdtui-index-2'),
    url(r'^indexing/3$', 'indexing', {'step':'3',}, name='mdtui-index-3'),
    url(r'^indexing/4$', 'indexing', {'step':'4',}, name='mdtui-index-4'),

)