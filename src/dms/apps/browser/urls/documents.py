from django.conf.urls.defaults import *

# TODO: Are these regexes optimal?

# DECISION: Need to make adding ruleid option to request url
# eg /get/{ruleid}/MYDOC.pdf

urlpatterns = patterns('browser.views',
     url(r'^get/(?P<document>[\w_-]+)$',
        'get_file', name='get_file_no_hash_and_extension'),
    url(r'^get/(?P<document>[\w_-]+)\.(?P<extension>\w{3})$',
        'get_file', name='get_file_no_hash'),
    url(r'^files/$',
        'files_index', name='files_index'),
    url(r'^files/(?P<id_rule>\d+)/$',
        'files_document', name='files_document'),
    url(r'^revision/(?P<document>[\w_-]+)$',
        'revision_document', name='revision_document'),
    url(r'^(?P<hashcode>\w+)/(?P<document>[\w_-]+)$',
        'get_file', name='get_file_no_extension'),
    url(r'^(?P<hashcode>\w+)/(?P<document>[\w_-]+)\.(?P<extension>\w{3})$',
        'get_file', name='get_file'),
)

# /files/code/