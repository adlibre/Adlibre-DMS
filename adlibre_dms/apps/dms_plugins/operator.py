"""
Module: DMS Plugins running logic handler.

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
Author: Iurii Garmash
"""

import logging
import djangoplugins

from django.conf import settings

from core.errors import ConfigurationError
from models import DoccodePluginMapping
from workers import DmsException
from workers import PluginError, PluginWarning, BreakPluginChain
from workers.info.tags import TagsPlugin
from dms_plugins import pluginpoints

from core.models import Document

log = logging.getLogger('dms_plugins.operator')

# PEP method to fix out redundant imports.
__all__ = ['PluginsOperator']

class PluginsOperator(object):
    """
    Handles Plugin() Processing logic.

    Must execute plugins for certain tasks.
    """
    # TODO: All plugin executions must be decoupled and optional, so you can remove any plugin and it will not affect entire system.
    def __init__(self):
        self.plugin_errors = []
        self.plugin_warnings = []

    def process_pluginpoint(self, pluginpoint, request, document=None):
        plugins = self.get_plugins_for_point(pluginpoint, document)
        log.debug('process_pluginpoint: %s with %s plugins.' % (pluginpoint, plugins))
        for plugin in plugins:
            try:
                log.debug('process_pluginpoint begin processing: %s.' % plugin)
                document = plugin.work(request, document)
                log.debug('process_pluginpoint begin processed: %s.' % plugin)
            except PluginError, e: # if some plugin throws an exception, stop processing and store the error message
                self.plugin_errors.append(e)
                if settings.DEBUG:
                    log.error('process_pluginpoint: %s.' % e) # e.parameter, e.code
                break
            except PluginWarning, e:
                self.plugin_warnings.append(str(e))
            except BreakPluginChain:
                break
        return document

    def get_plugins_from_mapping(self, mapping, pluginpoint, plugin_type):
        """
        Extracts and instantiates Plugin() objects from given plugin mapping.
        """
        plugins = []
        plugin_objects = getattr(mapping, 'get_' + pluginpoint.settings_field_name)()
        plugins = map(lambda plugin_obj: plugin_obj.get_plugin(), plugin_objects)
        if plugin_type:
            plugins = filter(lambda plugin: hasattr(plugin, 'plugin_type') and plugin.plugin_type == plugin_type, plugins)
        return plugins

    def get_plugin_list(self):
        all_plugins = djangoplugins.models.Plugin.objects.all().order_by('point__name', 'index')
        return all_plugins

    def get_plugins_for_point(self, pluginpoint, document, plugin_type=None):
        """
        Retrieves Plugins for given Pluginpoint.
        """
        docrule = document.get_docrule()
        # FIXME: with current architecture there might be more than one docrule mappings.
        mapping = docrule.get_docrule_plugin_mappings()
        if mapping:
            plugins = self.get_plugins_from_mapping(mapping, pluginpoint, plugin_type)
        else:
            plugins = []
        return plugins

    # FIXME: Maybe it should be some kind of DoccodePluginMapping manager or similar.
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

    def get_revisions_metadata(self, doccode_plugin_mapping):
        metadata = None
        pluginpoint=pluginpoints.StoragePluginPoint
        metadatas = self.get_plugins_from_mapping(doccode_plugin_mapping, pluginpoint, plugin_type='metadata')
        if metadatas:
            metadata = metadatas[0]
        return metadata

    """
    Some unusual magic with processing plugins...

    I think they must be part of the retrieve workflow with some options set.
    We should not touch those methods directly. IT creates a mess.
    e.g. DocumentProcessor().read(document, option='revision_count')
    """
    # TODO: make this part of retrieve workflow (like 'only_metadata' option)
    def get_revision_count(self, document_name, doccode_plugin_mapping):
        """
        Refactor ME to make part of read workflow...
        """
        storage = self.get_storage(doccode_plugin_mapping)
        doc = Document()
        doc.set_filename(document_name)
        return storage.worker.get_revision_count(doc)

    def get_storage(self, doccode_plugin_mapping):
        """
        Maybe it is a part of read workflow to???
        """
        pluginpoint = pluginpoints.StoragePluginPoint
        # Plugin point does not matter here as mapping must have a storage plugin both at storage and retrieval stages
        storage = self.get_plugins_from_mapping(doccode_plugin_mapping, pluginpoint, plugin_type='storage')
        # Document MUST have a storage plugin
        if not storage:
            raise ConfigurationError("No storage plugin for %s" % doccode_plugin_mapping)
        # Should we validate more than one storage plugin?
        # FIXME: document should be able to work with several storage plugins.
        return storage[0]