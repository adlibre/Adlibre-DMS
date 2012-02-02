from django.db import models

"""
New models
"""
from plugins.fields import PluginField, ManyPluginField
from plugins.models import Plugin
from taggit.managers import TaggableManager

from dms_plugins import pluginpoints
from doc_codes import DoccodeManagerInstance
from doc_codes.models import DoccodeModel

DOCCODE_CHOICES = map(lambda doccode: (str(doccode.doccode_id), doccode.title), DoccodeManagerInstance.get_doccodes())

class DoccodePluginMapping(models.Model):
    doccode = models.CharField(choices = DOCCODE_CHOICES, max_length = 64)
    #if changing *_plugins names please change dms_plugins.pluginpoints correspondingly
    before_storage_plugins = ManyPluginField(   pluginpoints.BeforeStoragePluginPoint, 
                                                related_name = 'settings_before_storage',
                                                blank = True,
                                                verbose_name = "Pre-Storage Workflow")
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
            doccode_name = DoccodeModel.objects.get(doccode_id=self.doccode).title
        except (KeyError, AttributeError):
            pass
        return unicode(doccode_name)
    name = property(get_name)

    def get_doccode(self):
        doccodes = DoccodeManagerInstance.get_doccodes()
        try:
            doccode = doccodes[int(self.doccode)]
        except:
            doccode = doccodes.filter(doccode_id=self.doccode)[0]
        return doccode

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

class PluginOption(models.Model):
    pluginmapping = models.ForeignKey(DoccodePluginMapping)
    plugin = models.ForeignKey(Plugin)
    name = models.CharField(max_length = 64)
    value = models.TextField(default = '', blank = True)

    def __unicode__(self):
        return "%s: %s" % (self.name, self.value)

class Document(models.Model):
    """
        A model that represents Document for maintainig database relations.
    """
    name = models.CharField(max_length = 128)
    doccode = models.CharField(max_length = 63, choices = DOCCODE_CHOICES)
    tags = TaggableManager()

    def get_tag_list(self):
        return map(lambda x: x.name, self.tags.all())

    def __unicode__(self):
        return unicode(self.name)