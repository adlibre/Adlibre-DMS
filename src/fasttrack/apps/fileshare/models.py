import os
import hashlib
import pkgutil

from django.db import models

from fileshare.utils import ValidatorProvider, SplitterProvider, StorageProvider

class FileShare(models.Model):
    hashcode = models.CharField(max_length=255)
    document = models.CharField(max_length=255)
    splitter = models.CharField(max_length=255)
    storage = models.CharField(max_length=255)


    def __unicode__(self):
        return "%s" % os.path.basename(self.sharefile.file.name)

    def save(self, *args, **kwargs):
        self.hashcode = hashlib.md5(self.document).hexdigest()
        super(FileShare, self).save(*args, **kwargs)

    @models.permalink
    def get_absolute_url(self):
        return ('get_file', [self.hashcode, self.document])



class FileShareSetting(models.Model):
    validator = models.CharField(max_length=255)
    storage = models.CharField(max_length=255)
    splitter = models.CharField(max_length=255)


def get_validator():
    """
    Get active validator method
    """

    try:
        filesetting = FileShareSetting.objects.get(id=1)
        validator = ValidatorProvider.plugins[filesetting.validator]
        return validator
    except Exception, e:
        print e
        return None



def get_storage():
    """
    Get active storage engine
    """

    try:
        filesetting = FileShareSetting.objects.get(id=1)
        storage = StorageProvider.plugins[filesetting.storage]
        return storage
    except Exception, e:
        print e
        return None



def get_splitter():
    """
    Get active splitter method
    """

    try:
        filesetting = FileShareSetting.objects.get(id=1)
        splitter = SplitterProvider.plugins[filesetting.splitter]
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

