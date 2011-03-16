import re

from fileshare.utils import DocCodeProvider


class DocCode(DocCodeProvider):
    name = 'DocCode-2'
    description = '[a-z]{5}[0-9]{3}'

    @staticmethod
    def validate(document):
        if re.match("^[a-z]{5}[0-9]{3}$", document):
            return True
        return False

    @staticmethod
    def split(document):
        d = [ document[0:5], document[5:8], ]
        return d