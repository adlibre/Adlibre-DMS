import zlib
import tempfile

from dms_plugins.pluginpoints import BeforeStoragePluginPoint, BeforeRetrievalPluginPoint
from dms_plugins.workers import Plugin, PluginError

class GzipOnStorePlugin(Plugin, BeforeStoragePluginPoint):
    title = 'Gzip Plugin'
    has_configuration = True #TODO: configure

    def work(self, request, document):
        return Gzip().work_store(request, document)

class GzipOnRetrievePlugin(Plugin, BeforeRetrievalPluginPoint):
    title = 'Gzip Plugin'
    has_configuration = True #TODO: configure

    def work(self, request, document):
        return Gzip().work_retrieve(request, document)

class Gzip(object):
    compression_type = 'GZIP'
    def _work(self, file_obj, method):
        file_obj.seek(0)
        tmp_file_obj = tempfile.TemporaryFile()
        if method == 'STORAGE':
            compressed_file = zlib.compress(file_obj.read())
            tmp_file_obj.write(compressed_file)
            tmp_file_obj.seek(0)
            print "FILE SIZE: %s bytes" % len(compressed_file)
        elif method == 'RETRIEVAL':
            content = file_obj.read()
            before = len(content)
            decompressed = zlib.decompress(content)
            after = len(decompressed)
            tmp_file_obj.write(decompressed)
            tmp_file_obj.seek(0)
        return tmp_file_obj

    def work_store(self, request, document):
        compressed_file = self._work(document.get_file_obj(), method = 'STORAGE')
        document.set_file_obj(compressed_file)
        document.update_current_metadata({'compression_type': self.compression_type})
        return document

    def work_retrieve(self, request, document):
        if document.get_current_metadata().get('compression_type', None) == self.compression_type:
            try:
                decompressed_file = self._work(document.get_file_obj(), method = 'RETRIEVAL')
            except:
                raise
                #raise PluginError("Couln't decompress file: was it compressed when stored?")
            document.set_file_obj(decompressed_file)
            document.decompressed_file = decompressed_file
        return document
