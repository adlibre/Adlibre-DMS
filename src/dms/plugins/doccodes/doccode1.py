import re

from fileshare.utils import DocCodeProvider


class DocCode(DocCodeProvider):
    name = 'DocCode-1'
    description = '[A-Z]{3}[0-9]{8}'

    @staticmethod
    def validate(document):
        if re.match("^[A-Z]{3}[0-9]{8}$", document):
            return True
        return False

