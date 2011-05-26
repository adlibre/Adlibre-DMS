from dms_plugins.workers import PluginError
from dms_plugins.pluginpoints import BeforeStoragePluginPoint, BeforeRetrievalPluginPoint

from document import Document
from base import models

class DocumentManager(object):
    def __init__(self):
        self.errors = []

    def get_plugin_mapping(self, document):
        mapping = models.DoccodePluginMapping.objects.filter(doccode = document.get_doccode().get_id())
        if mapping.count():
            mapping = mapping[0]
        else:
            mapping = None
        return mapping

    def get_plugins(self, pluginpoint, document):
        mapping = self.get_plugin_mapping(document)
        if mapping:
            plugin_objects = getattr(mapping, pluginpoint.settings_field_name).order_by('index')
            plugins = map(lambda plugin_obj: plugin_obj.get_plugin(), plugin_objects)
        else:
            plugins = []
        return plugins

    def process_pluginpoint(self, pluginpoint, request, document = None):
        plugins = self.get_plugins(pluginpoint, document)
        for plugin in plugins:
            try:
                document = plugin.work(request, document)
            except PluginError, e: # if some plugin throws an exception, stop processing and store the error message
                self.errors.append(str(e))
                break
        return document

    def store(self, request, uploaded_file):
        #process all storage plugins
        #uploaded file is http://docs.djangoproject.com/en/1.3/topics/http/file-uploads/#django.core.files.uploadedfile.UploadedFile
        doc = Document()
        doc.set_uploaded_file(uploaded_file)
        return self.process_pluginpoint(BeforeStoragePluginPoint, request, document = doc)

    def retrieve(self, request, document_id):
        doc = Document()
        doc.set_id(document_id)
        return self.process_pluginpoint(BeforeRetrievalPluginPoint, request, document = doc)


