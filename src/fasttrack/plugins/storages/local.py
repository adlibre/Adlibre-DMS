import os

from django.conf import settings

from fileshare.utils import StorageProvider


class Local(StorageProvider):
    name = "Local Storage"

    @staticmethod
    def store(f, root = settings.DOCUMENT_ROOT):
        filename = f.name
        directory = "%s/%s/%s" % (filename[0:3], filename[3:7], os.path.splitext(filename)[0])
        if root:
            directory = "%s/%s" % (root, directory)
        if not os.path.exists(directory):
            os.makedirs(directory)
        destination = open('%s/%s' % (directory, f.name), 'wb+')
        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()


    @staticmethod
    def get(document, root = settings.DOCUMENT_ROOT):

        directory = "%s/%s/%s" % (document[0:3], document[3:7], os.path.splitext(document)[0])
        if root:
            directory = "%s/%s" % (root, directory)
        try:
            filename = os.listdir(directory)[0]
        except OSError:
            return None
        fullpath = '%s/%s' % (directory, filename)
        return fullpath

