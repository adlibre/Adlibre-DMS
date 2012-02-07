from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
from django.views.generic.simple import redirect_to

import mdtui.views

urlpatterns = patterns('mdtui.views',
    url(r'^retrieve/(?P<step>[\-\d\w]+)$', 'retrieve', name='retrieve'),
    url(r'^upload/(?P<step>[\-\d\w]+)$', 'upload', name='upload'),

)