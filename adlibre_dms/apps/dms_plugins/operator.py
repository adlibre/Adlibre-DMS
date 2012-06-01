"""
Module: DMS Plugins running logic handler.

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
"""

import logging
from models import DoccodePluginMapping
from workers import DmsException
from workers.info.tags import TagsPlugin

log = logging.getLogger('dms_plugins.operator')

class PluginsOperator(object):
    def __init__(self):
        # FIXME: Dummy init (unused for now)
        self.plugins = None

    def get_plugins_from_mapping(self, mapping, pluginpoint, plugin_type):
        """
        Extracts and instantiates plugins from given plugin mapping.
        """
        plugins = []
        plugin_objects = getattr(mapping, 'get_' + pluginpoint.settings_field_name)()
        plugins = map(lambda plugin_obj: plugin_obj.get_plugin(), plugin_objects)
        if plugin_type:
            plugins = filter(lambda plugin: hasattr(plugin, 'plugin_type') and plugin.plugin_type == plugin_type, plugins)
        return plugins

    # Maybe it should be some kind of DoccodePluginMapping manager or similar.
    def get_plugin_mapping_by_id(self, pk):
        try:
            mapping = DoccodePluginMapping.objects.get(pk=int(pk))
        except mapping.DoesNotExist:
            raise DmsException('Rule not found', 404)
        return mapping

    # TODO: Convert it into workflow. Do not use Plugin() directly. WRONG!
    # Maybe MAKE some Tags() Manager to handle it's logic with own pluginpoints etc...
    def get_all_tags(self, doccode=None):
        return TagsPlugin().get_all_tags(doccode = doccode)
