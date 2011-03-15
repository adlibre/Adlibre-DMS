from django.conf import settings
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^api/', include('api.urls')),
    url(r'^settings/', include('fileshare.urls.settings')),
    url(r'^docs/', include('fileshare.urls.documentation')),
    url(r'^upload/$', 'fileshare.views.upload', name='upload'),
    (r'^$', 'fileshare.views.index'),
    
    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT }),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login', name='logout'),

    # robots
    (r'^robots.txt$', 'django.views.generic.simple.direct_to_template', {'template': 'robots.txt', 'mimetype' : 'text/plain'}),

    # favicon
    ('^favicon.ico$', 'django.views.generic.simple.redirect_to', {'url': settings.MEDIA_URL+'favicon.ico'}),

    # This needs to be last
    (r'^', include('fileshare.urls.documents')),
)

