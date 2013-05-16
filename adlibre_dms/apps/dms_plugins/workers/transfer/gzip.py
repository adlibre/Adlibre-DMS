"""
Module: Compression Plugin
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
"""

import zlib
import tempfile

from dms_plugins.pluginpoints import BeforeStoragePluginPoint, BeforeRetrievalPluginPoint, BeforeUpdatePluginPoint
from dms_plugins.workers import Plugin


class GzipOnStorePlugin(Plugin, BeforeStoragePluginPoint):
    title = 'Gzip Plugin on storage'
    has_configuration = True  # TODO: configure
    description = "Compresses files before storing"
    plugin_type = "storage_processing"

    def work(self, document):
        return Gzip().work_store(document)


class GzipOnUpdatePlugin(Plugin, BeforeUpdatePluginPoint):
    title = 'Gzip Plugin on update'
    has_configuration = True  # TODO: configure
    description = "Compresses files on updating file"
    plugin_type = "update_processing"

    def work(self, document):
        return Gzip().work_store(document)


class GzipOnRetrievePlugin(Plugin, BeforeRetrievalPluginPoint):
    title = 'Gzip Plugin on retrieval'
    has_configuration = True  # TODO: configure
    description = "Decompresses files on retrieval"
    plugin_type = "retrieval_processing"

    def work(self, document):
        return Gzip().work_retrieve(document)


class Gzip(object):
    compression_type = 'GZIP'

    def _work(self, file_obj, method):
        file_obj.seek(0)
        tmp_file_obj = tempfile.TemporaryFile()
        if method == 'STORAGE':
            compressed_file = zlib.compress(file_obj.read())
            tmp_file_obj.write(compressed_file)
            tmp_file_obj.seek(0)
        elif method == 'RETRIEVAL':
            content = file_obj.read()
            before = len(content)
            decompressed = zlib.decompress(content)
            after = len(decompressed)
            tmp_file_obj.write(decompressed)
            tmp_file_obj.seek(0)
        return tmp_file_obj

    def work_store(self, document):
        # Doing nothing for rename/change docrule for document
        if document.old_docrule:
            return document
        if document.get_file_obj():
            compressed_file = self._work(document.get_file_obj(), method='STORAGE')
            document.set_file_obj(compressed_file)
            document.update_current_file_revision_data({'compression_type': self.compression_type})
        return document

    def work_retrieve(self, document):
        # Doing nothing for only_metadata option
        if document.get_option('only_metadata'):
            return document
        if document.get_current_file_revision_data().get('compression_type', None) == self.compression_type:
            try:
                decompressed_file = self._work(document.get_file_obj(), method='RETRIEVAL')
            except:
                raise
                #raise PluginError("Couldn't decompress file: was it compressed when stored?")
            document.set_file_obj(decompressed_file)
            document.decompressed_file = decompressed_file
        return document
