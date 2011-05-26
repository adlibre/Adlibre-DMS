"""
Module: DMS Django Models
Project: Adlibre DMS
Copyright: Adlibre Pty Ltd 2011
License: See LICENSE for license information
"""

import pkgutil
import pickle

from django.db import models
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from base.utils import ValidatorProvider, StorageProvider, SecurityProvider, DocCodeProvider

from plugins.models import Plugin


class RuleManager(models.Manager):
    """
    Manager for Rule model
    """

    def match(self, document):
        """
        Get rule according to document naming, return None if not found
        """

        for rule in self.filter(active=True):
            doccode = rule.get_doccode()
            if doccode and doccode.validate(document):
                return rule
        #return None

        raise ObjectDoesNotExist('Rule matching query does not exist')


class Rule(models.Model):
    """
    Specify rule for a document naming. Each rule has its own plugins.
    The plugins is saved in pickle object format in database.
    """

    doccode = models.TextField(max_length=255, unique=True)
    storage = models.TextField(max_length=255)
    validators = models.TextField(blank=True)
    securities = models.TextField(blank=True)
    #transfers = models.ManyToManyField(PluginRule, blank=True, null=True) #FIXME: This needs to link to PluginRule(Plugin) model
    active = models.BooleanField(default=True)

    objects = RuleManager()

    def __unicode__(self):
        return self.get_doccode().name

    def get_doccode(self):
        try:
            return pickle.loads(self.doccode.encode("ascii"))
        except:
            return None


    def get_securities(self):
        try:
            return pickle.loads(self.securities.encode("ascii"))
        except:
            return []


    def get_security(self, name):
        """
        Get security plugin by name, return None if not found
        """
        try:
            securities = pickle.loads(self.securities.encode("ascii"))
            for security in securities:
                if security.name == name:
                    return security
        except:
            pass
        return None


    def get_storage(self):
        try:
            return pickle.loads(self.storage.encode("ascii"))
        except:
            return None


    def get_validators(self):
        try:
            return pickle.loads(self.validators.encode("ascii"))
        except:
            return []


#    def get_transfers(self):
#        t = []
#        for transfer in self.transfers.all():
#            t.append(transfer.get_plugin())
#        return t


def available_doccodes():
    """
    Get available document code plugins
    """

    for module in list(pkgutil.iter_modules(["%s/doccodes" % settings.PLUGIN_DIR])):
        __import__("doccodes.%s" % module[1], fromlist=[""])
    return DocCodeProvider.plugins


def available_validators():
    """
    Get available document validator plugins
    """

    for module in list(pkgutil.iter_modules(["%s/validators" % settings.PLUGIN_DIR])):
        __import__("validators.%s" % module[1], fromlist=[""])
    return ValidatorProvider.plugins


def available_storages():
    """
    Get available storage engine plugins
    """

    for module in list(pkgutil.iter_modules(["%s/storages" % settings.PLUGIN_DIR])):
        __import__("storages.%s" % module[1], fromlist=[""])
    return StorageProvider.plugins


def available_securities():
    """
    Get available security plugins
    """

    for module in list(pkgutil.iter_modules(["%s/securities" % settings.PLUGIN_DIR])):
        __import__("securities.%s" % module[1], fromlist=[""])
    return SecurityProvider.plugins


class PluginRule(models.Model):

    rule = models.ForeignKey(Rule)
    plugin = models.ForeignKey(Plugin)
    active = models.BooleanField(default=True)
    index = models.IntegerField(default=0)

    class Meta:
        ordering = ['-index',]
        #order_with_respect_to = 'rule'

    def __unicode__(self):
        return "%s - %s" % (self.rule, self.plugin)

    # active = inherit , actually we should be able to turn this on and off
    # point = inherit
    # FIXME: How to make only some fields editable, the rest should inherit from the plugin!

"""
New models
"""
from plugins.fields import ManyPluginField

from dms_plugins import pluginpoints
from doc_codes import DoccodeManagerInstance
DOCCODE_CHOICES = map(lambda x: (str(x[0]), x[1].get_title()), DoccodeManagerInstance.get_doccodes().items())

class DoccodePluginMapping(models.Model):
    doccode = models.CharField(choices = DOCCODE_CHOICES, max_length = 64)
    #if changing *_plugins names please change dms_plugins.pluginpoints correspondingly
    before_storage_plugins = ManyPluginField(   pluginpoints.BeforeStoragePluginPoint, 
                                                related_name = 'settings_before_storage',)
    before_retrieval_plugins = ManyPluginField( pluginpoints.BeforeRetrievalPluginPoint, 
                                                related_name = 'settings_before_retrieval',
                                                blank = True) # blank is only for debug


    def __unicode__(self):
        doccode_name = "ERROR"
        try:
            doccode_name = DoccodeManagerInstance.get_doccodes()[int(self.doccode)].title
        except (KeyError, AttributeError):
            pass
        return unicode(doccode_name)