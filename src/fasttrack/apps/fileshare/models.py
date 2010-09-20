import os
import hashlib
import pkgutil

from django.db import models

from fileshare.utils import ValidatorProvider, SplitterProvider, StorageProvider, HashProvider


class RuleManager(models.Manager):

    def match(self, document):
        for rule in self.filter(active=True):
            validator = rule.get_validator()
            if validator and validator.validate(document):
                return rule
        return None


class Rule(models.Model):
    validator = models.CharField(max_length=255, unique=True)
    storage = models.CharField(max_length=255)
    splitter = models.CharField(max_length=255)
    hashcode = models.CharField(max_length=255)
    is_hash_active = models.BooleanField(default=True)
    active = models.BooleanField(default=True)

    objects = RuleManager()

    def get_validator(self):
        """
        Get active validator method
        """

        try:
            validator = ValidatorProvider.plugins[self.validator]
            return validator
        except Exception, e:
            return None

    def get_storage(self):
        """
        Get active storage engine
        """

        try:
            storage = StorageProvider.plugins[self.storage]
            return storage
        except Exception, e:
            print e
            return None

    def get_splitter(self):
        """
        Get active splitter method
        """

        try:
            splitter = SplitterProvider.plugins[self.splitter]
            return splitter
        except Exception, e:
            print e
            return None


def available_validators():
    """
    Get available document validator plugins
    """
    for module in list(pkgutil.iter_modules(["plugins/validators"])):
        __import__("plugins.validators.%s" % module[1], fromlist=[""])
    return ValidatorProvider.plugins


def available_storages():
    """
    Get available storage engines plugins
    """
    for module in list(pkgutil.iter_modules(["plugins/storages"])):
        __import__("plugins.storages.%s" % module[1], fromlist=[""])
    return StorageProvider.plugins


def available_splitters():
    """
    Get available splitter plugins
    """
    for module in list(pkgutil.iter_modules(["plugins/splitters"])):
        __import__("plugins.splitters.%s" % module[1], fromlist=[""])
    return SplitterProvider.plugins


def available_hash():
    """
    Get available splitter plugins
    """
    for module in list(pkgutil.iter_modules(["plugins/hash"])):
        __import__("plugins.hash.%s" % module[1], fromlist=[""])
    return HashProvider.plugins

