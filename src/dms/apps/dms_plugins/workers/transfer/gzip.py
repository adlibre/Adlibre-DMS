import zlib
import tempfile

from dms_plugins.pluginpoints import BeforeStoragePluginPoint, BeforeRetrievalPluginPoint
from dms_plugins.workers import Plugin, PluginError

class GzipOnStorePlugin(Plugin, BeforeStoragePluginPoint):
    title = 'Gzip Plugin'
    active = True
    has_configuration = True #TODO: configure

    def work(self, request, document):
        return Gzip.work_store(request, document)

class GzipOnRetrievePlugin(Plugin, BeforeRetrievalPluginPoint):
    title = 'Gzip Plugin'
    active = True
    has_configuration = True #TODO: configure

    def work(self, request, document):
        return Gzip.work_retrieve(request, document)

class Gzip(object):
    def _work(self, file_obj, method):
        file_obj.seek(0)
        content = file_obj.read()
        tmp_file_obj = tempfile.TemporaryFile()

        if method == 'STORAGE':
            tmp_file_obj.write(zlib.compress(content))
        elif method == 'RETRIEVAL':
            tmp_file_obj.write(zlib.decompress(content))
        return tmp_file_obj

    def work_store(self, request, document):
        compressed_file = self._work(document.get_file_obj(), method = 'STORAGE')
        document.set_compressed_file(compressed_file)
        return document

    def work_retrieve(self, request, document):
        compressed_file = self._work(document.get_file_obj(), method = 'RETRIEVAL')
        document.set_compressed_file(compressed_file)
        return document
