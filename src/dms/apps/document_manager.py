from dms_plugins.workers import PluginError
from dms_plugins.pluginpoints import BeforeStoragePluginPoint, BeforeRetrievalPluginPoint

from document import Document

class DocumentManager(object):
    def __init__(self):
        self.errors = []

    def get_plugins(self, pluginpoint, document):
        return pluginpoint.get_plugins() #TODO: filter plugins according to document doccode

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
        return self.process_pluginpoint(BeforeStoragePluginPoint, request, document = doc)


