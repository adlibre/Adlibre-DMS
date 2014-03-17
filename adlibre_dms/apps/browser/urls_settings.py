"""
Module: DMS Browser Django Settings URLs

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

from django.conf.urls import patterns, url

urlpatterns = patterns('browser.views',
    url(r'^$', 'setting', name='setting'),
    url(r'^plugins$', 'plugins', name='plugins'),
    url(r'^(?P<rule_id>\d+)/$', 'edit_setting', name='edit_setting'),
    url(r'^state/(?P<rule_id>\d+)/$', 'toggle_rule_state', name='toggle_rule_state'),
    url(r'^(?P<rule_id>\d+)/conf/(?P<plugin_id>\d+)/$', 'plugin_setting', name='plugin_setting'),
)
