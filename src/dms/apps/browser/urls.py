"""
Module: DMS Browser Django URLs
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

from django.conf.urls.defaults import *

# TODO: Are these regexes optimal?

# DECISION: Need to make adding ruleid option to request url
# eg /get/{ruleid}/MYDOC.pdf

urlpatterns = patterns('browser.views',
    url(r'^settings/plugins$',
        'plugins',
        name='plugins'),
    url(r'^upload/$', 'upload', name='upload'),
    url(r'^get/(?P<document>.+)$',
        'get_file', name='get_file'),
    url(r'^files/$',
        'files_index', name='files_index'),
    url(r'^files/(?P<id_rule>\d+)/$',
        'files_document', name='files_document'),
    url(r'^revision/(?P<document>.+)$',
        'revision_document', name='revision_document'),
)