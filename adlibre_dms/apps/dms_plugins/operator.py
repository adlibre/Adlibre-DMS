"""
Module: DMS Plugins running logic handler.

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
"""

import logging

log = logging.getLogger('dms_plugins.operator')

class PluginsOperator(object):
    def __init__(self):
        # FIXME: Dummy init (unused fro now)
        self.plugins = None

    def get_plugins_from_mapping(self, mapping, pluginpoint, plugin_type):
        plugins = []
        plugin_objects = getattr(mapping, 'get_' + pluginpoint.settings_field_name)()
        plugins = map(lambda plugin_obj: plugin_obj.get_plugin(), plugin_objects)
        if plugin_type:
            plugins = filter(lambda plugin: hasattr(plugin, 'plugin_type') and plugin.plugin_type == plugin_type, plugins)
        return plugins
