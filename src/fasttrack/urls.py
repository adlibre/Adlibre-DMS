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
    url(r'^setting/', include('fileshare.urls')),
    (r'^$', 'fileshare.views.index'),
    url(r'^(?P<hashcode>\w+)/(?P<filename>.*)$', 'fileshare.views.get_file', name="get_file"),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
)

