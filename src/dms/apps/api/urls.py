"""
Module: DMS API Django URLs
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

from django.conf.urls.defaults import *
from piston.resource import Resource
from handlers import FileHandler, FileListHandler, RevisionCountHandler

file_handler = Resource(FileHandler)
file_list_handler = Resource(FileListHandler)
revision_count_handler = Resource(RevisionCountHandler)
#rules_handler = Resource(RulesHandler)
#plugins_handler = Resource(PluginsHandler)

urlpatterns = patterns('',
   url(r'^file/', file_handler),
   url(r'^files/(?P<id_rule>\d+)/$', file_list_handler),
   url(r'^revision_count/(?P<document>[\w_-]+)$', revision_count_handler),
#   url(r'^rules\.(?P<emitter_format>.+)$', rules_handler),
#   url(r'^rules/(?P<id_rule>\d+)\.(?P<emitter_format>.+)$', Resource(RulesDetailHandler)),
#   url(r'^plugins\.(?P<emitter_format>.+)$', plugins_handler),
)

