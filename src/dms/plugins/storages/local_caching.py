"""
Module: Local Storage + Caching Example Plugin
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

from django.conf import settings

from storages.local import Local

# This is how we implement caching
# we create a storage plugin, that provides
# caching for the access methods

# TODO: Make this actually cache :)

class LocalCaching(Local):
    
    name = "Caching Local Storage"
    description = "Local storage plugin with caching"


    def store(self, filename, root=settings.DOCUMENT_ROOT):
        return super(LocalCaching, self).store(filename, root)


    def retrieve(self, filename, revision=None, root=settings.DOCUMENT_ROOT):
        return super(LocalCaching, self).retrieve(filename, revision, root)


    def delete(self, filename, revision=None, root=settings.DOCUMENT_ROOT):
        return super(LocalCaching, self).delete(filename, revision, root)


    def get_meta_data(self, document, root=settings.DOCUMENT_ROOT):
        return super(LocalCaching, self).get_meta_data(document, root)


    def get_revision_count(self, document, root=settings.DOCUMENT_ROOT):
        return super(LocalCaching, self).get_revision_count(document, root)


    def get_list(self, id_rule, root=settings.DOCUMENT_ROOT):
        return super(LocalCaching, self).get_list(id_rule, root)
