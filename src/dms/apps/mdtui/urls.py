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
    url(r'^upload/$', 'upload', name='mdtui-index'),
   # url(r'^upload/step-(?P<step>\d+)/$', 'upload'),


)