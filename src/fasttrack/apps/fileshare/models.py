import os
import hashlib
import pkgutil
import pickle

from django.db import models
from django.conf import settings

from fileshare.utils import ValidatorProvider, StorageProvider, SecurityProvider, \
                            DocCodeProvider


class RuleManager(models.Manager):

    def match(self, document):
        for rule in self.filter(active=True):
            validator = rule.pvalidator
            if validator and validator.validate(document):
                return rule
        return None


class Rule(models.Model):
    doccode = models.CharField(max_length=255, unique=True)
    storage = models.CharField(max_length=255)
    validators = models.TextField(blank=True)
    securities = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    objects = RuleManager()

    def get_doccode(self):
        try:
            return pickle.loads(self.doccode.encode("ascii"))
        except:
            return None

    def get_securities(self):
        try:
            return pickle.loads(self.securities.encode("ascii"))
        except:
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
            return None



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
    Get available storage engines plugins
    """
    for module in list(pkgutil.iter_modules(["%s/storages" % settings.PLUGIN_DIR])):
        __import__("storages.%s" % module[1], fromlist=[""])
    return StorageProvider.plugins



def available_securities():
    """
    Get available splitter plugins
    """
    for module in list(pkgutil.iter_modules(["%s/securities" % settings.PLUGIN_DIR])):
        __import__("securities.%s" % module[1], fromlist=[""])
    return SecurityProvider.plugins

