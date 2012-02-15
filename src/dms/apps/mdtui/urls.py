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
    url(r'^retrieve/$', 'retrieve', name='mdtui-retrieve'),
    url(r'^retrieve/options$', 'retrieve', {'step':'1',}, name='mdtui-retrieve-1'),
    url(r'^retrieve/results$', 'retrieve', {'step':'2',},name='mdtui-retrieve-2'),

    url(r'^upload/$', 'upload', name='mdtui-index'),
    url(r'^upload/1$', 'upload', {'step':'1',}, name='mdtui-index-1'),
    url(r'^upload/2$', 'upload', {'step':'2',}, name='mdtui-index-2'),
    url(r'^upload/3$', 'upload', {'step':'3',}, name='mdtui-index-3'),
    url(r'^upload/4$', 'upload', {'step':'4',}, name='mdtui-index-4'),

)