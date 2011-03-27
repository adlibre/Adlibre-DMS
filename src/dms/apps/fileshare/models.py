import pkgutil
import pickle

from django.db import models
from django.conf import settings

from fileshare.utils import ValidatorProvider, StorageProvider, SecurityProvider, \
    DocCodeProvider


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
        return None


class Rule(models.Model):
    """
    Specify rule for a document naming. Each rule has its own plugins.
    The plugins is saved in pickle object format in database.
    """

    doccode = models.TextField(max_length=255, unique=True)
    storage = models.TextField(max_length=255)
    validators = models.TextField(blank=True)
    securities = models.TextField(blank=True)
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

