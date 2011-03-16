from django.conf.urls.defaults import *
from piston.resource import Resource
from handlers import FileHandler, FileListHandler, RulesHandler, PluginsHandler, RulesDetailHandler

file_handler = Resource(FileHandler)
file_list_handler = Resource(FileListHandler)
rules_handler = Resource(RulesHandler)
plugins_handler = Resource(PluginsHandler)

urlpatterns = patterns('',
   url(r'^file/', file_handler),
   url(r'^files/(?P<id_rule>\d+)/$', file_list_handler),
   url(r'^rules\.(?P<emitter_format>.+)$', rules_handler),
   url(r'^rules/(?P<id_rule>\d+)\.(?P<emitter_format>.+)$', Resource(RulesDetailHandler)),
   url(r'^plugins\.(?P<emitter_format>.+)$', plugins_handler),
)

