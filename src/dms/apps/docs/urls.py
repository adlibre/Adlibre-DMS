"""
Module: DMS Base Documentation Django URLs
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

from django.conf.urls.defaults import *


urlpatterns = patterns('docs.views',
     url(r'^$', 'documentation_index', name='documentation_index'),
     url(r'^about/$', 'about_documentation', name='about_documentation'),
     url(r'^api/$', 'api_documentation', name='api_documentation'),
     url(r'^technical/$', 'technical_documentation', name='technical_documentation'),
)
