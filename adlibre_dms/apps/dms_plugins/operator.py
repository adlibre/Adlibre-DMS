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
from core.errors import DmsException
from workers import PluginError, PluginWarning, BreakPluginChain
from workers.info.tags import TagsPlugin
from dms_plugins import pluginpoints
from core.models import DocumentTypeRule

log = logging.getLogger('dms')

# PEP method to fix out redundant imports.
__all__ = ['PluginsOperator']


class PluginsOperator(object):
    """
    Handles Plugin() Processing logic.

    Must execute plugins for certain minor tasks. (That are not CRUD)
    e.g. PluginsOperator().rename_file(old_filename, new_filename)
    """
    # TODO: All plugin executions must be decoupled and optional,
    # so you can remove any plugin and it will not affect entire system.
    def __init__(self):
        self.plugin_errors = []
        self.plugin_warnings = []

    def process_pluginpoint(self, pluginpoint, document=None):
        """
        PluginsOperator() main gear.

        Iterates over plugins and executes them according to config and workflow specified (PluginPoint)

        @param pluginpoint: a special DMS internal set of plugins to be executed
        @param document: DMS Document() instance
        """
        plugins = self.get_plugins_for_point(pluginpoint, document)
        #log.debug('process_pluginpoint: %s with %s plugins.' % (pluginpoint, plugins))
        for plugin in plugins:
            try:
                # log.debug('process_pluginpoint begin processing: %s.' % plugin)
                document = plugin.work(document)
                # log.debug('process_pluginpoint begin processed: %s.' % plugin)
            except PluginError, e:  # if some plugin throws an exception, stop processing and store the error message
                self.plugin_errors.append(e)
                if settings.DEBUG:
                    log.error('process_pluginpoint: %s.' % e)  # e.parameter, e.code
                break
            except PluginWarning, e:
                self.plugin_warnings.append(str(e))
            except BreakPluginChain:
                break
        return document

    def get_plugins_from_mapping(self, mapping, pluginpoint, plugin_type):
        """Extracts and instantiates Plugin() objects from given plugin mapping.

        @param mapping: DocumentTYpeRulePluginMapping() instance"""
        plugin_objects = getattr(mapping, 'get_' + pluginpoint.settings_field_name)()
        plugins = map(lambda plugin_obj: plugin_obj.get_plugin(), plugin_objects)
        if plugin_type:
            plugins = filter(
                lambda plugin: hasattr(plugin, 'plugin_type') and plugin.plugin_type == plugin_type, plugins
            )
        return plugins

    def get_plugin_list(self):
        """Gets a list of all installed into DMS plugins."""
        all_plugins = djangoplugins.models.Plugin.objects.all().order_by('point__name', 'index')
        return all_plugins

    def get_plugins_for_point(self, pluginpoint, document, plugin_type=None):
        """Retrieves Plugins for given Pluginpoint."""
        # update sequence should use old docrule and iterate through plugins, instead of new one
        if document.old_docrule:
            docrule = document.old_docrule
        else:
            docrule = document.get_docrule()
        # FIXME: with current architecture there might be more than one docrule mappings.
        mapping = docrule.get_docrule_plugin_mappings()
        if mapping:
            plugins = self.get_plugins_from_mapping(mapping, pluginpoint, plugin_type)
        else:
            plugins = []
        return plugins

    def get_plugin_mapping_by_docrule_id(self, pk):
        mapping = DoccodePluginMapping.objects.filter(doccode__pk=int(pk), doccode__active=True)
        if not mapping.exists():
            raise DmsException('Rule not found', 404)
        return mapping[0]

    # TODO:
    # Some unusual magic with processing plugins...
    #
    # I think they must be part of the retrieve workflow with some options set.
    # We should not touch those methods directly. IT creates a mess.
    # e.g. DocumentProcessor().read(document, option='revision_count')

    def get_file_list(self, doccode_plugin_mapping, start=0, finish=None, order=None, searchword=None,
                      tags=None, filter_date=None):
        """This must be a part of some retrieve workflow
        e.g. DocumentProcessor().read(document, option='get_file_list')"""
        # TODO: refactor this to a retrieval workflow with certain option.
        # Proper tags init according to PEP
        if not tags:
            tags = []
        metadata = None
        pluginpoint=pluginpoints.StoragePluginPoint
        metadatas = self.get_plugins_from_mapping(doccode_plugin_mapping, pluginpoint, plugin_type='metadata')
        if metadatas:
            metadata = metadatas[0]
        pluginpoint = pluginpoints.StoragePluginPoint
        # Plugin point does not matter here as mapping must have a storage plugin both at storage and retrieval stages
        storage = self.get_plugins_from_mapping(doccode_plugin_mapping, pluginpoint, plugin_type='storage')
        # Document MUST have a storage plugin
        if not storage:
            raise ConfigurationError("No storage plugin for %s" % doccode_plugin_mapping)
        # Should we validate more than one storage plugin?
        # FIXME: document should be able to work with several storage plugins.
        storage = storage[0]
        docrule = doccode_plugin_mapping.get_docrule()
        doc_models = TagsPlugin().get_doc_models(docrule=doccode_plugin_mapping.get_docrule(), tags=tags)
        doc_names = map(lambda x: x.name, doc_models)
        if metadata:
            document_directories = metadata.worker.get_directories(docrule, filter_date=filter_date)
        else:
            document_directories = []
        return storage.worker.get_list(docrule, document_directories, start, finish, order, searchword,
            limit_to=doc_names)
