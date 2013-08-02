import magic

from dms_plugins.pluginpoints import BeforeStoragePluginPoint
from dms_plugins.workers import Plugin, PluginError

MIMETYPES = [
                ('application/pdf', 'pdf'),
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

def get_mimetypes():
    return [x[0] for x in MIMETYPES]

class FileTypeValidationPlugin(Plugin, BeforeStoragePluginPoint):
    title = "File Type Validator"
    description = "Validates document type against supported types"
    plugin_type = "storage_validation"

    mimetypes = get_mimetypes()

    def work(self, document, **kwargs):
        if document.get_file_obj():
            # Commented to support 0 revisions doc storage
            # filebuffer = document.get_file_obj()
            # if filebuffer is None:
            #     raise PluginError('File buffer not initialized', 500)
            # TODO: FIXME: This does not actually validate the mimetype! filebuffer is not actually used!
            #mime = magic.Magic( mime = True )
            #content = ''
            #for line in filebuffer:
            #    content += line
            #typ = mime.from_buffer( content )
            typ = document.get_mimetype()
            if not typ in self.mimetypes:
                raise PluginError('File type %s is not supported' % typ, 500)
            document.set_mimetype(typ)
        return document
