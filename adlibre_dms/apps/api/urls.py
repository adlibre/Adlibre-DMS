"""
Module: DMS API Django URLs

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

from django.conf.urls import patterns, url
from piston.resource import Resource
from api import handlers

# Deprecated file handler
old_file_handler = Resource(handlers.OldFileHandler)

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
    # Deprecated file handlers:
    # /api/file/ABC1234
    url(r'^file/(?P<code>[\w_-]+)$', old_file_handler, name='api_file_deprecated'),
    # /api/file/ABC1234.pdf
    url(r'^file/(?P<code>[\w_-]+)\.(?P<suggested_format>[\w_-]+)$', old_file_handler, name='api_file_deprecated'),

    # Working handlers:
    # /api/file/ABC1234
    url(r'^new_file/(?P<code>[\w_-]+)$', file_handler, name='api_file'),
    # /api/file/ABC1234.pdf
    url(r'^new_file/(?P<code>[\w_-]+)\.(?P<suggested_format>[\w_-]+)$', file_handler, name='api_file'),
    # /api/file-info/ABC1234
    url(r'^file-info/(?P<code>[\w_-]+)$', file_info_handler, name='api_file_info'),
    # /api/file-info/ABC1234.pdf
    url(r'^file-info/(?P<code>[\w_-]+)\.(?P<suggested_format>[\w_-]+)', file_info_handler, name='api_file_info'),
    url(r'^files/(?P<id_rule>\d+)/$', file_list_handler, name='api_file_list'),
    url(r'^revision_count/(?P<document>[\w_-]+)$', revision_count_handler, name='api_revision_count'),
    url(r'^rules\.(?P<emitter_format>.+)$', rules_handler, name='api_rules'),
    url(r'^rules/(?P<id_rule>\d+)\.(?P<emitter_format>.+)$', rules_detail_handler, name='api_rules_detail'),
    url(r'^tags-(?P<id_rule>\d+)\.(?P<emitter_format>.+)$', tags_handler, name='api_tags'),
    url(r'^plugins\.(?P<emitter_format>.+)$', plugins_handler, name='api_plugins'),
    url(r'^mdt/$', mdt_handler, name='api_mdt'),
)

