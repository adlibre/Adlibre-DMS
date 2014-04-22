from django.conf import settings
from django.conf.urls import patterns, include, url
from django.views.generic import TemplateView, RedirectView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

# Custom 500 with MEDIA_URL context
handler500 = 'adlibre_dms.views.server_error'

urlpatterns = []

if settings.DEBUG:
    urlpatterns += patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
        url(r'^500/$', 'adlibre_dms.views.server_error'),
    )

urlpatterns += patterns('',
    url(r'^api/', include('api.urls')),
    url(r'^settings/', include('browser.urls_settings')),
    url(r'^docs/', include('docs.urls')),
    url(r'^admin/', include('django-log-file-viewer.admin_urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login', name='logout'),

    # Robots
    url(r'^robots.txt$', TemplateView.as_view(template_name='robots.txt', content_type='text/plain')),
    # Favicon
    url(r'^favicon.ico$', RedirectView.as_view(url=settings.STATIC_URL+'favicon.ico')),

    # Independent DMS Apps
    url(r'^mdtui/', include('mdtui.urls')),
    url(r'^bcp/', include('bcp.urls')),
    url(r'^user/', include('adlibre.auth.urls')),
    url(r'^feedback/', include('feedback.urls')),

    # This needs to be last
    url(r'', include('browser.urls')),
)

