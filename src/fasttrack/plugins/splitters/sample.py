import os

from fileshare.utils import SplitterProvider

class Sample(SplitterProvider):
    name = 'Sample'

    @staticmethod
    def perform(document):
        return "%s/%s/%s" % (document[0:3], document[3:7], os.path.splitext(document)[0])

