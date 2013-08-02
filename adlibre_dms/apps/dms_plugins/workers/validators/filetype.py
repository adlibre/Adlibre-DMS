"""
Module: File Type Plugin
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2013
License: See LICENSE for license information
"""

from dms_plugins.pluginpoints import BeforeStoragePluginPoint
from dms_plugins.workers import Plugin, PluginError


class FileTypeValidationPlugin(Plugin, BeforeStoragePluginPoint):
    title = "File Type Validator"
    description = "Validates document type against supported types"
    plugin_type = "storage_validation"

    def work(self, document):
        """Main method to validate a MIME type of a file

        @param document: DMS Document() instance"""
        if document.get_file_obj():
            typ = document.get_mimetype()
            if not typ in self.get_mime_types():
                raise PluginError('File type %s is not supported' % typ, 500)
            document.set_mimetype(typ)
        return document

    def get_mime_types(self):
        """Method to return all the file MIME types DMS supports"""
        MIMETYPES = [
            ("application/pdf", 'pdf'),
            ('image/tiff', 'tiff'),
            ('image/jpeg', 'jpg'),
            ('image/gif', 'gif'),
            ('image/png', 'png'),
            ('text/plain', 'txt'),
            ('text/x-c', 'txt'),  # In fact is a txt file type
            ('text/x-c++', 'txt'),  # In fact is a txt file type
            ('application/msword', 'doc'),
            ('application/vnd.ms-excel', 'xls'),
        ]
        return [x[0] for x in MIMETYPES]
