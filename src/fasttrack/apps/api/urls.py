from django.conf.urls.defaults import *
from piston.resource import Resource
from handlers import FileHandler

file_handler = Resource(FileHandler)

urlpatterns = patterns('',
   url(r'^file/', file_handler),
)

