from dms_plugins.workers import PluginError, PluginWarning, BreakPluginChain
from dms_plugins.pluginpoints import BeforeStoragePluginPoint, BeforeRetrievalPluginPoint

from document import Document
from base import models

class ConfigurationError(Exception):
    pass

class DocumentManager(object):
    def __init__(self):
        self.errors = []
        self.warnings = []

    def get_plugin_mapping(self, document):
        mapping = models.DoccodePluginMapping.objects.filter(doccode = document.get_doccode().get_id())
        if mapping.count():
            mapping = mapping[0]
        else:
            mapping = None
        return mapping

    def get_plugins_from_mapping(self, mapping, pluginpoint, plugin_type):
        plugins = []
        plugin_objects = getattr(mapping, pluginpoint.settings_field_name).order_by('index')
        plugins = map(lambda plugin_obj: plugin_obj.get_plugin(), plugin_objects)
        if plugin_type:
            plugins = filter(lambda plugin: hasattr(plugin, 'plugin_type') and plugin.plugin_type == plugin_type, plugins)
        return plugins

    def get_plugins(self, pluginpoint, document, plugin_type = None):
        mapping = self.get_plugin_mapping(document)
        if mapping:
            plugins = self.get_plugins_from_mapping(mapping, pluginpoint, plugin_type)
        else:
            plugins = []
        return plugins

    def process_pluginpoint(self, pluginpoint, request, document = None):
        plugins = self.get_plugins(pluginpoint, document)
        print 'plugins: %s' % plugins
        for plugin in plugins:
            try:
                document = plugin.work(request, document)
                print "Processed %s: Here is document: \n%s" % (plugin, document)
            except PluginError, e: # if some plugin throws an exception, stop processing and store the error message
                self.errors.append(str(e))
                break
            except PluginWarning, e:
                self.warnings.append(str(e))
            except BreakPluginChain:
                break
        return document

    def store(self, request, uploaded_file):
        #process all storage plugins
        #uploaded file is http://docs.djangoproject.com/en/1.3/topics/http/file-uploads/#django.core.files.uploadedfile.UploadedFile
        doc = Document()
        doc.set_file_obj(uploaded_file)
        doc.set_filename(uploaded_file.name)
        doc.set_mimetype(uploaded_file.content_type)
        return self.process_pluginpoint(BeforeStoragePluginPoint, request, document = doc)

    def retrieve(self, request, document_name, hashcode = None, revision = None, only_metadata = False, extension = None):
        """
            retrieve_only tells system that it should ignore all plugins AFTER storage 
            plugin has retrieved file. This is necessary to prevent needless work like 
            compression etc in case we only need metadata.
        """
        doc = Document()
        doc.set_filename(document_name)
        doc.set_hashcode(hashcode)
        doc.set_revision(revision)
        options = {'only_metadata': only_metadata}
        if extension:
            options['convert_to_extension'] = extension
        doc.update_options(options)
        return self.process_pluginpoint(BeforeRetrievalPluginPoint, request, document = doc)

    def get_storage(self, doccode_plugin_mapping, pluginpoint = BeforeStoragePluginPoint):
        #Plugin point does not matter here as mapping must have a storage plugin both at storage and retrieval stages
        storage = self.get_plugins_from_mapping(doccode_plugin_mapping, pluginpoint, plugin_type = 'storage')
        #Document MUST have a storage plugin
        if not storage:
            raise ConfigurationError("No storage plugin for %s" % doccode_plugin_mapping)
        #Should we validate more than one storage plugin?
        return storage[0]

    def get_file_list(self, doccode_plugin_mapping):
        storage = self.get_storage(doccode_plugin_mapping)
        return storage.worker.get_list(doccode_plugin_mapping.get_doccode())

