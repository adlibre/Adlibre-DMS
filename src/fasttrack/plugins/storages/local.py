import os

from django.conf import settings

from fileshare.utils import StorageProvider
from converter import FileConverter


class Local(StorageProvider):
    name = "Local"

    @staticmethod
    def store(f, splitter, root = settings.MEDIA_ROOT):
        filename = f.name
        directory = splitter.perform(filename)
        if root:
            directory = "%s/%s" % (root, directory)
        if not os.path.exists(directory):
            os.makedirs(directory)
        destination = open('%s/%s' % (directory, f.name), 'wb+')
        for chunk in f.chunks():
            destination.write(chunk)
        destination.close()


    @staticmethod
    def get(document, splitter, root = settings.MEDIA_ROOT):
        directory = splitter.perform(document)
        if root:
            directory = "%s/%s" % (root, directory)

        filename = os.listdir(directory)[0]
        fullpath = '%s/%s' % (directory, filename)
        content = FileConverter(fullpath)
        return content.to_pdf()

