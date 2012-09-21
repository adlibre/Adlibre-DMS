"""
Module: DMS Plugins DB connections module

Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2012
License: See LICENSE for license information
"""

from django.db import models
import logging

from djangoplugins.fields import PluginField, ManyPluginField
from djangoplugins.models import Plugin
from taggit.managers import TaggableManager

from dms_plugins import pluginpoints
from doc_codes.models import DocumentTypeRule

log = logging.getLogger('dms_plugins.models')

class DoccodePluginMapping(models.Model):
    doccode = models.ForeignKey(DocumentTypeRule)
    #if changing *_plugins names please change dms_plugins.pluginpoints correspondingly
    before_storage_plugins = ManyPluginField(   pluginpoints.BeforeStoragePluginPoint, 
                                                related_name = 'settings_before_storage',
                                                blank = True,
                                                verbose_name = "Pre-Storage Workflow")
    database_storage_plugins = ManyPluginField(   pluginpoints.DatabaseStoragePluginPoint,
                                                related_name = 'settings_database_storage',
                                                blank = True,
                                                verbose_name = "Database Storage Workflow")
    storage_plugins = ManyPluginField(   pluginpoints.StoragePluginPoint, 
                                                related_name = 'settings_storage',
                                                blank = True,
                                                verbose_name = "Storage Workflow")
    before_retrieval_plugins = ManyPluginField( pluginpoints.BeforeRetrievalPluginPoint, 
                                                related_name = 'settings_before_retrieval',
                                                blank = True,
                                                verbose_name = "Retrieval Workflow")
    before_removal_plugins = ManyPluginField( pluginpoints.BeforeRemovalPluginPoint, 
                                                related_name = 'settings_before_removal',
                                                blank = True,
                                                verbose_name = "Removal Workflow")
    before_update_plugins = ManyPluginField( pluginpoints.BeforeUpdatePluginPoint, 
                                                related_name = 'settings_before_update',
                                                blank = True,
                                                verbose_name = "Modification Workflow")
    active = models.BooleanField(default = False)

    def __unicode__(self):
        return unicode(self.get_name())

    def get_name(self):
        try:
            doccode_name = self.doccode.get_title()
        except (KeyError, AttributeError):
            doccode_name = 'No name given'
            pass
        return unicode(doccode_name)
    name = property(get_name)

    def get_docrule(self):
        return self.doccode

    def get_before_storage_plugins(self):
        """
        Method to get active 'before_storage_plugins' plugins for Doccode Plugin Mapping instance
        """
        return self.before_storage_plugins.all().order_by('index')

    def get_storage_plugins(self):
        """
        Method to get active 'storage_plugins' plugins for Doccode Plugin Mapping instance
        """
        return self.storage_plugins.all().order_by('index')

    def get_before_retrieval_plugins(self):
        """
        Method to get active 'before_retrieval_plugins' plugins for Doccode Plugin Mapping instance
        """
        return self.before_retrieval_plugins.all().order_by('index')

    def get_before_removal_plugins(self):
        """
        Method to get active 'before_removal_plugins' plugins for Doccode Plugin Mapping instance
        """
        return self.before_removal_plugins.all().order_by('index')

    def get_before_update_plugins(self):
        """
        Method to get active 'before_update_plugins' plugins for Doccode Plugin Mapping instance
        """
        return self.before_update_plugins.all().order_by('index')

    def get_database_storage_plugins(self):
        """
        Method to get active 'database_storage_plugins' plugins for Doccode Plugin Mapping instance
        """
        return self.database_storage_plugins.all().order_by('index')

class PluginOption(models.Model):
    pluginmapping = models.ForeignKey(DoccodePluginMapping)
    plugin = models.ForeignKey(Plugin)
    name = models.CharField(max_length = 64)
    value = models.TextField(default = '', blank = True)

    def __unicode__(self):
        return "%s: %s" % (self.name, self.value)

class DocTags(models.Model):
    """
        A model that represents Document for maintainig Tag relations.
    """
    name = models.CharField(max_length = 128)
    doccode = models.ForeignKey(DocumentTypeRule)
    tags = TaggableManager()

    class Meta:
        verbose_name = "Document > Tags mapping"
        verbose_name_plural = "Document > Tags mappings"

    def get_tag_list(self):
        return map(lambda x: x.name, self.tags.all())

    def __unicode__(self):
        return unicode(self.name)
