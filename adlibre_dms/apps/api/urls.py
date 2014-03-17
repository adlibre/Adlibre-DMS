"""
Module: DMS API Django URLs

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

from django.conf.urls import patterns, url
from api import views


urlpatterns = patterns(
    '',
    # Deprecated file handlers:
    # /api/file/ABC1234
    url(
        r'^file/(?P<code>[\w_-]+)$',
        views.OldFileHandler.as_view(),
        name='api_file_deprecated',
    ),
    # /api/file/ABC1234.pdf
    url(
        r'^file/(?P<code>[\w_-]+)\.(?P<suggested_format>[\w_-]+)$',
        views.OldFileHandler.as_view(),
        name='api_file_deprecated',
    ),

    # Working handlers:
    # /api/file/ABC1234
    url(
        r'^new_file/(?P<code>[\w_-]+)$',
        views.FileHandler.as_view(),
        name='api_file',
    ),
    # /api/file/ABC1234.pdf
    url(
        r'^new_file/(?P<code>[\w_-]+)\.(?P<suggested_format>[\w_-]+)$',
        views.FileHandler.as_view(),
        name='api_file',
    ),
    # /api/file-info/ABC1234
    url(
        r'^file-info/(?P<code>[\w_-]+)$',
        views.FileInfoHandler.as_view(),
        name='api_file_info',
    ),
    # /api/file-info/ABC1234.pdf
    url(
        r'^file-info/(?P<code>[\w_-]+)\.(?P<suggested_format>[\w_-]+)',
        views.FileInfoHandler.as_view(),
        name='api_file_info',
    ),
    url(
        r'^files/(?P<id_rule>\d+)/$',
        views.FileListHandler.as_view(),
        name='api_file_list',
    ),
    url(
        r'^revision_count/(?P<document>[\w_-]+)$',
        views.RevisionCountHandler.as_view(),
        name='api_revision_count',
    ),
    url(
        r'^rules.json$',
        views.RulesHandler.as_view(),
        name='api_rules',
    ),
    url(
        r'^rules/(?P<id_rule>\d+).json$',
        views.RulesDetailHandler.as_view(),
        name='api_rules_detail',
    ),
    url(
        r'^tags-(?P<id_rule>\d+)$',
        views.TagsHandler.as_view(),
        name='api_tags',
    ),
    url(
        r'^plugins.json$',
        views.PluginsHandler.as_view(),
        name='api_plugins'
    ),
    url(
        r'^mdt/$',
        views.MetaDataTemplateHandler.as_view(),
        name='api_mdt'
    ),
    url(
        r'^parallel/$',
        views.ParallelKeysHandler.as_view(),
        name='api_parallel',
    ),
    url(
        r'^thumbnail/(?P<code>[\w_-]+)$',
        views.ThumbnailsHandler.as_view(),
        name='api_thumbnail',
    ),
    url(
        r'^version$',
        views.VersionHandler.as_view(),
        name='api_version'
    ),
)

