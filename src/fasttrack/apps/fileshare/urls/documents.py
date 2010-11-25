from django.conf.urls.defaults import *

urlpatterns = patterns('fileshare.views',
     url(r'^get/(?P<document>\w+)$',
        'get_file_no_hash', name='get_file_no_hash_and_extension'),
    url(r'^get/(?P<document>\w+)\.(?P<extension>\w{3})$',
        'get_file_no_hash', name='get_file_no_hash'),
    url(r'^revision/(?P<document>\w+)$',
        'revision_document', name='revision_document'),
    url(r'^(?P<hashcode>\w+)/(?P<document>\w+)$',
        'get_file', name='get_file_no_extension'),
    url(r'^(?P<hashcode>\w+)/(?P<document>\w+)\.(?P<extension>\w{3})$',
        'get_file', name='get_file'),
)

