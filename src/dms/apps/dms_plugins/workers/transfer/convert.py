from adlibre.converter import NewFileConverter

from dms_plugins.pluginpoints import BeforeStoragePluginPoint, BeforeRetrievalPluginPoint
from dms_plugins.workers import Plugin, PluginError, DmsException

class ConvertFileTypePlugin(Plugin, BeforeRetrievalPluginPoint):
    title = "File Type Converter"

    def work(self, request, document):
        return Converter().work_retrieve(request, document)

class Converter(object):
    def work_retrieve(self, request, document):
        to_extension = document.get_option('convert_to_extension')
        if to_extension:
            converter = NewFileConverter(document.get_file_obj(), document.get_fullpath(), to_extension)
            mimetype, new_file_obj = converter.convert()
            document.set_mimetype(mimetype)
            document.set_file_obj(new_file_obj)
        return document


