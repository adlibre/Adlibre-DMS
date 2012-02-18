"""
Module: DMS Plugins DB connections module
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

from django.db import models

"""
New models
"""
from plugins.fields import PluginField, ManyPluginField
from plugins.models import Plugin
from taggit.managers import TaggableManager

from dms_plugins import pluginpoints
from doc_codes.models import DocumentTypeRuleManagerInstance
from doc_codes.models import DocumentTypeRule

try:
    DOCRULE_CHOICES = map(lambda doccode: (str(doccode.doccode_id), doccode.title), DocumentTypeRule.objects.all())
except:
    # HACK: syncdb or no initial DocumentTypeRule exists...
    DOCRULE_CHOICES = [('1000', 'No Doccode'),]
    pass

class DoccodePluginMapping(models.Model):
    doccode = models.CharField(choices = DOCRULE_CHOICES, max_length = 64)
    #if changing *_plugins names please change dms_plugins.pluginpoints correspondingly
    before_storage_plugins = ManyPluginField(   pluginpoints.BeforeStoragePluginPoint, 
                                                related_name = 'settings_before_storage',
                                                blank = True,
                                                verbose_name = "Pre-Storage Workflow")
    database_storage_plugins = ManyPluginField(   pluginpoints.DatabaseStoragePluginPoint,
                                                related_name = 'settings_database_storage',
                                                blank = True,
                                                verbose_name = "Storage Workflow")
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
        return self.get_name()

    def get_name(self):
        doccode_name = "No name given"
        try:
            doccode_name = DocumentTypeRule.objects.get(doccode_id=self.doccode).title
        except (KeyError, AttributeError):
            pass
        return unicode(doccode_name)
    name = property(get_name)

    def get_docrule(self):
        docrules = DocumentTypeRuleManagerInstance.get_docrules()
        try:
            docrule = docrules[int(self.doccode)]
        except:
            docrule = docrules.filter(doccode_id=self.doccode)[0]
        return docrule

    def get_before_storage_plugins(self):
        return self.before_storage_plugins.all().order_by('index')

    def get_storage_plugins(self):
        return self.storage_plugins.all().order_by('index')

    def get_before_retrieval_plugins(self):
        return self.before_retrieval_plugins.all().order_by('index')

    def get_before_removal_plugins(self):
        return self.before_removal_plugins.all().order_by('index')

    def get_before_update_plugins(self):
        return self.before_update_plugins.all().order_by('index')

    def get_database_storage_plugins(self):
        return self.database_storage_plugins.all().order_by('index')

class PluginOption(models.Model):
    pluginmapping = models.ForeignKey(DoccodePluginMapping)
    plugin = models.ForeignKey(Plugin)
    name = models.CharField(max_length = 64)
    value = models.TextField(default = '', blank = True)

    def __unicode__(self):
        return "%s: %s" % (self.name, self.value)

# TODO: Refactor this to more suitable name (without using verbose_name)
class Document(models.Model):
    """
        A model that represents Document for maintainig Tag relations.
    """
    name = models.CharField(max_length = 128)
    doccode = models.CharField(max_length = 63, choices = DOCRULE_CHOICES)
    tags = TaggableManager()

    class Meta:
        verbose_name = "Document > Tags mapping"
        verbose_name_plural = "Document > Tags mappings"

    def get_tag_list(self):
        return map(lambda x: x.name, self.tags.all())

    def __unicode__(self):
        return unicode(self.name)