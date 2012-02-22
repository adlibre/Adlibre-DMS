"""
Module: DMS API Django URLs
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

from django.conf.urls.defaults import *
from piston.resource import Resource
from api import handlers

file_handler = Resource(handlers.FileHandler)
file_info_handler = Resource(handlers.FileInfoHandler)
file_list_handler = Resource(handlers.FileListHandler)
revision_count_handler = Resource(handlers.RevisionCountHandler)
rules_handler = Resource(handlers.RulesHandler)
rules_detail_handler = Resource(handlers.RulesDetailHandler)
plugins_handler = Resource(handlers.PluginsHandler)
tags_handler = Resource(handlers.TagsHandler)
mdt_handler = Resource(handlers.MetaDataTemplateHandler)

urlpatterns = patterns('',
   url(r'^file/', file_handler, name = "api_file"),
   url(r'^file-info/', file_info_handler, name = "api_file_info"),
   url(r'^files/(?P<id_rule>\d+)/$', file_list_handler, name = "api_file_list"),
   url(r'^revision_count/(?P<document>[\w_-]+)$', revision_count_handler, name = "api_revision_count"),
   url(r'^rules\.(?P<emitter_format>.+)$', rules_handler, name = "api_rules"),
   url(r'^rules/(?P<id_rule>\d+)\.(?P<emitter_format>.+)$', rules_detail_handler, name = "api_rules_detail"),
   url(r'^tags-(?P<id_rule>\d+)\.(?P<emitter_format>.+)$', tags_handler, name = "api_tags"),
   url(r'^plugins\.(?P<emitter_format>.+)$', plugins_handler, name = "api_plugins"),
   url(r'^mdt/$', mdt_handler, name = "api_mdt"),
)

