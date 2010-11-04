from django.conf import settings
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^fasttrack/', include('fasttrack.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^settings/', include('fileshare.urls')),
    (r'^$', 'fileshare.views.index'),
    url(r'^get/(?P<document>\w+)\.(?P<extension>\w{3})$', 'fileshare.views.get_file_no_hash', name='get_file_no_hash'),
    url(r'^(?P<hashcode>\w+)/(?P<document>\w+)\.(?P<extension>\w{3})$', 'fileshare.views.get_file', name='get_file'),
    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT }),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login', name='logout')
)

