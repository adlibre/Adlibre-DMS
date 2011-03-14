from django.conf.urls.defaults import *


urlpatterns = patterns('fileshare.views',
     url(r'^$', 'documentation_index', name='documentation_index'),
     url(r'^api/$', 'api_documentation', name='api_documentation'),
     url(r'^technical/$', 'technical_documentation', name='technical_documentation'),
)
