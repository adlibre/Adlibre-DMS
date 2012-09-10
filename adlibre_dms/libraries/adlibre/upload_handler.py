"""
http://djangosnippets.org/snippets/678/

Upload progress handler using cache framework

Setup: place the UploadProgressCachedHandler anywhere you like on the python path, and add to your settings.py:

from django.conf import global_settings
FILE_UPLOAD_HANDLERS = ('path.to.UploadProgressCachedHandler', ) + global_settings.FILE_UPLOAD_HANDLERS

Set up the upload_progress view in any of your apps along with a corresponding entry in your urlconf.

Here's some javascript example code to make the ajax requests and display the progress meter: http://www.djangosnippets.org/snippets/679/
"""


from django.core.files.uploadhandler import MemoryFileUploadHandler

class UploadProgressCachedHandler(MemoryFileUploadHandler):
    """
    Tracks progress for file uploads.
    The http post request must contain a header or query parameter, 'X-Progress-ID'
    which should contain a unique string to identify the upload to be tracked.

    Uses django.sessions framework instead of memcache or similar cache based decisions @garmoncheg
    """

    def __init__(self, request=None):
        super(UploadProgressCachedHandler, self).__init__(request)
        self.progress_id = None
        self.cache_key = None

    def handle_raw_input(self, input_data, META, content_length, boundary, encoding=None):
        self.content_length = content_length
        if 'X-Progress-ID' in self.request.GET :
            self.progress_id = self.request.GET['X-Progress-ID']
        elif 'X-Progress-ID' in self.request.META:
            self.progress_id = self.request.META['X-Progress-ID']
        if self.progress_id:
            self.cache_key = "%s_%s" % (self.request.META['REMOTE_ADDR'], self.progress_id )
            self.request.session[self.cache_key] = {
                'length': self.content_length,
                'uploaded' : 0
            }

    def new_file(self, field_name, file_name, content_type, content_length, charset=None):
        pass

    def receive_data_chunk(self, raw_data, start):
        if self.cache_key:
            data = self.request.session[self.cache_key]
            data['uploaded'] += self.chunk_size
            self.request.session[self.cache_key] = data
        return raw_data

    def file_complete(self, file_size):
        pass

    def upload_complete(self):
        if self.cache_key:
            del self.request.session[self.cache_key]

