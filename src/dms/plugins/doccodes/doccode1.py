import re

from fileshare.utils import DocCodeProvider


class DocCode(DocCodeProvider):
    name = 'Adlibre Invoices'
    description = 'ADL-[0-9]{4}'
    splits = 2 # TODO: surely this can be dynamicly determined

    @staticmethod
    def validate(document):
        if re.match("^ADL-[0-9]{4}$", document):
            return True
        return False

    @staticmethod
    def split(document):
        d = [ document[0:3], document[4:8], ]
        return d
