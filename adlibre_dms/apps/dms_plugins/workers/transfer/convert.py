from adlibre.converter import NewFileConverter

from dms_plugins.pluginpoints import BeforeRetrievalPluginPoint
from dms_plugins.workers import Plugin

class ConvertFileTypePlugin(Plugin, BeforeRetrievalPluginPoint):
    title = "File Type Converter"
    description = "Converts file types"
    plugin_type = "retrieval_processing"

    def work(self, document):
        return Converter().work_retrieve(document)

class Converter(object):
    def work_retrieve(self, document):
        to_extension = document.get_requested_extension()
        if to_extension:
            converter = NewFileConverter(document.get_file_obj(), document.get_fullpath(), to_extension)
            mimetype, new_file_obj = converter.convert()
            document.set_mimetype(mimetype)
            document.set_file_obj(new_file_obj)
        return document


